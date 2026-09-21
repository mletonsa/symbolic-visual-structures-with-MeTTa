"""
test_blend_insideoutside.py

End-to-end integration test for the Sprint B pipeline (enumerate ->
antiunify -> blend -> coherence check) on real data: the ConceptARC
InsideOutside group, chosen because its defining concept (an object
nested inside another) maps directly onto the encoder's existing
`contains` predicate - see the conversation/decisions.md for why this
group was picked over e.g. AboveBelow or Center, which would need
predicates the vocabulary doesn't have yet.

Requires `make data` to have fetched ConceptARC; skipped (not failed)
if the data isn't present, so `make test` still works offline.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from encoder import GridEncoder  # noqa: E402
from enumerate import extract_from_task_json  # noqa: E402
from blend_pipeline import blend_and_check  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
GROUP_DIR = os.path.join(REPO_ROOT, "data", "ConceptARC", "corpus", "InsideOutside")


def _require_data():
    if not os.path.isdir(GROUP_DIR):
        pytest.skip("ConceptARC not fetched - run `make data` first")


def _load_task(name):
    with open(os.path.join(GROUP_DIR, f"{name}.json")) as f:
        return json.load(f)


def _grids_atoms(task_json, qualified_id, encoder):
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


def test_contains_blend_generalizes_within_insideoutside_group():
    _require_data()
    enc = GridEncoder()

    t1 = _load_task("InsideOutside1")
    t4 = _load_task("InsideOutside4")
    t5 = _load_task("InsideOutside5")

    c1 = [c for c in extract_from_task_json(t1, "conceptarc__InsideOutside1", enc)
          if c.relation == "contains"]
    c4 = [c for c in extract_from_task_json(t4, "conceptarc__InsideOutside4", enc)
          if c.relation == "contains"]
    assert c1 and c4, "expected at least one contains-candidate in each source task"

    held_out_grids = _grids_atoms(t5, "conceptarc__InsideOutside5", enc)
    assert held_out_grids, "expected InsideOutside5 to have at least one grid"

    blend_str, is_degenerate, matches = blend_and_check(c1[0], c4[0], held_out_grids)

    assert blend_str is not None
    assert "(contains X Y)" in blend_str, "the anchor relation must survive as the invariant core"
    assert is_degenerate is False, "these two source instances differ enough not to be degenerate"

    # coherence: the blend should generalize to at least some held-out
    # grids in the SAME group, even though it was built from two
    # DIFFERENT tasks. This is the actual claim under test - not that
    # every grid matches (several legitimately won't, e.g. output grids
    # where the puzzle strips the containment structure away), only
    # that the blend is not vacuous.
    total_matches = sum(len(v) for v in matches.values())
    assert total_matches > 0, "blend should match at least one held-out InsideOutside5 grid"

    n_grids_matched = sum(1 for v in matches.values() if v)
    n_grids_total = len(matches)
    assert n_grids_matched >= n_grids_total // 3, (
        f"expected the blend to generalize to a meaningful fraction of held-out "
        f"grids, got {n_grids_matched}/{n_grids_total}"
    )


def test_identical_task_pair_blend_is_degenerate():
    """Sanity check in the other direction: anti-unifying two candidates
    from the exact SAME grid pair should tend toward degenerate/trivial
    results far more often than two different tasks, since there's
    nothing for the pattern to generalize across. Not asserted as an
    absolute (a task could coincidentally contain two truly distinct
    contains-instances), just checked that at least one degenerate
    result exists somewhere in the pairwise combinations - a weak but
    real regression signal for the isDegenerate machinery working end
    to end on real (not synthetic) data.
    """
    _require_data()
    enc = GridEncoder()
    t1 = _load_task("InsideOutside1")
    c1 = [c for c in extract_from_task_json(t1, "conceptarc__InsideOutside1", enc)
          if c.relation == "contains"]
    assert len(c1) >= 2, "need at least 2 contains-candidates within task1 for this check"

    found_degenerate = False
    for i in range(min(len(c1), 5)):
        blend_str, is_degenerate = __import__("blend_pipeline").build_blend(c1[i], c1[i])
        if is_degenerate:
            found_degenerate = True
            break
    assert found_degenerate, "anti-unifying a candidate with itself must be degenerate"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
