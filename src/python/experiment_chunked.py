"""
experiment_chunked.py

Runs experiment_group_sweep's per-pair logic for ONE held-out task at a
time, appending JSON-lines results to a file. Exists purely because a
full 10-task sweep (~105 checks * ~2-4s each) exceeds a single tool
call's wall-clock budget in this environment - not a permanent part of
the pipeline, just a chunking wrapper for running large sweeps across
multiple invocations. See docs/decisions.md D11/D12 for the actual
experiment results this was used to produce.

Usage:
  python3 python/experiment_chunked.py --group InsideOutside \\
      --relation contains --held-out InsideOutside5 --strategy diverse \\
      --out /tmp/results.jsonl
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from encoder import GridEncoder  # noqa: E402
from enumerate import extract_from_task_json, select_most_diverse_pair  # noqa: E402
from blend_pipeline import blend_and_check, _extract_pattern_atoms  # noqa: E402
from scoring import mdl_gain  # noqa: E402
from experiment_group_sweep import load_task, grids_atoms, CORPUS_ROOT  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True)
    ap.add_argument("--relation", required=True)
    ap.add_argument("--held-out", required=True)
    ap.add_argument("--n-tasks", type=int, default=10)
    ap.add_argument("--strategy", choices=["first", "diverse"], default="first")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    enc = GridEncoder()
    task_ids = [f"{args.group}{i}" for i in range(1, args.n_tasks + 1)]
    tasks = {name: load_task(args.group, name) for name in task_ids}

    all_candidates = {}
    for name in task_ids:
        qid = f"conceptarc__{name}"
        cands = [c for c in extract_from_task_json(tasks[name], qid, enc)
                 if c.relation == args.relation]
        if cands:
            all_candidates[name] = cands

    contributing = sorted(all_candidates)
    if args.held_out not in contributing:
        print(f"{args.held_out} has no {args.relation}-candidates, nothing to do")
        return

    held_out_grids = grids_atoms(tasks[args.held_out], f"conceptarc__{args.held_out}", enc)

    all_symbols = set()
    for name in contributing:
        for c in all_candidates[name]:
            all_symbols.update([c.relation, c.color_x, c.color_y])
            all_symbols.update(c.sym_x)
            all_symbols.update(c.sym_y)
    symbol_vocab_size = max(len(all_symbols), 2)

    others = [t for t in contributing if t != args.held_out]

    # resumability: skip pairs already computed (e.g. from a chunk that
    # got cut off partway by the tool's wall-clock limit last time)
    already_done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                r = json.loads(line)
                if r["held_out"] == args.held_out and r["strategy"] == args.strategy:
                    already_done.add((r["a"], r["b"]))
    if already_done:
        print(f"resuming: {len(already_done)} pairs already done for "
              f"{args.held_out}/{args.strategy}, skipping those")

    n_written = 0
    with open(args.out, "a") as f:
        for i in range(len(others)):
            for j in range(i + 1, len(others)):
                a, b = others[i], others[j]
                if (a, b) in already_done:
                    continue
                if args.strategy == "first":
                    ca, cb = all_candidates[a][0], all_candidates[b][0]
                else:
                    ca, cb, _score = select_most_diverse_pair(all_candidates[a], all_candidates[b])
                blend_str, degenerate, matches = blend_and_check(ca, cb, held_out_grids)
                n_matched = sum(1 for v in matches.values() if v)
                n_total = len(matches)
                total_instances = sum(len(v) for v in matches.values())
                pattern_atoms = _extract_pattern_atoms(blend_str)
                mdl = mdl_gain(pattern_atoms, max(total_instances, 0), symbol_vocab_size)
                row = {
                    "held_out": args.held_out, "a": a, "b": b, "strategy": args.strategy,
                    "degenerate": degenerate, "n_matched": n_matched, "n_total": n_total,
                    "mdl_gain": mdl.dl_gain,
                    "in_matched": sum(1 for lbl, v in matches.items() if "_input" in lbl and v),
                    "in_total": sum(1 for lbl in matches if "_input" in lbl),
                    "out_matched": sum(1 for lbl, v in matches.items() if "_output" in lbl and v),
                    "out_total": sum(1 for lbl in matches if "_output" in lbl),
                }
                # write and flush IMMEDIATELY after each pair, not batched
                # at the end - a chunk cut off by the tool's wall-clock
                # limit must not lose already-computed results.
                f.write(json.dumps(row) + "\n")
                f.flush()
                n_written += 1
                print(row, flush=True)

    print(f"appended {n_written} rows to {args.out}")


if __name__ == "__main__":
    main()
