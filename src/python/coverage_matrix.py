"""
coverage_matrix.py

Extends check_group_relation_coverage.py from one group to all of them: for
every ConceptARC group and every anchor relation enumerate.py uses
(contains, sameColor, sameShape, alignedRow, alignedCol), reports what
fraction of grids carry that relation at all.

This is the ceiling from D14, computed in advance rather than after building
a sweep: a relation-anchored blend cannot match a grid with none of that
relation's atoms, so grid-level coverage bounds the best achievable held-out
match rate before anything is built. Doing this across every group answers
the question D7 answered by inspection for one group ("InsideOutside was
chosen because contains atoms fire on 3 of the first 5 tasks inspected") with
a real number for all of them, and flags which (group, relation) pairs have
enough usable tasks (tasks with >=1 grid carrying the relation) to support a
leave-one-out sweep at all - InsideOutside/contains needed 7, SameDifferent/
sameShape used 5.

Pure Python, no hyperon - each grid is encoded once and all five relations
are tallied from that single atom list, not five separate encodes.

Usage:
    python python/coverage_matrix.py
    python python/coverage_matrix.py --min-usable-tasks 5
    python python/coverage_matrix.py --out docs/coverage_matrix.md
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder  # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"
RELATIONS = ("contains", "sameColor", "sameShape", "alignedRow", "alignedCol")


def group_of(fp: str) -> str:
    """Same rule used throughout this project's scripts: the parent
    directory is authoritative, the file stem is the fallback."""
    parent = os.path.basename(os.path.dirname(fp))
    return parent if parent and parent not in (".", "corpus") else \
        os.path.splitext(os.path.basename(fp))[0]


def discover_groups():
    groups = {}
    for fp in sorted(glob.glob(CONCEPTARC_GLOB)):
        groups.setdefault(group_of(fp), []).append(fp)
    return groups


def grids_of(task_json):
    for split in ("train", "test"):
        for i, pair in enumerate(task_json.get(split, [])):
            for gname in ("input", "output"):
                if gname in pair:
                    yield f"{split}{i}_{gname}", pair[gname]


def measure_group(group_files, enc):
    """Returns, per relation: (grids_with, grids_total, tasks_with,
    tasks_total). One encode per grid, all five relations tallied at once."""
    grids_with = {r: 0 for r in RELATIONS}
    tasks_with = {r: 0 for r in RELATIONS}
    grids_total = 0
    tasks_total = len(group_files)

    for fp in group_files:
        tid = os.path.splitext(os.path.basename(fp))[0]
        qid = f"conceptarc__{tid}"
        tj = json.load(open(fp))
        task_has = {r: False for r in RELATIONS}
        for label, grid in grids_of(tj):
            atoms, _ = enc.encode(qid, label, grid)
            present = {a.predicate for a in atoms if a.predicate in RELATIONS}
            grids_total += 1
            for r in RELATIONS:
                if r in present:
                    grids_with[r] += 1
                    task_has[r] = True
        for r in RELATIONS:
            if task_has[r]:
                tasks_with[r] += 1

    return {r: (grids_with[r], grids_total, tasks_with[r], tasks_total)
            for r in RELATIONS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-usable-tasks", type=int, default=5,
                    help="flag (group, relation) pairs with at least this "
                         "many tasks carrying the relation as sweep-ready "
                         "(SameDifferent used 5, InsideOutside used 7)")
    ap.add_argument("--out", default=None,
                    help="also write the markdown table to this path")
    args = ap.parse_args()

    groups = discover_groups()
    if not groups:
        raise SystemExit(f"no groups found under {CONCEPTARC_GLOB} "
                         f"(cwd={os.getcwd()}, did you run `make data`?)")

    enc = GridEncoder()
    print(f"{len(groups)} groups found: {', '.join(sorted(groups))}\n")

    results = {}
    for i, (group, files) in enumerate(sorted(groups.items())):
        print(f"  [{i+1}/{len(groups)}] {group} ({len(files)} tasks)...")
        results[group] = measure_group(files, enc)

    # --- markdown matrix: coverage % per (group, relation) ---
    lines = ["# ConceptARC coverage matrix", "",
             "Grid-level coverage per group and anchor relation - the D14 "
             "ceiling, computed for every group at once. A cell is "
             "`grids_with/grids_total (pct%)`; `*` marks a relation with at "
             f"least {args.min_usable_tasks} usable tasks (tasks carrying "
             "that relation in at least one grid), the threshold a "
             "leave-one-out sweep needs.", "",
             "| Group | " + " | ".join(RELATIONS) + " |",
             "|---|" + "---|" * len(RELATIONS)]

    ready = []
    for group in sorted(results):
        row = [group]
        for r in RELATIONS:
            gw, gt, tw, tt = results[group][r]
            pct = 100 * gw / gt if gt else 0
            star = "*" if tw >= args.min_usable_tasks else ""
            row.append(f"{gw}/{gt} ({pct:.0f}%){star}")
            if tw >= args.min_usable_tasks:
                ready.append((group, r, gw, gt, tw, tt, pct))
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append(f"## Sweep-ready pairs (>={args.min_usable_tasks} usable tasks)")
    lines.append("")
    lines.append("| Group | Relation | Coverage | Usable tasks |")
    lines.append("|---|---|---|---|")
    for group, r, gw, gt, tw, tt, pct in sorted(ready, key=lambda x: -x[6]):
        lines.append(f"| {group} | {r} | {gw}/{gt} ({pct:.1f}%) | {tw}/{tt} |")
    if not ready:
        lines.append("| (none found) | | | |")

    out = "\n".join(lines)
    print("\n" + out)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write(out + "\n")
        print(f"\nwritten to {args.out}")


if __name__ == "__main__":
    main()
