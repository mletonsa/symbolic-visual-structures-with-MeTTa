"""
verify_table3.py

Re-runs the same measurement coverage_matrix.py does, using whatever
encoder.py is currently on the path, and diffs the result against the
exact figures published in docs/analysis/analysis2.md's Table 3.

Why this matters: Table 3, and everything downstream of it (the InsideOutside
sweep in Section 3, the novelty survey in Section 4, D9/D11/D13/D14/D16/D17
in decisions.md), depends on `contains` and `gridSymmetric` being computed
correctly (decisions.md D13). If encoder.py was not actually fixed when any
of that work was done, this is the fastest way to find out - a discrepancy
here means the recorded figures need re-checking; an exact match is real
evidence (though not for every single downstream computation individually)
that the encoder was already correct.

Only the `contains` column is checked in detail, since that is the column
D13's fix touched. `gridSymmetric` is not in Table 3 at all (it uses a
different table in D13 directly), so it is not checked here.

Usage:
    python python/verify_table3.py
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder  # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"

# Exact figures from docs/analysis/analysis2.md Table 3, contains column
# only (matched, total).
PUBLISHED_CONTAINS = {
    "AboveBelow": (11, 108), "Center": (17, 120), "CleanUp": (31, 106),
    "CompleteShape": (9, 102), "Copy": (43, 106), "Count": (13, 114),
    "ExtendToBoundary": (33, 118), "ExtractObjects": (32, 106),
    "FilledNotFilled": (31, 118), "HorizontalVertical": (25, 110),
    "InsideOutside": (46, 118), "MoveToBoundary": (5, 110),
    "Order": (14, 102), "SameDifferent": (33, 126),
    "TopBottom2D": (4, 128), "TopBottom3D": (15, 122),
}


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


def main():
    files_by_group = {}
    for fp in sorted(glob.glob(CONCEPTARC_GLOB)):
        files_by_group.setdefault(group_of(fp), []).append(fp)

    if not files_by_group:
        raise SystemExit(f"no ConceptARC files found under {CONCEPTARC_GLOB} "
                         f"(cwd={os.getcwd()}, did you run `make data`?)")

    enc = GridEncoder()
    mismatches = []
    print(f"{'Group':<20}{'Published':<14}{'Fresh run':<14}{'Match?'}")
    print("-" * 60)

    for group in sorted(PUBLISHED_CONTAINS):
        if group not in files_by_group:
            print(f"{group:<20}{'(not found in data)':<28}SKIPPED")
            continue
        grids_with, grids_total = 0, 0
        for fp in files_by_group[group]:
            tid = os.path.splitext(os.path.basename(fp))[0]
            qid = f"conceptarc__{tid}"
            tj = json.load(open(fp))
            for label, grid in grids_of(tj):
                atoms, _ = enc.encode(qid, label, grid)
                grids_total += 1
                if any(a.predicate == "contains" for a in atoms):
                    grids_with += 1

        pub_with, pub_total = PUBLISHED_CONTAINS[group]
        pub_str = f"{pub_with}/{pub_total}"
        fresh_str = f"{grids_with}/{grids_total}"
        match = (pub_with, pub_total) == (grids_with, grids_total)
        print(f"{group:<20}{pub_str:<14}{fresh_str:<14}{'OK' if match else '*** MISMATCH ***'}")
        if not match:
            mismatches.append((group, (pub_with, pub_total), (grids_with, grids_total)))

    print()
    if mismatches:
        print(f"{len(mismatches)} group(s) do not match the published table:")
        for group, pub, fresh in mismatches:
            print(f"  {group}: published {pub[0]}/{pub[1]}, fresh run {fresh[0]}/{fresh[1]}")
        print()
        print("This means Table 3 (and likely the InsideOutside sweep and the")
        print("novelty survey, both of which depend on the same contains")
        print("computation) were generated against a different encoder.py than")
        print("is currently active, and need to be re-verified.")
    else:
        print("All groups match exactly. This is evidence (not proof for every")
        print("downstream computation individually) that the encoder producing")
        print("Table 3 was already behaving as documented.")


if __name__ == "__main__":
    main()
