"""
test_novelty.py

Pure Python, no hyperon needed for most of this file. See novelty.py's
module docstring for the scope this module operates under (interim,
pre-library novelty assessment) before reading these tests.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from enumerate import Candidate                                       # noqa: E402
from novelty import assess_novelty, ALL_AXES                          # noqa: E402


def mk(color_x="red", color_y="blue", size_x=10, size_y=2,
       shape_x=(("a",),), shape_y=(("b",),),
       sym_x=frozenset(), sym_y=frozenset()):
    return Candidate(
        relation="contains", color_x=color_x, color_y=color_y,
        size_x=size_x, size_y=size_y, shape_x=shape_x, shape_y=shape_y,
        sym_x=frozenset(sym_x), sym_y=frozenset(sym_y),
        task="t", grid="g", obj_x="ox", obj_y="oy",
    )


def test_identical_candidates_are_parent_echo():
    c = mk(sym_x={"h", "v"}, sym_y={"h"})
    r = assess_novelty(c, c)
    assert r.verdict == "parent_echo"
    assert r.n_fixed == 6
    assert "restates a parent" in r.describe()


def test_fully_disagreeing_candidates_with_no_shared_symmetry_are_trivial():
    c1 = mk(color_x="red", color_y="blue", size_x=10, size_y=2,
            shape_x=(("a",),), shape_y=(("b",),), sym_x={"h"}, sym_y={"v"})
    c2 = mk(color_x="green", color_y="yellow", size_x=99, size_y=3,
            shape_x=(("c",),), shape_y=(("d",),), sym_x={"d1"}, sym_y={"d2"})
    r = assess_novelty(c1, c2)
    assert r.verdict == "trivial"
    assert r.n_fixed == 0
    assert r.shared_sym_x == frozenset() and r.shared_sym_y == frozenset()
    assert "bare anchor relation" in r.describe()


def test_shared_symmetry_alone_prevents_trivial_verdict():
    """All six scalar slots disagree, exactly the trivial case above,
    except the two candidates happen to share one symmetry axis. That
    one shared axis is real surviving content, so the verdict must not
    be trivial even though every scalar slot generalized."""
    c1 = mk(color_x="red", color_y="blue", size_x=10, size_y=2,
            shape_x=(("a",),), shape_y=(("b",),), sym_x={"h", "v"}, sym_y=set())
    c2 = mk(color_x="green", color_y="yellow", size_x=99, size_y=3,
            shape_x=(("c",),), shape_y=(("d",),), sym_x={"h"}, sym_y=set())
    r = assess_novelty(c1, c2)
    assert r.verdict == "novel"
    assert r.n_fixed == 0
    assert r.shared_sym_x == {"h"}


def test_partial_scalar_agreement_is_novel():
    c1 = mk(color_x="red", size_x=10)
    c2 = mk(color_x="red", size_x=20)   # colorX agrees, sizeX differs
    r = assess_novelty(c1, c2)
    assert r.verdict == "novel"
    assert "colorX" in r.fixed_slots
    assert r.n_fixed == 5   # everything but sizeX agreed in this mk() default


def test_describe_flags_all_six_symmetry_as_worth_checking():
    c1 = mk(sym_x=ALL_AXES, sym_y=ALL_AXES)
    c2 = mk(color_x="green", size_x=999, sym_x=ALL_AXES, sym_y=ALL_AXES)
    r = assess_novelty(c1, c2)
    assert r.shared_sym_x == ALL_AXES
    assert "trivially symmetric" in r.describe()


# ---------------------------------------------------------------------
# Golden case: the exact pair and exact GenericSpace from a real run of
# trace_pipeline.py against real ConceptARC data, as quoted in
# docs/implementation/pipeline4.md. This is not a synthetic example;
# every value below is copied from that trace's printed output, so a
# pass here is evidence (not proof - see novelty.py's module docstring)
# that this module's symmetry-intersection logic agrees with
# antiunify.metta's genOrDrop on at least one real case.
# ---------------------------------------------------------------------
def test_matches_real_trace_generic_space():
    # Candidate A: InsideOutside1's (contains red/20 blue/1) candidate.
    # Candidate B: InsideOutside4's (contains blue/38 green/20) candidate.
    # Shapes are given as opaque distinct placeholders here since their
    # exact cell-offset content isn't the point of this test - only
    # that A's and B's shapes differ, which the trace's atoms confirm
    # (20-cell frame vs 38-cell frame, 1-cell dot vs 20-cell frame).
    a = mk(color_x="red", color_y="blue", size_x=20, size_y=1,
           shape_x=("A_outer",), shape_y=("A_inner",),
           sym_x=ALL_AXES, sym_y=ALL_AXES)
    b = mk(color_x="blue", color_y="green", size_x=38, size_y=20,
           shape_x=("B_outer",), shape_y=("B_inner",),
           sym_x={"h", "rot180", "v"}, sym_y=ALL_AXES)

    r = assess_novelty(a, b)

    # From the trace's printed GenericSpace:
    #   (ColorX (Generalized colX)) (ColorY (Generalized colY))
    #   (SizeX (Generalized szX))   (SizeY (Generalized szY))
    #   (ShapeX (Generalized shX))  (ShapeY (Generalized shY))
    #   (SymX (h rot180 v))
    #   (SymY (d1 d2 h rot180 rot90 v))
    assert r.n_fixed == 0
    assert r.fixed_slots == frozenset()
    assert r.shared_sym_x == {"h", "rot180", "v"}
    assert r.shared_sym_y == ALL_AXES

    # a.size_y == 1, so shared_sym_y (all six) is size-1-discounted for
    # the verdict decision (post-D17). shared_sym_x is a proper subset,
    # never discounted, and survives on its own - so the verdict is
    # still "novel", now for a code-verified reason rather than only a
    # narrative caveat: the real content is entirely on the X side.
    assert r.verdict == "novel"
    assert r.size1_discounted_roles == frozenset({"Y"})
    d = r.describe()
    assert "h" in d and "rot180" in d
    assert "trivially symmetric" in d   # raw Y-side field still reported...
    assert "discounted" in d            # ...but now flagged as discounted too


# ---------------------------------------------------------------------
# D17: a human rating of 24 sampled blends found 3 of 16 automated-
# "novel" verdicts were immediately read as trivial by a human, all
# three via the same mechanism - surviving content fully explained by
# a single-cell object in one source instance. These tests pin the fix
# down directly, using the same structural shapes as the real cards
# that motivated it (docs/D17_draft.md).
# ---------------------------------------------------------------------

def test_size1_only_symmetry_is_now_trivial():
    """Models card 008: the only surviving content is shared all-six
    symmetry on Y, and Y is a single cell in (at least) one source
    instance. Pre-D17 this was "novel"; post-D17 it is "trivial"."""
    c1 = mk(color_x="green", color_y="green", size_x=62, size_y=1,
            shape_x=("frame62",), shape_y=("dot",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    c2 = mk(color_x="orange", color_y="yellow", size_x=16, size_y=16,
            shape_x=("frame16",), shape_y=("odd16",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    r = assess_novelty(c1, c2)
    assert r.verdict == "trivial"
    assert r.size1_discounted_roles == frozenset({"Y"})
    assert "single-cell" in r.describe()


def test_size1_scalar_trap_is_now_trivial():
    """Models cards 016/023: shapeY and sizeY are fixed at the canonical
    single-cell values, and nothing else survives. Pre-D17 this was
    "novel" (n_fixed=2); post-D17 it is "trivial"."""
    c1 = mk(color_x="blue", color_y="yellow", size_x=20, size_y=1,
            shape_x=("frameA",), shape_y=("dot",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    c2 = mk(color_x="green", color_y="magenta", size_x=28, size_y=1,
            shape_x=("frameB",), shape_y=("dot",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    r = assess_novelty(c1, c2)
    assert r.verdict == "trivial"
    assert r.fixed_slots == {"sizeY", "shapeY"}  # raw, undiscounted
    assert r.size1_discounted_roles == frozenset({"Y"})


def test_size1_trap_does_not_swallow_real_content_on_other_role():
    """Models card 022: the same Y-side single-cell trap as above, BUT
    X carries a genuine partial symmetry claim. A human rated this
    "novel" (2/2/2), distinctly from 016/023's "trivial" (1/3/1) - the
    fix must not discount X's real content just because Y's is
    discounted. This is the test that would catch an over-eager fix."""
    c1 = mk(color_x="green", color_y="blue", size_x=28, size_y=1,
            shape_x=("frameA",), shape_y=("dot",),
            sym_x={"h", "rot180", "v"}, sym_y=ALL_AXES)
    c2 = mk(color_x="grey", color_y="yellow", size_x=52, size_y=1,
            shape_x=("frameB",), shape_y=("dot",),
            sym_x={"h", "rot180", "v"}, sym_y=ALL_AXES)
    r = assess_novelty(c1, c2)
    assert r.verdict == "novel"
    assert r.size1_discounted_roles == frozenset({"Y"})
    assert r.shared_sym_x == {"h", "rot180", "v"}   # real, survives


def test_large_object_full_symmetry_is_not_discounted():
    """Models cards 009/010/011: Y is symmetric on all six axes in both
    source instances, but Y is 16 cells in both, not a single cell.
    This is rare and genuinely restrictive, and stayed "novel" (human
    rated 2) - the fix must not discount it just because the axis set
    happens to be the full six."""
    c1 = mk(color_x="orange", color_y="yellow", size_x=16, size_y=16,
            shape_x=("frame16a",), shape_y=("odd16a",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    c2 = mk(color_x="green", color_y="red", size_x=19, size_y=16,
            shape_x=("frame19",), shape_y=("odd16b",),
            sym_x=frozenset(), sym_y=ALL_AXES)
    r = assess_novelty(c1, c2)
    assert r.verdict == "novel"
    assert r.size1_discounted_roles == frozenset()
    assert r.shared_sym_y == ALL_AXES


def test_colour_coincidence_is_never_discounted():
    """A shared colour is genuine one-in-ten luck, not a structural
    guarantee the way single-cell size/shape/symmetry is. D17's rated
    sample never dropped a colour-coincidence blend to novelty=1, and
    the fix is deliberately scoped not to touch this case."""
    c1 = mk(color_x="orange", color_y="blue", size_x=52, size_y=5,
            shape_x=("shapeA",), shape_y=("shapeC",),
            sym_x=frozenset(), sym_y=frozenset())
    c2 = mk(color_x="orange", color_y="red", size_x=29, size_y=9,
            shape_x=("shapeB",), shape_y=("shapeD",),
            sym_x=frozenset(), sym_y=frozenset())
    r = assess_novelty(c1, c2)
    assert r.verdict == "novel"
    assert r.size1_discounted_roles == frozenset()
    assert r.fixed_slots == {"colorX"}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
