"""
test_1d_arc.py

1D-ARC (Xu et al. / optozorax/arc_1d) is a procedural Rust generator, not
a data dump - there is no fixed JSON corpus to download and diff against.
Rather than reproducing its generator in this project, this module
validates the encoder's 1D path directly: a handful of hand-built
single-row grids, in the style of published 1D-ARC task families
(single-object recolor, move/translate, fill-between-endpoints), encoded
with the same GridEncoder used for full 2D grids and checked for the
properties the research plan calls out 1D-ARC for: same vocabulary,
reduced geometric complexity, all relational facts still meaningful with
n_rows == 1.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from encoder import GridEncoder, Atom  # noqa: E402


def atom_set(atoms):
    return {a.to_metta() for a in atoms}


# ---------------------------------------------------------------------
# "Move": a single colored segment shifted right in the output. Single
# row, single object per grid; checks the encoder handles n_rows == 1
# without special-casing (no crashes on row-symmetry axes, sane bbox).
# ---------------------------------------------------------------------
def test_1d_single_segment_object():
    grid_in = [[0, 3, 3, 0, 0, 0, 0, 0]]
    grid_out = [[0, 0, 0, 3, 3, 0, 0, 0]]

    atoms_in, objs_in = GridEncoder().encode("move1d", "in0", grid_in)
    atoms_out, objs_out = GridEncoder().encode("move1d", "out0", grid_out)

    assert len(objs_in) == 1 and len(objs_out) == 1
    assert objs_in[0].size == 2 and objs_out[0].size == 2
    assert objs_in[0].bbox == ((0, 1), (0, 2))
    assert objs_out[0].bbox == ((0, 3), (0, 4))

    # a 1-row object is trivially symmetric under h (row-flip is a no-op
    # when there is only one row) - this is an expected degenerate case,
    # not a bug, and worth documenting since it means "symmetric h" on
    # 1D-ARC data carries no information and should be down-weighted or
    # excluded by candidate extraction (Sprint C) when working on 1D data.
    s = atom_set(atoms_in)
    assert Atom("symmetric", (objs_in[0].oid, "h")).to_metta() in s


# ---------------------------------------------------------------------
# "Recolor": same shape/position, different color between in/out -
# confirms sameShape can hold across two objects that do NOT sameColor,
# which is exactly the kind of cross-example pattern Stage 1 candidate
# extraction (enumerate.py, Sprint B) needs to find.
# ---------------------------------------------------------------------
def test_1d_recolor_same_shape_different_color():
    grid_in = [[0, 2, 2, 2, 0]]
    grid_out = [[0, 4, 4, 4, 0]]

    atoms_in, objs_in = GridEncoder().encode("recolor1d", "in0", grid_in)
    atoms_out, objs_out = GridEncoder().encode("recolor1d", "out0", grid_out)

    assert objs_in[0].shape_signature == objs_out[0].shape_signature
    assert objs_in[0].color != objs_out[0].color


# ---------------------------------------------------------------------
# "Fill between": two single-cell endpoints get the space between them
# filled in the output - two objects collapse to one, exercising object
# COUNT change across in/out, which the corpus-level candidate extraction
# needs to be robust to (not every in/out pair has matching object counts).
# ---------------------------------------------------------------------
def test_1d_fill_between_endpoints():
    grid_in = [[0, 5, 0, 0, 0, 5, 0]]
    grid_out = [[0, 5, 5, 5, 5, 5, 0]]

    _, objs_in = GridEncoder().encode("fill1d", "in0", grid_in)
    _, objs_out = GridEncoder().encode("fill1d", "out0", grid_out)

    assert len(objs_in) == 2      # two separate endpoint objects
    assert len(objs_out) == 1     # one filled segment
    assert objs_out[0].size == 5


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
