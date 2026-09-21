"""
experiment_group_sweep.py

Generalized version of the InsideOutside leave-one-task-out sweep
(python/experiment_insideoutside.py, kept as-is for its own commit
history) - parameterized by ConceptARC group and anchor relation, so
the same validation can run against a second group without duplicating
the whole script. Used to check whether Sprint B's pipeline generalizes
beyond the one group it was built against, not just to re-derive the
same InsideOutside numbers a different way.

Usage:
  PYTHONPATH=python python3 python/experiment_group_sweep.py \\
      --group SameDifferent --relation sameShape
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

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
CORPUS_ROOT = os.path.join(REPO_ROOT, "data", "ConceptARC", "corpus")


def load_task(group, name):
    with open(os.path.join(CORPUS_ROOT, group, f"{name}.json")) as f:
        return json.load(f)


def grids_atoms(task_json, qualified_id, encoder):
    out = []
    for split in ("train", "test"):
        for i, pair in enumerate(task_json.get(split, [])):
            for gname in ("input", "output"):
                if gname not in pair:
                    continue
                label = f"{split}{i}_{gname}"
                atoms, _ = encoder.encode(qualified_id, label, pair[gname])
                out.append((label, atoms))
    return out


def run_sweep(group: str, relation: str, n_tasks: int = 10, strategy: str = "first"):
    """strategy: "first" (baseline - always use each task's first
    matching candidate) or "diverse" (use select_most_diverse_pair over
    ALL of each task's candidates - see docs/decisions.md D11 for why
    this is expected to do better, and enumerate.n_coincidental_fixed_slots
    for the mechanism)."""
    enc = GridEncoder()
    task_ids = [f"{group}{i}" for i in range(1, n_tasks + 1)]
    tasks = {name: load_task(group, name) for name in task_ids}

    all_candidates = {}
    all_grids = {}
    for name in task_ids:
        qid = f"conceptarc__{name}"
        cands = [c for c in extract_from_task_json(tasks[name], qid, enc)
                 if c.relation == relation]
        if cands:
            all_candidates[name] = cands
        else:
            print(f"{name}: 0 {relation}-candidates")
        all_grids[name] = grids_atoms(tasks[name], qid, enc)

    contributing = sorted(all_candidates)
    print(f"\n{len(contributing)}/{len(task_ids)} tasks have a {relation}-candidate: {contributing}\n")
    if len(contributing) < 3:
        print("fewer than 3 contributing tasks - leave-one-out sweep needs at least "
              "1 held-out + 2 sources, skipping")
        return []

    all_symbols = set()
    for name in contributing:
        for c in all_candidates[name]:
            all_symbols.update([c.relation, c.color_x, c.color_y])
            all_symbols.update(c.sym_x)
            all_symbols.update(c.sym_y)
    symbol_vocab_size = max(len(all_symbols), 2)

    results = []
    per_grid_matches = []
    for held_out in contributing:
        others = [t for t in contributing if t != held_out]
        for i in range(len(others)):
            for j in range(i + 1, len(others)):
                a, b = others[i], others[j]
                if strategy == "first":
                    ca, cb = all_candidates[a][0], all_candidates[b][0]
                elif strategy == "diverse":
                    ca, cb, _score = select_most_diverse_pair(all_candidates[a], all_candidates[b])
                else:
                    raise ValueError(f"unknown strategy: {strategy}")
                blend_str, degenerate, matches = blend_and_check(ca, cb, all_grids[held_out])
                n_matched = sum(1 for v in matches.values() if v)
                n_total = len(matches)
                total_match_instances = sum(len(v) for v in matches.values())
                pattern_atoms = _extract_pattern_atoms(blend_str)
                mdl = mdl_gain(pattern_atoms, max(total_match_instances, 0), symbol_vocab_size)
                results.append((held_out, a, b, degenerate, n_matched, n_total, mdl.dl_gain))
                if not degenerate:
                    per_grid_matches.extend(matches.items())

    print(f"{len(results)} (held_out_task, source_pair) blend+coherence checks run "
          f"[strategy={strategy}]\n")

    n_degenerate = sum(1 for r in results if r[3])
    nondeg_results = [r for r in results if not r[3]]
    total_matched = sum(r[4] for r in nondeg_results)
    total_grids = sum(r[5] for r in nondeg_results)

    print(f"--- summary: {group} / {relation} ---")
    print(f"total blend+check runs: {len(results)}")
    print(f"degenerate blends: {n_degenerate} ({100*n_degenerate/len(results):.0f}%)")
    if total_grids:
        print(f"held-out grid match rate (non-degenerate blends only): "
              f"{total_matched}/{total_grids} ({100*total_matched/total_grids:.0f}%)")

    in_matched = in_total = out_matched = out_total = 0
    for label, ms in per_grid_matches:
        if "_input" in label:
            in_total += 1
            in_matched += 1 if ms else 0
        elif "_output" in label:
            out_total += 1
            out_matched += 1 if ms else 0
    print(f"\n--- input vs output grid breakdown ---")
    if in_total:
        print(f"input grids:  {in_matched}/{in_total} ({100*in_matched/in_total:.0f}%)")
    if out_total:
        print(f"output grids: {out_matched}/{out_total} ({100*out_matched/out_total:.0f}%)")

    ranked = sorted(results, key=lambda r: r[6], reverse=True)
    print(f"\n--- top 3 blends by MDL gain ---")
    for held_out, a, b, degenerate, n_matched, n_total, gain in ranked[:3]:
        print(f"  {held_out:<16} {a}+{b:<16} matched {n_matched}/{n_total}, MDL gain {gain:.1f}")
    print(f"--- bottom 3 blends by MDL gain ---")
    for held_out, a, b, degenerate, n_matched, n_total, gain in ranked[-3:]:
        print(f"  {held_out:<16} {a}+{b:<16} matched {n_matched}/{n_total}, MDL gain {gain:.1f}")

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True)
    ap.add_argument("--relation", required=True)
    ap.add_argument("--n-tasks", type=int, default=10)
    ap.add_argument("--strategy", choices=["first", "diverse"], default="first")
    args = ap.parse_args()
    run_sweep(args.group, args.relation, args.n_tasks, args.strategy)
