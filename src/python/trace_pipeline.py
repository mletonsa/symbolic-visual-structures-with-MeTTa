"""
trace_pipeline.py

Dumps one real task through every stage of the pipeline, so the
implementation chapter can quote actual output instead of invented
examples. Writes nothing and changes nothing; it only prints.

Run from the repo root:
    python python/trace_pipeline.py > docs/pipeline_trace.txt 2>&1

Options:
    --task InsideOutside1     which ConceptARC task to trace
    --other InsideOutside4    the task to pair its candidates against
    --held-out InsideOutside5 the task to check the blend against
    --relation contains       anchor relation
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder                                   # noqa: E402
import enumerate as enum_mod                                      # noqa: E402
import blend_pipeline as bp                                       # noqa: E402
import scoring                                                    # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"
RULE = "=" * 72


def find_task(name):
    for fp in sorted(glob.glob(CONCEPTARC_GLOB)):
        if os.path.splitext(os.path.basename(fp))[0].lower() == name.lower():
            return fp
    raise SystemExit(f"task {name!r} not found under {CONCEPTARC_GLOB} "
                     f"(cwd is {os.getcwd()})")


def head(title):
    print(f"\n{RULE}\n{title}\n{RULE}")


def grids_of(task_json):
    for split in ("train", "test"):
        for i, pair in enumerate(task_json.get(split, [])):
            for gname in ("input", "output"):
                if gname in pair:
                    yield f"{split}{i}_{gname}", pair[gname]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="InsideOutside1")
    ap.add_argument("--other", default="InsideOutside4")
    ap.add_argument("--held-out", default="InsideOutside5")
    ap.add_argument("--relation", default="contains")
    ap.add_argument("--vocab-size", type=int, default=64,
                    help="symbol vocabulary size used by the MDL formula")
    args = ap.parse_args()

    enc = GridEncoder()

    # ---------------------------------------------------------------- 1
    head("STAGE 0  the grid, and the atoms it becomes")
    tj = json.load(open(find_task(args.task)))
    qid = f"conceptarc__{args.task}"

    label, grid = None, None
    for lbl, g in grids_of(tj):
        atoms, objs = enc.encode(qid, lbl, g)
        if any(a.predicate == args.relation for a in atoms):
            label, grid = lbl, g
            break
    if label is None:
        raise SystemExit(f"no grid in {args.task} has a {args.relation} atom")

    atoms, objs = enc.encode(qid, label, grid)
    print(f"task {args.task}, grid {label}, "
          f"{len(grid)}x{len(grid[0])}, {len(objs)} objects\n")
    for row in grid:
        print("   " + " ".join("." if v == 0 else str(v) for v in row))
    cellish = {"cell", "coord", "color", "adj", "member"}
    print(f"\n{len(atoms)} atoms total, "
          f"{sum(1 for a in atoms if a.predicate in cellish)} of them cell-level")
    print("\nobject level and above:")
    for a in atoms:
        if a.predicate not in cellish:
            print("   ", a)

    # ---------------------------------------------------------------- 2
    head("STAGE 1  candidates extracted from that grid")
    cands = enum_mod.extract_candidates(qid, label, atoms)
    print(f"{len(cands)} candidates, "
          f"{sum(1 for c in cands if c.relation == args.relation)} on "
          f"{args.relation}\n")
    for c in cands[:6]:
        print(f"   {c.relation:<11} x={c.color_x}/{c.size_x} "
              f"y={c.color_y}/{c.size_y}  from {c.obj_x} {c.obj_y}")
    print("\nthe first one as MeTTa, which is what antiunify.metta receives:\n")
    first = next(c for c in cands if c.relation == args.relation)
    print("   ", first.to_metta())

    # ---------------------------------------------------------------- 3
    head("STAGE 2  pairing against another task's candidates")
    tj2 = json.load(open(find_task(args.other)))
    qid2 = f"conceptarc__{args.other}"
    pool_a = [c for c in enum_mod.extract_from_task_json(tj, qid, enc)
              if c.relation == args.relation]
    pool_b = [c for c in enum_mod.extract_from_task_json(tj2, qid2, enc)
              if c.relation == args.relation]
    print(f"{args.task}: {len(pool_a)} candidates   "
          f"{args.other}: {len(pool_b)} candidates")

    n_pairs = sum(1 for _ in enum_mod.select_pairs(pool_a, pool_b))
    print(f"valid pairs: {n_pairs}")

    print("\ncoincidental fixed slots for the first few pairs "
          "(lower is better):")
    for i, (c1, c2) in enumerate(enum_mod.select_pairs(pool_a, pool_b)):
        if i >= 8:
            break
        print(f"   pair {i}: {enum_mod.n_coincidental_fixed_slots(c1, c2)}")

    c1, c2, score = enum_mod.select_most_diverse_pair(pool_a, pool_b)
    print(f"\nselected pair has {score} coincidental fixed slots")
    print("   A:", c1.to_metta())
    print("   B:", c2.to_metta())

    # ---------------------------------------------------------------- 4
    head("STAGE 3  the generic space")
    m = bp._get_blend_runtime()
    gs = m.run(f"!(antiunifyPair {c1.to_metta()} {c2.to_metta()})")
    print(gs[0][0] if gs and gs[0] else "(antiunifyPair returned nothing)")

    # ---------------------------------------------------------------- 5
    head("STAGE 4  the blend")
    blend_str, degenerate = bp.build_blend(c1, c2)
    print(blend_str)
    print(f"\ndegenerate: {degenerate}")

    pattern = bp._extract_pattern_atoms(blend_str)
    print("\nthe materialized pattern on its own:\n")
    for a in scoring.split_pattern_atoms(pattern):
        print("   ", a)

    print("\nturned into a query:\n")
    print("   ", bp.pattern_to_query(pattern))

    # ---------------------------------------------------------------- 6
    head("STAGE 5a  coherence against a held-out task")
    tj3 = json.load(open(find_task(args.held_out)))
    qid3 = f"conceptarc__{args.held_out}"
    held = [(lbl, enc.encode(qid3, lbl, g)[0]) for lbl, g in grids_of(tj3)]
    res = bp.check_coherence_per_grid(pattern, held)
    hit = sum(1 for v in res.values() if v)
    print(f"{args.held_out}: matched {hit} of {len(res)} grids\n")
    for lbl, v in res.items():
        print(f"   {lbl:<18} {len(v):>3} matches")
    ins = [l for l, v in res.items() if v and "input" in l]
    outs = [l for l, v in res.items() if v and "output" in l]
    print(f"\ninput grids matched: {len(ins)}   output grids matched: {len(outs)}")

    # ---------------------------------------------------------------- 7
    head("STAGE 5b  MDL")
    total = sum(len(v) for v in res.values())
    r = scoring.mdl_gain(pattern, total, args.vocab_size)
    print(f"total match instances : {total}")
    print(f"grids matched         : {hit}")
    print(f"dl_definition         : {r.dl_definition:.1f} bits")
    print(f"dl_raw_per_instance   : {r.dl_raw_per_instance:.1f} bits")
    print(f"dl_rewritten_per_inst : {r.dl_rewritten_per_instance:.1f} bits")
    print(f"dl_gain               : {r.dl_gain:.1f} bits")
    print(f"worth_it              : {r.worth_it}")


if __name__ == "__main__":
    main()
