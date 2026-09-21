"""
sample_for_rating.py

Builds the sample for the qualitative evaluation rubric
(docs/rating/rubric.md). Three outputs:

  docs/rating/cards/<blend_id>.txt     one concept card per sampled blend,
                                        for the rater - no automated scores
  docs/rating/ratings_template.csv     blend_id + empty score columns, for
                                        the rater to fill in
  docs/rating/manifest_with_scores.json  blend_id -> every automated metric
                                        (verdict, n_fixed, symmetry sets,
                                        match count, MDL gain). Stays CLOSED
                                        until rating is done - opening it
                                        before rating defeats the point of
                                        the comparison.

Sampling is stratified by novelty verdict (trivial / symmetry_only /
with_scalar), computed cheaply over the full pair space via build_blend +
assess_novelty (no coherence checking, per D9 this is fast and pure). Only
the final sampled blends get coherence-checked, against every other task in
the group that isn't one of the pair's two source tasks (capped by
--n-heldout for cost control), which is the expensive part.

Card generation needs pretty.render_grid(grid) -> multi-line string, the
only part of pretty.py this script assumes. If pretty.py can render a
highlighted subset of a grid (the research plan's phrasing suggests it
might), swap render_source_grid below to use it - source-grid objects are
currently described in text (colour and size) rather than highlighted,
since Candidate does not carry bbox and this script does not attempt to
re-derive it.

Usage:
    python python/sample_for_rating.py
    python python/sample_for_rating.py --group SameDifferent --relation sameShape
    python python/sample_for_rating.py --n-per-bucket 8 --seed 1
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from encoder import GridEncoder                    # noqa: E402
import enumerate as enum_mod                         # noqa: E402
import blend_pipeline as bp                           # noqa: E402
import scoring                                          # noqa: E402
from novelty import assess_novelty, ALL_AXES             # noqa: E402
from pretty import render_grid                            # noqa: E402

CONCEPTARC_GLOB = "data/ConceptARC/corpus/*/*.json"
OUT_DIR = "docs/rating"


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


def gloss(c1, c2, r) -> str:
    """Plain-language description of what the blend claims, built from the
    novelty profile rather than the raw MeTTa pattern - this is the text a
    rater actually reads, so it should read like a sentence, not an atom
    list."""
    rel_word = {"contains": "contains", "sameColor": "shares a colour with",
                "sameShape": "shares a shape with", "alignedRow": "is row-aligned with",
                "alignedCol": "is column-aligned with"}.get(c1.relation, c1.relation)
    parts = [f"An object X {rel_word} an object Y."]

    labels = {"colorX": "X's colour", "colorY": "Y's colour",
              "sizeX": "X's size", "sizeY": "Y's size",
              "shapeX": "X's shape", "shapeY": "Y's shape"}
    if r.fixed_slots:
        fixed_desc = []
        vals = {"colorX": c1.color_x, "colorY": c1.color_y,
                "sizeX": c1.size_x, "sizeY": c1.size_y}
        for slot in sorted(r.fixed_slots):
            if slot in vals:
                fixed_desc.append(f"{labels[slot]} is fixed at {vals[slot]}")
            else:
                fixed_desc.append(f"{labels[slot]} is fixed (both instances match)")
        parts.append(" ".join(d + "." for d in fixed_desc))

    if r.shared_sym_x:
        note = " (this holds for all six axes - common for small/simple shapes, may not be meaningful)" \
            if r.shared_sym_x == ALL_AXES else ""
        parts.append(f"X is symmetric under: {', '.join(sorted(r.shared_sym_x))}{note}.")
    if r.shared_sym_y:
        note = " (this holds for all six axes - common for small/simple shapes, may not be meaningful)" \
            if r.shared_sym_y == ALL_AXES else ""
        parts.append(f"Y is symmetric under: {', '.join(sorted(r.shared_sym_y))}{note}.")

    if not r.fixed_slots and not r.shared_sym_x and not r.shared_sym_y:
        parts.append("Nothing else is claimed beyond the relation itself.")

    return " ".join(parts)


def render_source_grid(task_grids, grid_label, cand, role):
    grid = task_grids[grid_label]
    color = cand.color_x if role == "X" else cand.color_y
    size = cand.size_x if role == "X" else cand.size_y
    lines = [f"grid {grid_label}:"]
    lines += ["  " + row for row in render_grid(grid).split("\n")]
    lines.append(f"  ({role} is the {color} object with {size} cells)")
    return "\n".join(lines)


def write_card(path, blend_id, c1, c2, r, task_a, task_a_grids,
                task_b, task_b_grids, matched, unmatched, held_out_grids):
    lines = [
        f"Concept card: {blend_id}",
        "=" * 60,
        "",
        "What this concept claims:",
        "  " + gloss(c1, c2, r),
        "",
        "Built from:",
        "",
        render_source_grid(task_a_grids, c1.grid, c1, "X"),
        "",
        render_source_grid(task_b_grids, c2.grid, c2, "Y"),
        "",
        "Checked against grids from other tasks it was not built from:",
        "",
    ]
    shown = 0
    for label, grid in matched[:2]:
        lines.append(f"MATCHES  {label}:")
        lines += ["  " + row for row in render_grid(grid).split("\n")]
        lines.append("")
        shown += 1
    for label, grid in unmatched[:1]:
        lines.append(f"DOES NOT MATCH  {label}:")
        lines += ["  " + row for row in render_grid(grid).split("\n")]
        lines.append("")
        shown += 1
    if shown == 0:
        lines.append("(no held-out grids were checked, or none available)")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="InsideOutside")
    ap.add_argument("--relation", default="contains")
    ap.add_argument("--n-per-bucket", type=int, default=8,
                    help="target sample count per novelty-verdict bucket")
    ap.add_argument("--n-heldout", type=int, default=3,
                    help="how many other tasks to check each sampled blend against")
    ap.add_argument("--vocab-size", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    files = [fp for fp in sorted(glob.glob(CONCEPTARC_GLOB))
             if group_of(fp).lower() == args.group.lower()]
    if not files:
        raise SystemExit(f"no files found for group {args.group!r}")

    enc = GridEncoder()
    pools, task_grids, task_json = {}, {}, {}
    for fp in files:
        tid = os.path.splitext(os.path.basename(fp))[0]
        qid = f"conceptarc__{tid}"
        tj = json.load(open(fp))
        task_json[tid] = tj
        task_grids[tid] = dict(grids_of(tj))
        cands = [c for c in enum_mod.extract_from_task_json(tj, qid, enc)
                 if c.relation == args.relation]
        if cands:
            pools[tid] = cands

    task_ids = sorted(pools)
    print(f"{len(task_ids)} tasks with {args.relation} candidates")

    buckets = {"trivial": [], "novel_symmetry_only": [], "novel_with_scalar": []}
    for i, ta in enumerate(task_ids):
        for tb in task_ids[i + 1:]:
            for c1, c2 in enum_mod.select_pairs(pools[ta], pools[tb]):
                r = assess_novelty(c1, c2)
                if r.verdict == "trivial":
                    buckets["trivial"].append((c1, c2, r))
                elif r.verdict == "novel" and r.n_fixed == 0:
                    buckets["novel_symmetry_only"].append((c1, c2, r))
                elif r.verdict == "novel":
                    buckets["novel_with_scalar"].append((c1, c2, r))
                # parent_echo pairs are excluded: rating a blend that is
                # identical to its own parents tells a rater nothing new.

    for k, v in buckets.items():
        print(f"  {k}: {len(v)} available")

    sample = []
    for bucket_name, items in buckets.items():
        rng.shuffle(items)
        for c1, c2, r in items[:args.n_per_bucket]:
            sample.append((bucket_name, c1, c2, r))
    print(f"sampled {len(sample)} blends total\n")

    manifest = {}
    csv_rows = ["blend_id,novelty_1to3,consistency_1to3,value_1to3,notes"]

    for idx, (bucket_name, c1, c2, r) in enumerate(sample):
        blend_id = f"{args.group}_{args.relation}_{idx:03d}"
        blend_str, is_degenerate = bp.build_blend(c1, c2)
        if blend_str is None:
            continue
        pattern = bp._extract_pattern_atoms(blend_str)

        other_tasks = [t for t in task_ids if t not in (c1.task.split("__")[-1],
                                                         c2.task.split("__")[-1])]
        rng.shuffle(other_tasks)
        held_out = other_tasks[:args.n_heldout]

        grids_checked = []
        for t in held_out:
            for label, grid in task_grids[t].items():
                qid = f"conceptarc__{t}"
                atoms, _ = enc.encode(qid, label, grid)
                grids_checked.append((f"{t}/{label}", grid, atoms))

        res = bp.check_coherence_per_grid(
            pattern, [(lbl, atoms) for lbl, grid, atoms in grids_checked])
        matched = [(lbl, grid) for lbl, grid, _ in grids_checked if res.get(lbl)]
        unmatched = [(lbl, grid) for lbl, grid, _ in grids_checked if not res.get(lbl)]
        total_matches = sum(len(v) for v in res.values())
        n_grids_matched = sum(1 for v in res.values() if v)

        mdl = scoring.mdl_gain(pattern, total_matches, args.vocab_size)

        card_path = f"{OUT_DIR}/cards/{blend_id}.txt"
        write_card(card_path, blend_id, c1, c2, r,
                  c1.task, task_grids[c1.task.split("__")[-1]],
                  c2.task, task_grids[c2.task.split("__")[-1]],
                  matched, unmatched, grids_checked)

        manifest[blend_id] = {
            "novelty_bucket": bucket_name,
            "novelty_verdict": r.verdict,
            "n_fixed": r.n_fixed,
            "fixed_slots": sorted(r.fixed_slots),
            "shared_sym_x": sorted(r.shared_sym_x),
            "shared_sym_y": sorted(r.shared_sym_y),
            "is_degenerate": is_degenerate,
            "n_grids_checked": len(grids_checked),
            "n_grids_matched": n_grids_matched,
            "total_match_instances": total_matches,
            "mdl_gain": mdl.dl_gain,
            "mdl_worth_it": mdl.worth_it,
            "source_task_a": c1.task,
            "source_task_b": c2.task,
        }
        csv_rows.append(f"{blend_id},,,,")
        print(f"  {blend_id}  ({bucket_name})  "
              f"matched {n_grids_matched}/{len(grids_checked)} held-out grids")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/manifest_with_scores.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open(f"{OUT_DIR}/ratings_template.csv", "w") as f:
        f.write("\n".join(csv_rows) + "\n")

    print(f"\n{len(manifest)} cards written to {OUT_DIR}/cards/")
    print(f"rate from {OUT_DIR}/ratings_template.csv against the cards only")
    print(f"do not open {OUT_DIR}/manifest_with_scores.json until rating is done")


if __name__ == "__main__":
    main()
