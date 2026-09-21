"""
rerun_sweep.py

Generalizes rerun_insideoutside_sweep.py: leave-one-out sweep with diverse-
pair selection, for any ConceptARC group and any anchor relation, not just
InsideOutside/contains. Same methodology throughout (D9/D11): each held-out
task is checked against 15-to-many pairs drawn from the other usable tasks,
one candidate pair per task-pair via select_most_diverse_pair, checked
against every grid of the held-out task.

Usable tasks are discovered automatically (tasks with >=1 grid carrying the
target relation - see python/coverage_matrix.py for the full matrix this was
built from). --n-tasks caps how many usable tasks are included, since the
pair count grows as n*C(n-1,2) and a full 10-task group can be ~3.4x an
InsideOutside-sized (7-task) sweep. D12 capped SameDifferent at 5 of 10 tasks
for the same reason; this defaults to 5 as well.

Writes one JSON line per completed pair to --out as it goes, and skips pairs
already present on a second run - same resumability as
rerun_insideoutside_sweep.py, for the same reason (D11's silent-data-loss
lesson).

Usage:
    python python/rerun_sweep.py --group Copy --relation sameColor
    python python/rerun_sweep.py --group Copy --relation sameColor --n-tasks 10
    python python/rerun_sweep.py --group Copy --relation sameColor --summarize-only
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


def group_of(fp: str) -> str:
    parent = os.path.basename(os.path.dirname(fp))
    return parent if parent and parent not in (".", "corpus") else \
        os.path.splitext(os.path.basename(fp))[0]


def grids_of(task_json):
    for split in ("train", "test"):
        for i, pair in enumerate(task_json.get(split, [])):
            for gname in ("input", "output"):
                if gname in pair:
                    yield f"{split}{i}_{gname}", pair[gname]


def discover_usable_tasks(group, relation, enc, n_cap=None):
    """Finds every task in `group` with >=1 grid carrying `relation`,
    matching coverage_matrix.py's definition of "usable" exactly, so the
    same threshold this project already reports against (5 for
    SameDifferent, 7 for InsideOutside) is reproduced here rather than
    redefined. Deterministic order (sorted by task id) so --n-tasks picks
    the same subset on every run."""
    files = [fp for fp in sorted(glob.glob(CONCEPTARC_GLOB))
             if group_of(fp).lower() == group.lower()]
    if not files:
        raise SystemExit(f"no files found for group {group!r}")

    usable, pools, grids, task_json = [], {}, {}, {}
    for fp in files:
        tid = os.path.splitext(os.path.basename(fp))[0]
        qid = f"conceptarc__{tid}"
        tj = json.load(open(fp))
        task_json[tid] = tj
        pairs = dict(grids_of(tj))
        grids[tid] = pairs
        cands = [c for c in enum_mod.extract_from_task_json(tj, qid, enc)
                 if c.relation == relation]
        pools[tid] = cands
        if cands:
            usable.append(tid)

    usable.sort()
    if n_cap:
        usable = usable[:n_cap]
    return usable, pools, grids


def select_first_pair(pool_a, pool_b):
    """The D9 baseline: literally the first candidate extracted from each
    task's pool, no scoring, no selection logic at all - the naive strategy
    D11 showed diverse-pair selection beats. Returns (c1, c2, None); the
    third slot is coincidental_score in the diverse path, which has no
    meaning here and is kept None rather than a misleading 0.

    Deterministic: pool order comes from extract_from_task_json, which
    walks train/test splits and grids in a fixed order, so pool[0] is the
    same candidate on every run given the same data."""
    if not pool_a or not pool_b:
        return None, None, None
    return pool_a[0], pool_b[0], None


def already_done(out_path):
    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    done.add((rec["held_out"], rec["task_a"], rec["task_b"]))
    return done


def run_pair(pools, grids, enc, relation, held_out, task_a, task_b, select_fn):
    c1, c2, score = select_fn(pools[task_a], pools[task_b])
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


def summarize(out_path, n_expected=None):
    recs = [json.loads(l) for l in open(out_path) if l.strip()]
    n_in_m = sum(r["n_input_matched"] for r in recs)
    n_in_t = sum(r["n_input_total"] for r in recs)
    n_out_m = sum(r["n_output_matched"] for r in recs)
    n_out_t = sum(r["n_output_total"] for r in recs)
    n_deg = sum(1 for r in recs if r["is_degenerate"])

    denom = f"/{n_expected}" if n_expected else ""
    print(f"\n{'=' * 60}\nSWEEP SUMMARY  ({len(recs)}{denom} pairs recorded)\n{'=' * 60}")
    print(f"input  : {n_in_m}/{n_in_t}  ({100 * n_in_m / n_in_t if n_in_t else 0:.1f}%)")
    print(f"output : {n_out_m}/{n_out_t}  ({100 * n_out_m / n_out_t if n_out_t else 0:.1f}%)")
    tot_m, tot_t = n_in_m + n_out_m, n_in_t + n_out_t
    print(f"overall: {tot_m}/{tot_t}  ({100 * tot_m / tot_t if tot_t else 0:.1f}%)")
    print(f"degenerate blends: {n_deg}/{len(recs)}")


def compare(diverse_path, first_path):
    def totals(path):
        recs = [json.loads(l) for l in open(path) if l.strip()]
        im = sum(r["n_input_matched"] for r in recs)
        it = sum(r["n_input_total"] for r in recs)
        om = sum(r["n_output_matched"] for r in recs)
        ot = sum(r["n_output_total"] for r in recs)
        return len(recs), im, it, om, ot

    n_f, im_f, it_f, om_f, ot_f = totals(first_path)
    n_d, im_d, it_d, om_d, ot_d = totals(diverse_path)
    if n_f != n_d:
        print(f"WARNING: pair counts differ (first={n_f}, diverse={n_d}) - "
              f"comparison is not apples-to-apples unless both finished "
              f"with the same --n-tasks")

    def pct(m, t):
        return 100 * m / t if t else 0

    print(f"\n{'=' * 64}\nD9/D11-STYLE BEFORE/AFTER  (first-candidate vs diverse-pair)\n{'=' * 64}")
    print(f"{'':<10}{'first-candidate':<22}{'diverse-pair':<22}")
    print(f"{'input':<10}{f'{im_f}/{it_f} ({pct(im_f,it_f):.1f}%)':<22}"
          f"{f'{im_d}/{it_d} ({pct(im_d,it_d):.1f}%)':<22}")
    print(f"{'output':<10}{f'{om_f}/{ot_f} ({pct(om_f,ot_f):.1f}%)':<22}"
          f"{f'{om_d}/{ot_d} ({pct(om_d,ot_d):.1f}%)':<22}")
    tot_f_m, tot_f_t = im_f + om_f, it_f + ot_f
    tot_d_m, tot_d_t = im_d + om_d, it_d + ot_d
    print(f"{'overall':<10}"
          f"{f'{tot_f_m}/{tot_f_t} ({pct(tot_f_m,tot_f_t):.1f}%)':<22}"
          f"{f'{tot_d_m}/{tot_d_t} ({pct(tot_d_m,tot_d_t):.1f}%)':<22}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True)
    ap.add_argument("--relation", required=True)
    ap.add_argument("--n-tasks", type=int, default=5,
                    help="cap usable tasks included (pairs grow as "
                         "n*C(n-1,2); default 5, matching D12's SameDifferent "
                         "scope; use a larger value or 0 for no cap)")
    ap.add_argument("--strategy", choices=["diverse", "first"], default="diverse",
                    help="diverse (default): D11's select_most_diverse_pair. "
                         "first: D9's naive baseline, first candidate from "
                         "each pool. Run both with the same --group "
                         "--relation --n-tasks for a fair D11-style "
                         "before/after comparison - the task set must match "
                         "exactly, which requires the same --n-tasks on both.")
    ap.add_argument("--out", default=None)
    ap.add_argument("--held-out", default=None,
                    help="run only this held-out task (for chunking by hand)")
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--compare", action="store_true",
                    help="print a D11-style before/after table from the "
                         "diverse and first-candidate output files for this "
                         "--group/--relation (both must already exist)")
    args = ap.parse_args()

    if args.compare:
        diverse_path = args.out or f"docs/{args.group.lower()}_{args.relation}_sweep.jsonl"
        first_path = f"docs/{args.group.lower()}_{args.relation}_first_sweep.jsonl"
        compare(diverse_path, first_path)
        return

    # Default filename is UNCHANGED for strategy="diverse" (so an
    # already-running diverse sweep and this file's own --summarize-only
    # keep working against the same path with no migration needed); "first"
    # gets a distinct suffix so the two strategies' results can never
    # silently overwrite or mix in one file.
    suffix = "_first" if args.strategy == "first" else ""
    out_path = args.out or f"docs/{args.group.lower()}_{args.relation}{suffix}_sweep.jsonl"

    if args.summarize_only:
        summarize(out_path)
        return

    enc = GridEncoder()
    n_cap = None if args.n_tasks == 0 else args.n_tasks
    tasks, pools, grids = discover_usable_tasks(args.group, args.relation, enc, n_cap)
    if len(tasks) < 3:
        raise SystemExit(f"only {len(tasks)} usable tasks for "
                         f"{args.group}/{args.relation}, need >=3 for a "
                         f"leave-one-out sweep")

    n_pairs_per_held_out = len(list(combinations(range(len(tasks) - 1), 2)))
    n_total = len(tasks) * n_pairs_per_held_out
    print(f"{args.group}/{args.relation}, strategy={args.strategy}: "
          f"{len(tasks)} usable tasks ({', '.join(tasks)})")
    print(f"{n_total} total pairs ({n_pairs_per_held_out} per held-out task)\n")

    select_fn = select_first_pair if args.strategy == "first" else \
        enum_mod.select_most_diverse_pair

    done = already_done(out_path)
    if done:
        print(f"resuming: {len(done)} pairs already recorded in {out_path}")

    held_out_tasks = [args.held_out] if args.held_out else tasks
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    n_run = 0
    with open(out_path, "a") as f:
        for held_out in held_out_tasks:
            others = [t for t in tasks if t != held_out]
            for task_a, task_b in combinations(others, 2):
                key = (held_out, task_a, task_b)
                if key in done:
                    continue
                rec = run_pair(pools, grids, enc, args.relation,
                              held_out, task_a, task_b, select_fn)
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
    summarize(out_path, n_expected=n_total)


if __name__ == "__main__":
    main()
