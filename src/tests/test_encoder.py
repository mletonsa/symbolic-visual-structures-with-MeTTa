"""
test_encoder.py

Validates encoder.py against small, hand-checked fixture grids (E0 in the
research plan: "does the representation faithfully and inspectably encode
grids?"). Each fixture's expected object count, sizes, adjacency, and
symmetry facts were worked out by hand before running the code, not
derived from the code's own output.

Background color for every fixture below is 0 (black), the ARC default.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from encoder import GridEncoder, Atom  # noqa: E402


def atom_set(atoms):
    return {a.to_metta() for a in atoms}


# ---------------------------------------------------------------------
# Fixture 1: a single 1x2 horizontal red line.
#   0 2 2 0
#   0 0 0 0
# Expect: exactly one object, size 2, one adjacency edge between its
# two cells (direction "right"), shape symmetric under h and v (a 1xN
# strip is trivially symmetric across the axis parallel to its long side).
# ---------------------------------------------------------------------
def test_single_line_object():
    grid = [
        [0, 2, 2, 0],
        [0, 0, 0, 0],
    ]
    atoms, objects = GridEncoder().encode("t1", "in0", grid)

    assert len(objects) == 1
    obj = objects[0]
    assert obj.size == 2
    assert obj.color == 2
    assert obj.bbox == ((0, 1), (0, 2))
    assert obj.shape_signature == ((0, 0), (0, 1))
    assert obj.holes() == 0

    s = atom_set(atoms)
    assert Atom("adj", ("t1_in0_c0_1", "t1_in0_c0_2", "right")).to_metta() in s
    assert Atom("symmetric", (obj.oid, "h")).to_metta() in s
    assert Atom("symmetric", (obj.oid, "v")).to_metta() in s


# ---------------------------------------------------------------------
# Fixture 2: a solid 2x2 blue square.
#   1 1
#   1 1
# Expect: one object, size 4, symmetric under every axis tested
# (h, v, d1, d2, rot90, rot180), zero holes.
# ---------------------------------------------------------------------
def test_solid_square_full_symmetry():
    grid = [
        [1, 1],
        [1, 1],
    ]
    atoms, objects = GridEncoder().encode("t2", "in0", grid)

    assert len(objects) == 1
    obj = objects[0]
    assert obj.size == 4
    assert obj.holes() == 0

    s = atom_set(atoms)
    for axis in ("h", "v", "d1", "d2", "rot90", "rot180"):
        assert Atom("symmetric", (obj.oid, axis)).to_metta() in s, axis


# ---------------------------------------------------------------------
# Fixture 3: an L-tromino.
#   3 0
#   3 3
# Offsets: (0,0), (1,0), (1,1). Checked by hand (not just against the
# code): reflecting across the anti-diagonal (d2: (r,c) -> (-c,-r),
# then renormalize) maps (0,0)->(1,1), (1,0)->(1,0), (1,1)->(0,0), i.e.
# the same offset set - so this particular orientation of the L-tromino
# IS symmetric under d2, and asymmetric under h, v, d1, rot90, rot180.
# This fixture is a good regression check precisely because the answer
# is "one axis, not zero, not all" - it would not catch a transform
# function with its sign flipped, but it does catch the far more common
# bug of always returning "no symmetry" or applying the wrong axis list.
# ---------------------------------------------------------------------
def test_l_tromino_single_diagonal_symmetry():
    grid = [
        [3, 0],
        [3, 3],
    ]
    atoms, objects = GridEncoder().encode("t3", "in0", grid)

    assert len(objects) == 1
    obj = objects[0]
    assert obj.size == 3
    assert obj.shape_signature == ((0, 0), (1, 0), (1, 1))

    s = atom_set(atoms)
    assert Atom("symmetric", (obj.oid, "d2")).to_metta() in s
    for axis in ("h", "v", "d1", "rot90", "rot180"):
        assert Atom("symmetric", (obj.oid, axis)).to_metta() not in s, axis


# ---------------------------------------------------------------------
# Fixture 4: two same-colored diagonal cells that must NOT merge into one
# object (4-connectivity, no diagonal adjacency by default), plus a
# sameColor fact and the absence of alignedRow/alignedCol.
#   4 0
#   0 4
# ---------------------------------------------------------------------
def test_diagonal_cells_are_separate_objects():
    grid = [
        [4, 0],
        [0, 4],
    ]
    atoms, objects = GridEncoder().encode("t4", "in0", grid)

    assert len(objects) == 2
    o1, o2 = objects
    assert o1.size == 1 and o2.size == 1

    s = atom_set(atoms)
    same_color = (Atom("sameColor", (o1.oid, o2.oid)).to_metta() in s
                  or Atom("sameColor", (o2.oid, o1.oid)).to_metta() in s)
    assert same_color

    aligned_row = (Atom("alignedRow", (o1.oid, o2.oid)).to_metta() in s
                   or Atom("alignedRow", (o2.oid, o1.oid)).to_metta() in s)
    aligned_col = (Atom("alignedCol", (o1.oid, o2.oid)).to_metta() in s
                   or Atom("alignedCol", (o2.oid, o1.oid)).to_metta() in s)
    assert not aligned_row
    assert not aligned_col


# ---------------------------------------------------------------------
# Fixture 5: a hollow 3x3 ring (one enclosed background hole).
#   5 5 5
#   5 0 5
#   5 5 5
# Expect: one object, size 8, holes() == 1.
# ---------------------------------------------------------------------
def test_hollow_rectangle_has_one_hole():
    grid = [
        [5, 5, 5],
        [5, 0, 5],
        [5, 5, 5],
    ]
    atoms, objects = GridEncoder().encode("t5", "in0", grid)

    assert len(objects) == 1
    obj = objects[0]
    assert obj.size == 8
    assert obj.holes() == 1

    s = atom_set(atoms)
    assert Atom("holes", (obj.oid, 1)).to_metta() in s


# ---------------------------------------------------------------------
# Fixture 6: containment. A big object whose bbox contains a smaller
# object's bbox (two separate colors, one nested inside the other's
# bounding box but not touching it, so they remain separate objects).
#   6 6 6 6
#   6 0 7 6
#   6 0 0 6
#   6 6 6 6
# The 7 is a single-cell object inside the ring formed by the 6s. Its
# bbox is contained in the 6-object's bbox.
# ---------------------------------------------------------------------
def test_bbox_containment():
    grid = [
        [6, 6, 6, 6],
        [6, 0, 7, 6],
        [6, 0, 0, 6],
        [6, 6, 6, 6],
    ]
    atoms, objects = GridEncoder().encode("t6", "in0", grid)

    ring = next(o for o in objects if o.color == 6)
    dot = next(o for o in objects if o.color == 7)
    assert dot.size == 1

    s = atom_set(atoms)
    assert Atom("contains", (ring.oid, dot.oid)).to_metta() in s


# ---------------------------------------------------------------------
# Fixture 7: pairwise-relation cap. A grid with more single-cell objects
# than max_pairwise_objects should skip the O(n^2) relation set and emit
# tooManyObjects instead, rather than silently producing a huge atom
# list. Regression test for the blowup found on ARC-AGI task 0dfd9992
# during Sprint A validation (441 objects -> ~135,000 atoms uncapped).
# ---------------------------------------------------------------------
def test_pairwise_relation_cap():
    # 10 isolated single-cell objects of alternating colors, no two
    # adjacent, so each is its own object.
    grid = [[0] * 20]
    for i in range(10):
        grid[0][2 * i] = (i % 9) + 1

    atoms, objects = GridEncoder(max_pairwise_objects=5).encode("t7", "in0", grid)
    assert len(objects) == 10

    s = atom_set(atoms)
    assert Atom("tooManyObjects", ("t7", "in0", 10)).to_metta() in s
    assert not any(a.predicate in ("sameColor", "sameShape", "contains",
                                   "alignedRow", "alignedCol") for a in atoms)

    # same grid, cap raised above the object count: relations computed normally
    atoms2, _ = GridEncoder(max_pairwise_objects=20).encode("t7b", "in0", grid)
    assert any(a.predicate == "sameShape" for a in atoms2)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
