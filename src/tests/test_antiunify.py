"""
test_antiunify.py

Hand-checked unit tests for metta/antiunify.metta, using small synthetic
Candidate instances (not real ARC data - see test_blend_insideoutside.py
for that). Each expected GenericSpace was worked out by hand before
running the code.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from hyperon import MeTTa  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
ANTIUNIFY_FILE = os.path.join(REPO_ROOT, "metta", "antiunify.metta")


def fresh_metta():
    m = MeTTa()
    with open(ANTIUNIFY_FILE) as f:
        m.run(f.read())
    return m


def run_one(m, expr):
    res = m.run(f"!{expr}")
    assert len(res) == 1 and len(res[0]) == 1, f"expected exactly one result for {expr}, got {res}"
    return res[0][0]


# ---------------------------------------------------------------------
# Case 1: identical candidates except color - color should generalize,
# everything else (size, shape, symmetry) stays Fixed since it agrees.
# ---------------------------------------------------------------------
def test_color_generalizes_when_it_differs():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    c2 = "(Candidate contains green red 10 2 (a) (b) (h v) (h))"
    result = str(run_one(m, f"(antiunifyPair {c1} {c2})"))

    assert "(ColorX (Generalized colX))" in result
    assert "(ColorY (Fixed red))" in result
    assert "(SizeX (Fixed 10))" in result
    assert "(SizeY (Fixed 2))" in result
    assert "(ShapeX (Fixed (a)))" in result
    assert "(ShapeY (Fixed (b)))" in result
    assert "(SymX (h v))" in result
    assert "(SymY (h))" in result


# ---------------------------------------------------------------------
# Case 2: symmetry sets partially overlap - generic space keeps only
# the intersection (the subset both instances actually share).
# ---------------------------------------------------------------------
def test_symmetry_intersection():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v d1) (h))"
    c2 = "(Candidate contains blue red 10 2 (a) (b) (h rot180) (h v))"
    result = str(run_one(m, f"(antiunifyPair {c1} {c2})"))

    assert "(SymX (h))" in result       # {h,v,d1} ∩ {h,rot180} = {h}
    assert "(SymY (h))" in result       # {h} ∩ {h,v} = {h}


# ---------------------------------------------------------------------
# Case 3: different relations should NOT anti-unify under this equation
# (same_relation_only is enforced by Stage 2 pair selection in Python,
# but the MeTTa equation itself should also simply not fire - a defense
# in depth check, not just a Python-side filter).
# ---------------------------------------------------------------------
def test_different_relations_do_not_unify():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h) (h))"
    c2 = "(Candidate sameColor blue red 10 2 (a) (b) (h) (h))"
    res = m.run(f"!(antiunifyPair {c1} {c2})")
    # no equation matches -> MeTTa returns the call unevaluated (or
    # empty), NOT a GenericSpace
    flat = str(res)
    assert "GenericSpace" not in flat


# ---------------------------------------------------------------------
# Case 4: fully identical candidates produce a degenerate (all-Fixed)
# generic space, which isDegenerate should flag.
# ---------------------------------------------------------------------
def test_identical_candidates_are_degenerate():
    m = fresh_metta()
    c = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    result = run_one(m, f"(antiunifyPair {c} {c})")
    is_degenerate = run_one(m, f"(isDegenerate {result})")
    assert str(is_degenerate) == "True"


def test_generalized_candidates_are_not_degenerate():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    c2 = "(Candidate contains green red 10 2 (a) (b) (h v) (h))"
    result = run_one(m, f"(antiunifyPair {c1} {c2})")
    is_degenerate = run_one(m, f"(isDegenerate {result})")
    assert str(is_degenerate) == "False"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
