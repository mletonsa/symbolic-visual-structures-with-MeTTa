"""
survey_novelty.py

Two things, over real ConceptARC data:

1. PARITY CHECK: for every pair, assess_novelty's parent_echo verdict
   must agree with blend.metta's isDegenerate flag (returned by
   build_blend). novelty.py was designed to match isDegenerate exactly
   but never verified against a real MeTTa run - this is that
   verification. Any disagreement is printed in full and the script
   exits non-zero, since it means one of the two implementations has a
   bug worth finding before either is trusted.

2. VERDICT DISTRIBUTION: tallies parent_echo / trivial / novel across
   every valid same-relation cross-task pair for one group, and further
   splits "novel" by whether it carries a scalar property (n_fixed > 0)
   or is novel purely through shared symmetry (n_fixed == 0). This is
   the real-data counterpart to D14's convergence-to-primitives finding:
   how often does the pipeline's own selection heuristic land on a pair
   that is novel only via symmetry, versus one with real scalar content?

No coherence checking here (no new-space/add-atom), so this uses only
the persistent, non-mutating blend runtime - fast, per D9.

Usage:
    python python/survey_novelty.py
    python python/survey_novelty.py --group SameDifferent --relation sameShape
    python python/survey_novelty.py --limit 200        # cap pair count
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder                    # noqa: E402
import enumerate as enum_mod                        # noqa: E402
import blend_pipeline as bp                          # noqa: E402
from novelty import assess_novelty                   # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"


def group_of(fp: str) -> str:
    parent = os.path.basename(os.path.dirname(fp))
    return parent if parent and parent not in (".", "corpus") else \
        os.path.splitext(os.path.basename(fp))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="InsideOutside")
    ap.add_argument("--relation", default="contains")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of pairs processed")
    args = ap.parse_args()

    files = [fp for fp in sorted(glob.glob(CONCEPTARC_GLOB))
             if group_of(fp).lower() == args.group.lower()]
    if not files:
        raise SystemExit(f"no files found for group {args.group!r} under "
                         f"{CONCEPTARC_GLOB} (cwd={os.getcwd()})")

    enc = GridEncoder()
    pools = {}
    for fp in files:
        tid = os.path.splitext(os.path.basename(fp))[0]
        qid = f"conceptarc__{tid}"
        tj = json.load(open(fp))
        cands = [c for c in enum_mod.extract_from_task_json(tj, qid, enc)
                 if c.relation == args.relation]
        if cands:
            pools[tid] = cands

    print(f"group {args.group!r}, relation {args.relation!r}: "
          f"{len(pools)} tasks with candidates "
          f"({', '.join(sorted(pools))})")
    if len(pools) < 2:
        raise SystemExit("need at least 2 tasks with candidates to form "
                         "cross-task pairs")

    task_ids = sorted(pools)
    all_pairs = []
    for i, ta in enumerate(task_ids):
        for tb in task_ids[i + 1:]:
            all_pairs.extend(enum_mod.select_pairs(pools[ta], pools[tb]))
    if args.limit:
        all_pairs = all_pairs[:args.limit]
    print(f"{len(all_pairs)} valid cross-task pairs to process\n")

    tally = {"parent_echo": 0, "trivial": 0,
             "novel_symmetry_only": 0, "novel_with_scalar": 0}
    mismatches = []

    for i, (c1, c2) in enumerate(all_pairs):
        blend_str, is_degenerate = bp.build_blend(c1, c2)
        if blend_str is None:
            continue
        r = assess_novelty(c1, c2)

        agrees = (r.verdict == "parent_echo") == bool(is_degenerate)
        if not agrees:
            mismatches.append((i, c1, c2, r, is_degenerate, blend_str))

        if r.verdict == "parent_echo":
            tally["parent_echo"] += 1
        elif r.verdict == "trivial":
            tally["trivial"] += 1
        elif r.n_fixed == 0:
            tally["novel_symmetry_only"] += 1
        else:
            tally["novel_with_scalar"] += 1

        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1}/{len(all_pairs)} processed")

    n = sum(tally.values())
    print(f"\n{'=' * 60}\nVERDICT DISTRIBUTION  (n={n})\n{'=' * 60}")
    for k, v in tally.items():
        pct = 100 * v / n if n else 0
        print(f"  {k:<22} {v:>5}  ({pct:5.1f}%)")

    novel_total = tally["novel_symmetry_only"] + tally["novel_with_scalar"]
    if novel_total:
        pct_sym_only = 100 * tally["novel_symmetry_only"] / novel_total
        print(f"\n  of {novel_total} novel blends, "
              f"{pct_sym_only:.1f}% are novel through symmetry alone "
              f"(every scalar slot generalized)")

    print(f"\n{'=' * 60}\nPARITY CHECK: parent_echo vs isDegenerate\n{'=' * 60}")
    if mismatches:
        print(f"  MISMATCH on {len(mismatches)}/{n} pairs:\n")
        for i, c1, c2, r, is_degenerate, blend_str in mismatches[:5]:
            print(f"  pair {i}: assess_novelty={r.verdict!r} "
                  f"isDegenerate={is_degenerate}")
            print(f"    A: {c1.to_metta()}")
            print(f"    B: {c2.to_metta()}")
            print(f"    blend: {blend_str}\n")
        raise SystemExit(1)
    else:
        print(f"  {n}/{n} agree. parent_echo matches isDegenerate on "
              f"every pair checked.")


if __name__ == "__main__":
    main()
