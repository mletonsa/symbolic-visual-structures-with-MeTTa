"""
check_group_relation_coverage.py

Counts, per task in a ConceptARC concept group, how many grids carry a given
relation and how many atoms of it exist. Written to answer one question after
the D13 `contains` fix: do InsideOutside2, 3 and 9 still have zero
containment structure, as D7 recorded from pre-fix output?

The answer decides the scope of the sweep re-run. If those three tasks are
still empty, the sweep stays at 7 tasks and 105 runs, directly comparable to
the D9 and D11 baselines. If any gained structure, a 10-task sweep is 360
runs and is NOT comparable to those baselines, so the 7-task scope should be
rerun first for a controlled before-and-after.

Usage:
    python python/check_group_relation_coverage.py
    python python/check_group_relation_coverage.py --group SameDifferent \
        --relation sameShape
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder  # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"


def task_sort_key(tid):
    m = re.search(r"(\d+)$", tid)
    return (tid[:m.start()] if m else tid, int(m.group(1)) if m else 0)


def group_of(fp: str) -> str:
    """ConceptARC's layout puts the concept group in the directory name and,
    per export_corpus.py, usually in the file stem too (e.g.
    corpus/InsideOutside/InsideOutside1.json). Do not rely on either alone:
    take the directory name as authoritative and fall back to the stem's
    leading non-digit run."""
    parent = os.path.basename(os.path.dirname(fp))
    if parent and parent not in (".", "corpus"):
        return parent
    stem = os.path.splitext(os.path.basename(fp))[0]
    return re.match(r"[^\d]*", stem).group(0) or stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="InsideOutside")
    ap.add_argument("--relation", default="contains")
    ap.add_argument("--list-groups", action="store_true",
                    help="Print the groups found on disk and exit")
    args = ap.parse_args()

    all_files = sorted(glob.glob(CONCEPTARC_GLOB))
    if not all_files:
        print(f"no files matched {CONCEPTARC_GLOB} from cwd {os.getcwd()!r} "
              f"(did you run `make data`?)")
        return

    groups = {}
    for fp in all_files:
        groups.setdefault(group_of(fp), []).append(fp)

    if args.list_groups:
        print(f"{len(all_files)} task files in {len(groups)} groups:\n")
        for g in sorted(groups):
            print(f"  {g:<24} {len(groups[g])} tasks   "
                  f"e.g. {os.path.basename(groups[g][0])}")
        return

    # Case-insensitive match so 'insideoutside' works too.
    key = next((g for g in groups if g.lower() == args.group.lower()), None)
    if key is None:
        print(f"no group matched {args.group!r}. Found {len(groups)} groups:")
        for g in sorted(groups):
            print(f"  {g:<24} {len(groups[g])} tasks   "
                  f"e.g. {os.path.basename(groups[g][0])}")
        return
    files = groups[key]

    encoder = GridEncoder()
    rows = []
    for fp in files:
        tid = os.path.splitext(os.path.basename(fp))[0]
        with open(fp) as f:
            task = json.load(f)

        n_grids = n_grids_with = n_atoms = 0
        n_in = n_out = 0
        for split in ("train", "test"):
            for pair in task.get(split, []):
                for gname in ("input", "output"):
                    if gname not in pair:
                        continue
                    atoms, _ = encoder.encode(tid, f"{split}_{gname}",
                                              pair[gname])
                    k = sum(1 for a in atoms if a.predicate == args.relation)
                    n_grids += 1
                    n_atoms += k
                    if k:
                        n_grids_with += 1
                        if gname == "input":
                            n_in += 1
                        else:
                            n_out += 1
        rows.append((tid, n_grids, n_grids_with, n_atoms, n_in, n_out))

    rows.sort(key=lambda r: task_sort_key(r[0]))

    print(f"\nGroup: {key}   relation: {args.relation}   "
          f"({len(files)} task files)\n")
    print(f"{'task':<22} {'grids':>6} {'w/ rel':>7} {'atoms':>7} "
          f"{'in':>4} {'out':>4}")
    print("-" * 54)
    for tid, n_grids, n_with, n_atoms, n_in, n_out in rows:
        flag = "   <-- none" if n_atoms == 0 else ""
        print(f"{tid:<22} {n_grids:>6} {n_with:>7} {n_atoms:>7} "
              f"{n_in:>4} {n_out:>4}{flag}")

    usable = [r[0] for r in rows if r[3] > 0]
    empty = [r[0] for r in rows if r[3] == 0]
    print(f"\ntasks with {args.relation} structure : {len(usable)}/{len(rows)}")
    if empty:
        print(f"tasks with none                : {', '.join(empty)}")
    n = len(usable)
    if n >= 3:
        pairs = (n - 1) * (n - 2) // 2
        print(f"\nleave-one-out sweep scope: {n} held-out tasks x {pairs} "
              f"pairs = {n * pairs} blend+check runs")


if __name__ == "__main__":
    main()
