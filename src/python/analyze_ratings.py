"""
analyze_ratings.py

Run after docs/rating/ratings_template.csv has been filled in by hand.
Joins human ratings against docs/rating/manifest_with_scores.json (the
automated metrics kept hidden during rating) and reports where they agree
and where they don't.

This is the actual point of the exercise: three human-scored dimensions
against three automated proxies (novelty verdict, coherence match rate,
MDL gain), on the same sample. Agreement across all of them would be a much
stronger claim than any one measure alone; disagreement is worth reporting
exactly as honestly as D10's MDL-ranking surprise was, since a scoring
mechanism a human would call wrong is a finding, not an embarrassment.

Usage:
    python python/analyze_ratings.py
    python python/analyze_ratings.py --ratings path/to/filled_in.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as stats


def load_ratings(path):
    out = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            bid = row["blend_id"]
            vals = {}
            for dim in ("novelty_1to3", "consistency_1to3", "value_1to3"):
                v = row.get(dim, "").strip()
                vals[dim] = int(v) if v else None
            vals["notes"] = row.get("notes", "").strip()
            out[bid] = vals
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratings", default="docs/rating/ratings_template.csv")
    ap.add_argument("--manifest", default="docs/rating/manifest_with_scores.json")
    args = ap.parse_args()

    ratings = load_ratings(args.ratings)
    manifest = json.load(open(args.manifest))

    unrated = [b for b, r in ratings.items() if r["novelty_1to3"] is None]
    if unrated:
        print(f"{len(unrated)} blends have no rating yet: {unrated[:5]}"
              f"{' ...' if len(unrated) > 5 else ''}")
    rated = {b: r for b, r in ratings.items() if r["novelty_1to3"] is not None
             and b in manifest}
    print(f"{len(rated)} rated blends joined against the manifest\n")
    if not rated:
        return

    print("=" * 64)
    print("HUMAN NOVELTY vs AUTOMATED VERDICT")
    print("=" * 64)
    by_verdict = {}
    for b, r in rated.items():
        v = manifest[b]["novelty_verdict"]
        by_verdict.setdefault(v, []).append(r["novelty_1to3"])
    for v, scores in sorted(by_verdict.items()):
        print(f"  {v:<10} n={len(scores):<3} mean human novelty score "
              f"{stats.mean(scores):.2f}  (scores: {sorted(scores)})")
    print("\n  If the automated verdict tracks human judgement, 'trivial' "
          "should cluster low\n  and 'novel_with_scalar'/'novel_symmetry_only' "
          "should cluster higher. A trivial-\n  verdict blend that humans "
          "scored 3, or a novel-verdict blend scored 1, is worth\n  reading "
          "the card and notes for directly.")

    print(f"\n{'=' * 64}")
    print("HUMAN VALUE vs COHERENCE MATCH RATE")
    print("=" * 64)
    pairs = [(r["value_1to3"], manifest[b]["n_grids_matched"] / max(manifest[b]["n_grids_checked"], 1))
             for b, r in rated.items()]
    for value_score in (1, 2, 3):
        rates = [rate for v, rate in pairs if v == value_score]
        if rates:
            print(f"  value={value_score}  n={len(rates):<3} "
                  f"mean match rate {stats.mean(rates):.2f}")

    print(f"\n{'=' * 64}")
    print("HUMAN CONSISTENCY vs MDL WORTH_IT")
    print("=" * 64)
    for worth in (True, False):
        scores = [r["consistency_1to3"] for b, r in rated.items()
                 if manifest[b]["mdl_worth_it"] == worth]
        if scores:
            print(f"  mdl_worth_it={worth!s:<6} n={len(scores):<3} "
                  f"mean human consistency {stats.mean(scores):.2f}")

    print(f"\n{'=' * 64}")
    print("STRONGEST DISAGREEMENTS (worth reading individually)")
    print("=" * 64)
    flagged = []
    for b, r in rated.items():
        m = manifest[b]
        if m["novelty_verdict"] == "trivial" and r["novelty_1to3"] == 3:
            flagged.append((b, "automated=trivial, human novelty=3"))
        if m["novelty_verdict"] != "trivial" and r["novelty_1to3"] == 1:
            flagged.append((b, f"automated={m['novelty_verdict']}, human novelty=1"))
    if flagged:
        for b, note in flagged:
            print(f"  {b}: {note}")
            if rated[b]["notes"]:
                print(f"    rater note: {rated[b]['notes']}")
    else:
        print("  none - automated verdict and human novelty score never "
              "landed at opposite ends")


if __name__ == "__main__":
    main()
