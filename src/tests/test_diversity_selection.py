"""
test_diversity_selection.py

Regression test for enumerate.n_coincidental_fixed_slots and
select_most_diverse_pair, using the real InsideOutside1/6 candidates
that motivated this heuristic (see docs/decisions.md D11). Locks in the
exact 4x4 grid of (coincidental_fixed_slots, actual_held_out_matches)
pairs found during development, so a future encoder or candidate change
that silently breaks this correlation gets caught.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from encoder import GridEncoder  # noqa: E402
from enumerate import (extract_from_task_json, n_coincidental_fixed_slots,  # noqa: E402
                        select_most_diverse_pair)

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
GROUP_DIR = os.path.join(REPO_ROOT, "data", "ConceptARC", "corpus", "InsideOutside")


def _require_data():
    if not os.path.isdir(GROUP_DIR):
        pytest.skip("ConceptARC not fetched - run `make data` first")


def _load(name):
    with open(os.path.join(GROUP_DIR, f"{name}.json")) as f:
        return json.load(f)


def test_diversity_score_matches_known_grid():
    """Locks in the exact scores found during development (see
    docs/decisions.md D11) for the InsideOutside1 x InsideOutside6
    contains-candidates at indices 0, 2, 4, 6 in each task."""
    _require_data()
    enc = GridEncoder()
    t1, t6 = _load("InsideOutside1"), _load("InsideOutside6")
    c1 = [c for c in extract_from_task_json(t1, "conceptarc__InsideOutside1", enc)
          if c.relation == "contains"]
    c6 = [c for c in extract_from_task_json(t6, "conceptarc__InsideOutside6", enc)
          if c.relation == "contains"]

    expected = {
        (0, 0): 0, (0, 2): 2, (0, 4): 3, (0, 6): 3,
        (2, 0): 1, (2, 2): 3, (2, 4): 2, (2, 6): 2,
        (4, 0): 1, (4, 2): 3, (4, 4): 2, (4, 6): 2,
        (6, 0): 1, (6, 2): 3, (6, 4): 2, (6, 6): 2,
    }
    for (i1, i6), expected_score in expected.items():
        score = n_coincidental_fixed_slots(c1[i1], c6[i6])
        assert score == expected_score, f"c1[{i1}] x c6[{i6}]: expected {expected_score}, got {score}"


def test_select_most_diverse_pair_finds_the_zero_score_pair():
    """The (c1[0], c6[0]) pair scored 0 (fully diverse) and was the one
    that actually matched 7/12 held-out grids - select_most_diverse_pair
    should find exactly that pair without needing to run MeTTa at all."""
    _require_data()
    enc = GridEncoder()
    t1, t6 = _load("InsideOutside1"), _load("InsideOutside6")
    c1 = [c for c in extract_from_task_json(t1, "conceptarc__InsideOutside1", enc)
          if c.relation == "contains"]
    c6 = [c for c in extract_from_task_json(t6, "conceptarc__InsideOutside6", enc)
          if c.relation == "contains"]

    best_a, best_b, score = select_most_diverse_pair(c1, c6)
    assert score == 0
    assert best_a.obj_x == c1[0].obj_x and best_a.obj_y == c1[0].obj_y


def test_select_most_diverse_pair_returns_none_for_empty_pools():
    a, b, score = select_most_diverse_pair([], [])
    assert (a, b, score) == (None, None, None)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
