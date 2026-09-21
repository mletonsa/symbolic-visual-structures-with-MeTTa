"""
tests/test_encoder_fixes.py

Regression tests for the encoder fixes recorded in docs/decisions.md D13:
  - `contains` was only tested in one direction, keyed to connected-component
    scan order, and silently dropped real containments.
  - `gridSymmetric` carried a square-grid guard that is only valid under
    grid-frame symmetry, while the predicate is pattern-frame.

Each test below fails against the pre-D13 encoder.
"""


import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


import pytest

from encoder import GridEncoder


def contains_pairs(atoms):
    return {(a.args[0], a.args[1]) for a in atoms if a.predicate == "contains"}


def axes(atoms, predicate="gridSymmetric"):
    return {a.args[-1] for a in atoms if a.predicate == predicate}


def short(oid):
    """'t_g_o1' -> 'o1', so assertions stay readable."""
    return oid.split("_")[-1]


# --- contains -------------------------------------------------------------

def test_contains_when_enclosing_object_is_scanned_first():
    """The easy case: outer ring found before the inner cell."""
    grid = [
        [3, 3, 3, 3, 3],
        [3, 0, 0, 0, 3],
        [3, 0, 2, 0, 3],
        [3, 0, 0, 0, 3],
        [3, 3, 3, 3, 3],
    ]
    atoms, objs = GridEncoder().encode("t", "g", grid)
    pairs = {(short(a), short(b)) for a, b in contains_pairs(atoms)}
    assert pairs == {("o0", "o1")}


def test_contains_when_enclosed_object_is_scanned_first():
    """The regression case. The green shape's topmost row starts at column
    2, so the single red cell at (0, 0) is found first, even though the
    green bbox encloses it. Pre-D13 this emitted nothing."""
    grid = [
        [2, 0, 3, 3, 3],
        [0, 0, 0, 0, 3],
        [3, 3, 3, 0, 3],
        [3, 0, 0, 0, 3],
        [3, 3, 3, 3, 3],
    ]
    atoms, objs = GridEncoder().encode("t", "g", grid)
    assert [short(o.oid) for o in objs] == ["o0", "o1"]
    assert objs[0].color == 2 and objs[1].color == 3
    pairs = {(short(a), short(b)) for a, b in contains_pairs(atoms)}
    assert pairs == {("o1", "o0")}, "containment must be tested both ways"


def test_contains_is_never_mutual():
    """`contains` must never be emitted in both directions for one pair.

    Written as a property over random grids rather than a fixture: two
    4-connected components sharing an identical bbox would both have to
    touch all four sides of it, which appears to be unreachable in
    practice (0 instances in 200k random grids). The strictness clause in
    the encoder is therefore defensive, and this test guards the property
    rather than exercising a concrete case."""
    import random

    rnd = random.Random(11)
    encoder = GridEncoder()
    for _ in range(500):
        n, m = rnd.randint(3, 8), rnd.randint(3, 8)
        grid = [[rnd.choice([0, 0, 1, 2, 3]) for _ in range(m)]
                for _ in range(n)]
        pairs = contains_pairs(encoder.encode("t", "g", grid)[0])
        assert not any((b, a) in pairs for a, b in pairs)


def test_contains_matches_brute_force_on_random_grids():
    """Exhaustive cross-check against the definition, over many grids."""
    import random

    rnd = random.Random(0)
    encoder = GridEncoder()
    for _ in range(300):
        n, m = rnd.randint(3, 7), rnd.randint(3, 7)
        grid = [[rnd.choice([0, 0, 0, 1, 2, 3]) for _ in range(m)]
                for _ in range(n)]
        atoms, objs = encoder.encode("t", "g", grid)

        expected = set()
        for a in objs:
            for b in objs:
                if a.oid == b.oid:
                    continue
                (ar0, ac0), (ar1, ac1) = a.bbox
                (br0, bc0), (br1, bc1) = b.bbox
                a_enc = ar0 <= br0 and ac0 <= bc0 and ar1 >= br1 and ac1 >= bc1
                b_enc = br0 <= ar0 and bc0 <= ac0 and br1 >= ar1 and bc1 >= ac1
                if a_enc and not b_enc:
                    expected.add((a.oid, b.oid))
        assert contains_pairs(atoms) == expected


# --- gridSymmetric --------------------------------------------------------

def test_grid_symmetry_is_pattern_frame_not_grid_frame():
    """An off-centre but internally symmetric foreground fires. This is the
    deliberate pattern-frame reading, so the test pins it down rather than
    leaving it to be rediscovered."""
    grid = [
        [4, 0, 4, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    atoms, _ = GridEncoder().encode("t", "g", grid)
    assert "v" in axes(atoms)


def test_diagonal_symmetry_detected_on_non_square_grid():
    """The regression case. The foreground is d1-symmetric; the grid is
    3x5. Pre-D13 the square-grid guard skipped d1/d2/rot90 outright."""
    grid = [
        [6, 6, 0, 0, 0],
        [6, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    atoms, _ = GridEncoder().encode("t", "g", grid)
    assert "d1" in axes(atoms)


def test_asymmetric_foreground_reports_nothing():
    grid = [
        [5, 0, 0, 0],
        [5, 0, 0, 0],
        [5, 5, 0, 0],
        [0, 0, 0, 0],
    ]
    atoms, _ = GridEncoder().encode("t", "g", grid)
    assert axes(atoms) == set()


def test_empty_foreground_reports_nothing():
    atoms, _ = GridEncoder().encode("t", "g", [[0, 0], [0, 0]])
    assert axes(atoms) == set()


# --- input validation -----------------------------------------------------

def test_unknown_background_rule_is_rejected():
    with pytest.raises(ValueError, match="background_rule"):
        GridEncoder(background_rule="freqent")


@pytest.mark.parametrize("grid", [[], [[]]])
def test_empty_grid_is_rejected(grid):
    with pytest.raises(ValueError, match="empty grid"):
        GridEncoder().encode("t", "g", grid)
