"""
experiment_insideoutside.py

A leave-one-task-out cross-validation sweep over ConceptARC's
InsideOutside group: for each task held out, build blends from
`contains`-candidate pairs drawn from the OTHER tasks, then check each
blend's coherence against every grid in the held-out task. This is the
natural next increment after Sprint B's single hand-picked blend
example - a genuine (if small-scale) first pass at E1's question ("does
within-group blending recover the group's defining concept?") rather
than one anecdote.

Scope note: to keep this tractable without the full Stage 1-2 frequency
filtering machinery (Sprint C), each contributing task supplies at most
its FIRST contains-candidate, not all of them - this is a real
simplification, not an oversight; a fuller sweep using every candidate
per task would need the frequency-filtered candidate pool Sprint C is
meant to build.

Usage: PYTHONPATH=python python3 python/experiment_insideoutside.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from encoder import GridEncoder  # noqa: E402
from enumerate import extract_from_task_json  # noqa: E402
from blend_pipeline import blend_and_check, _extract_pattern_atoms  # noqa: E402
from scoring import mdl_gain  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
GROUP_DIR = os.path.join(REPO_ROOT, "data", "ConceptARC", "corpus", "InsideOutside")
TASK_IDS = [f"InsideOutside{i}" for i in range(1, 11)]


def load_task(name):
    with open(os.path.join(GROUP_DIR, f"{name}.json")) as f:
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


def main():
    enc = GridEncoder()
    tasks = {name: load_task(name) for name in TASK_IDS}

    first_contains_candidate = {}
    all_grids = {}
    for name in TASK_IDS:
        qid = f"conceptarc__{name}"
        cands = [c for c in extract_from_task_json(tasks[name], qid, enc)
                 if c.relation == "contains"]
        if cands:
            first_contains_candidate[name] = cands[0]
        else:
            print(f"{name}: 0 contains-candidates (no containment structure in this task)")
        all_grids[name] = grids_atoms(tasks[name], qid, enc)

    contributing = sorted(first_contains_candidate)
    print(f"\n{len(contributing)}/{len(TASK_IDS)} tasks have a contains-candidate: {contributing}\n")

    # rough symbol vocabulary size for the MDL formula: distinct
    # predicate/color/axis symbols actually seen across the group,
    # not the full ARC palette - keeps the log2|symbols| term honest
    # to what this group's candidates actually use.
    all_symbols = set()
    for name in contributing:
        c = first_contains_candidate[name]
        all_symbols.update([c.relation, c.color_x, c.color_y])
        all_symbols.update(c.sym_x)
        all_symbols.update(c.sym_y)
    symbol_vocab_size = max(len(all_symbols), 2)

    results = []  # (held_out, source_a, source_b, degenerate, n_matched_grids, n_total_grids, mdl_gain)
    per_grid_matches = []  # (label, matches) across every run, for the input/output breakdown below
    for held_out in contributing:
        others = [t for t in contributing if t != held_out]
        for i in range(len(others)):
            for j in range(i + 1, len(others)):
                a, b = others[i], others[j]
                ca, cb = first_contains_candidate[a], first_contains_candidate[b]
                blend_str, degenerate, matches = blend_and_check(ca, cb, all_grids[held_out])
                n_matched = sum(1 for v in matches.values() if v)
                n_total = len(matches)
                total_match_instances = sum(len(v) for v in matches.values())
                pattern_atoms = _extract_pattern_atoms(blend_str)
                mdl = mdl_gain(pattern_atoms, max(total_match_instances, 0), symbol_vocab_size)
                results.append((held_out, a, b, degenerate, n_matched, n_total, mdl.dl_gain))
                if not degenerate:
                    per_grid_matches.extend(matches.items())

    print(f"{len(results)} (held_out_task, source_pair) blend+coherence checks run\n")

    print(f"{'held_out':<16} {'source_a':<16} {'source_b':<16} {'degenerate':<11} {'matched/total':<14} {'mdl_gain':<10}")
    for held_out, a, b, degenerate, n_matched, n_total, gain in results:
        print(f"{held_out:<16} {a:<16} {b:<16} {str(degenerate):<11} {n_matched}/{n_total:<12} {gain:.1f}")

    n_degenerate = sum(1 for r in results if r[3])
    n_nondeg = len(results) - n_degenerate
    nondeg_results = [r for r in results if not r[3]]
    total_matched = sum(r[4] for r in nondeg_results)
    total_grids = sum(r[5] for r in nondeg_results)

    print(f"\n--- summary ---")
    print(f"total blend+check runs: {len(results)}")
    print(f"degenerate blends: {n_degenerate} ({100*n_degenerate/len(results):.0f}%)")
    print(f"non-degenerate blends: {n_nondeg}")
    if total_grids:
        print(f"held-out grid match rate (non-degenerate blends only): "
              f"{total_matched}/{total_grids} ({100*total_matched/total_grids:.0f}%)")

    # Input vs output breakdown. Hypothesis worth testing directly
    # (raised while inspecting a single hand-picked example earlier):
    # InsideOutside puzzles often strip the containment structure away
    # as their transformation, so blends built from `contains`
    # candidates should generalize better to INPUT grids than OUTPUT
    # grids. Tracked inline above rather than re-running the sweep.
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

    # MDL ranking: does the score actually track how well a blend
    # generalized (n_matched/n_total), or is it just noise? Sorted
    # here, not asserted, since this is exploratory - Sprint C's real
    # deliverable is validating the correlation across MORE groups
    # before trusting MDL as an acceptance gate on its own.
    print(f"\n--- top 5 blends by MDL gain ---")
    ranked = sorted(results, key=lambda r: r[6], reverse=True)
    for held_out, a, b, degenerate, n_matched, n_total, gain in ranked[:5]:
        print(f"  {held_out:<16} {a}+{b:<16} matched {n_matched}/{n_total}, MDL gain {gain:.1f}")
    print(f"\n--- bottom 5 blends by MDL gain ---")
    for held_out, a, b, degenerate, n_matched, n_total, gain in ranked[-5:]:
        print(f"  {held_out:<16} {a}+{b:<16} matched {n_matched}/{n_total}, MDL gain {gain:.1f}")

    return results


if __name__ == "__main__":
    main()
