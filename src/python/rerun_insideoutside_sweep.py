"""
rerun_insideoutside_sweep.py

Re-runs the D9/D11 InsideOutside leave-one-out sweep against the current
(D13-fixed) encoder, using D11's diverse-pair selection throughout (not the
first-candidate baseline - D13 already showed the fix is purely additive, so
the baseline-vs-diverse comparison itself doesn't need re-running, only the
headline diverse-pair number does).

Methodology (unchanged from D9/D11): 7 held-out tasks (the ones with
`contains` structure), each held out in turn against 15 task-pairs drawn from
the other 6, one candidate pair per task-pair via select_most_diverse_pair,
checked against every grid of the held-out task. 105 pairs, ~1200 grid
checks.

Writes one JSON line per completed pair to --out as it goes (not batched),
and skips pairs already present on a second run - if this gets interrupted,
re-running the same command picks up where it left off rather than losing
progress (see docs/decisions.md D11 for why this matters).

Usage:
    python python/rerun_insideoutside_sweep.py
    python python/rerun_insideoutside_sweep.py --held-out InsideOutside5
    python python/rerun_insideoutside_sweep.py --summarize-only
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder                    # noqa: E402
import enumerate as enum_mod                          # noqa: E402
import blend_pipeline as bp                              # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"
TASKS = ["InsideOutside1", "InsideOutside4", "InsideOutside5",
         "InsideOutside6", "InsideOutside7", "InsideOutside8",
         "InsideOutside10"]
DEFAULT_OUT = "docs/insideoutside_sweep_postD13.jsonl"


def load_group():
    files = {}
    for fp in sorted(glob.glob(CONCEPTARC_GLOB)):
        tid = os.path.splitext(os.path.basename(fp))[0]
        if tid in TASKS:
            files[tid] = fp
    missing = [t for t in TASKS if t not in files]
    if missing:
        raise SystemExit(f"missing task files for {missing} under {CONCEPTARC_GLOB}")

    enc = GridEncoder()
    pools, grids = {}, {}
    for tid, fp in files.items():
        qid = f"conceptarc__{tid}"
        tj = json.load(open(fp))
        pairs = {}
        for split in ("train", "test"):
            for i, pair in enumerate(tj.get(split, [])):
                for gname in ("input", "output"):
                    if gname in pair:
                        pairs[f"{split}{i}_{gname}"] = pair[gname]
        grids[tid] = pairs
        cands = [c for c in enum_mod.extract_from_task_json(tj, qid, enc)
                 if c.relation == "contains"]
        pools[tid] = cands
    return pools, grids


def already_done(out_path):
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done.add((rec["held_out"], rec["task_a"], rec["task_b"]))
    return done


def run_pair(pools, grids, enc, held_out, task_a, task_b):
    c1, c2, score = enum_mod.select_most_diverse_pair(
        pools[task_a], pools[task_b])
    if c1 is None:
        return None
    blend_str, is_degenerate = bp.build_blend(c1, c2)
    if blend_str is None:
        return None
    pattern = bp._extract_pattern_atoms(blend_str)

    qid = f"conceptarc__{held_out}"
    checks = []
    for label, grid in grids[held_out].items():
        atoms, _ = enc.encode(qid, label, grid)
        checks.append((label, atoms))
    res = bp.check_coherence_per_grid(pattern, checks)

    n_in_total = sum(1 for lbl in res if "input" in lbl)
    n_out_total = sum(1 for lbl in res if "output" in lbl)
    n_in_matched = sum(1 for lbl, v in res.items() if v and "input" in lbl)
    n_out_matched = sum(1 for lbl, v in res.items() if v and "output" in lbl)

    return {
        "held_out": held_out, "task_a": task_a, "task_b": task_b,
        "coincidental_score": score, "is_degenerate": is_degenerate,
        "n_input_total": n_in_total, "n_input_matched": n_in_matched,
        "n_output_total": n_out_total, "n_output_matched": n_out_matched,
    }


def summarize(out_path):
    recs = [json.loads(l) for l in open(out_path) if l.strip()]
    n_in_m = sum(r["n_input_matched"] for r in recs)
    n_in_t = sum(r["n_input_total"] for r in recs)
    n_out_m = sum(r["n_output_matched"] for r in recs)
    n_out_t = sum(r["n_output_total"] for r in recs)
    n_deg = sum(1 for r in recs if r["is_degenerate"])

    print(f"\n{'=' * 60}\nSWEEP SUMMARY  ({len(recs)}/105 pairs recorded)\n{'=' * 60}")
    print(f"input  : {n_in_m}/{n_in_t}  ({100 * n_in_m / n_in_t if n_in_t else 0:.1f}%)")
    print(f"output : {n_out_m}/{n_out_t}  ({100 * n_out_m / n_out_t if n_out_t else 0:.1f}%)")
    tot_m, tot_t = n_in_m + n_out_m, n_in_t + n_out_t
    print(f"overall: {tot_m}/{tot_t}  ({100 * tot_m / tot_t if tot_t else 0:.1f}%)")
    print(f"degenerate blends: {n_deg}/{len(recs)}")
    print(f"\ncompare against D11 pre-fix (diverse-pair): "
          f"overall 54% (654/1200), input 81% (486/600), output 28% (168/600)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--held-out", default=None,
                    help="run only this held-out task (for chunking by hand)")
    ap.add_argument("--summarize-only", action="store_true",
                    help="skip running; just print the summary from --out")
    args = ap.parse_args()

    if args.summarize_only:
        summarize(args.out)
        return

    pools, grids = load_group()
    enc = GridEncoder()
    done = already_done(args.out)
    if done:
        print(f"resuming: {len(done)} pairs already recorded in {args.out}")

    held_out_tasks = [args.held_out] if args.held_out else TASKS
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    n_run = 0
    with open(args.out, "a") as f:
        for held_out in held_out_tasks:
            others = [t for t in TASKS if t != held_out]
            for task_a, task_b in combinations(others, 2):
                key = (held_out, task_a, task_b)
                if key in done:
                    continue
                rec = run_pair(pools, grids, enc, held_out, task_a, task_b)
                if rec is None:
                    continue
                f.write(json.dumps(rec) + "\n")
                f.flush()
                n_run += 1
                im = rec["n_input_matched"]; it = rec["n_input_total"]
                om = rec["n_output_matched"]; ot = rec["n_output_total"]
                print(f"  held_out={held_out:<16} {task_a} x {task_b}  "
                      f"score={rec['coincidental_score']}  "
                      f"in {im}/{it}  out {om}/{ot}")

    print(f"\n{n_run} new pairs recorded this run")
    summarize(args.out)


if __name__ == "__main__":
    main()
