"""
test_blend.py

Hand-checked unit tests for metta/blend.metta, using small synthetic
Candidate instances (real ARC data is exercised separately, in
test_blend_insideoutside.py).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from hyperon import MeTTa  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def fresh_metta():
    m = MeTTa()
    for fname in ("antiunify.metta", "blend.metta"):
        with open(os.path.join(REPO_ROOT, "metta", fname)) as f:
            m.run(f.read())
    return m


def run_one(m, expr):
    res = m.run(f"!{expr}")
    assert len(res) == 1 and len(res[0]) == 1, f"expected exactly one result for {expr}, got {res}"
    return res[0][0]


# ---------------------------------------------------------------------
# Materialized pattern should contain a real variable for the
# generalized color slot, and ground constants everywhere else.
# ---------------------------------------------------------------------
def test_materialized_pattern_has_real_variable_for_generalized_slot():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    c2 = "(Candidate contains green red 10 2 (a) (b) (h v) (h))"
    generic = run_one(m, f"(antiunifyPair {c1} {c2})")
    pattern = str(run_one(m, f"(materializePattern {generic})"))

    assert "(contains X Y)" in pattern
    assert "(objColor Y red)" in pattern       # invariant, stayed ground
    assert "(size X 10)" in pattern
    assert "(size Y 2)" in pattern
    # the generalized color slot must appear as an actual $ variable
    # (MeTTa alpha-renames it internally, e.g. to "$X#57" - not
    # literally "$colX" - so check structurally, not by exact name)
    import re
    assert re.search(r"\(objColor X \$\w", pattern), pattern
    assert "Generalized" not in pattern
    assert "(var " not in pattern


def test_materialized_pattern_all_invariant_is_fully_ground():
    m = fresh_metta()
    c = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    generic = run_one(m, f"(antiunifyPair {c} {c})")
    pattern = str(run_one(m, f"(materializePattern {generic})"))
    assert "$" not in pattern  # every slot Fixed -> no variables at all


# ---------------------------------------------------------------------
# Symmetry enrichment: union of both instances' axes, deduplicated.
# ---------------------------------------------------------------------
def test_blend_symmetry_enrichment_is_deduplicated_union():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    c2 = "(Candidate contains blue red 10 2 (a) (b) (h d1) (h v))"
    enrichment = str(run_one(m, f"(blendSymmetryEnrichment {c1} {c2})"))

    # X: {h,v} ∪ {h,d1} = {h,v,d1} (order not asserted, just membership)
    assert "h" in enrichment and "v" in enrichment and "d1" in enrichment
    # dedup check: 'h' should not appear twice
    assert enrichment.count(" h ") + enrichment.count(" h)") <= 2  # X and Y each once


# ---------------------------------------------------------------------
# Full pipeline: buildBlend ties antiunify + materialize + enrichment +
# degeneracy check together in one call.
# ---------------------------------------------------------------------
def test_build_blend_end_to_end():
    m = fresh_metta()
    c1 = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    c2 = "(Candidate contains green red 10 2 (a) (b) (h v) (h))"
    blend = str(run_one(m, f"(buildBlend {c1} {c2})"))

    assert "Blend" in blend
    assert "(contains X Y)" in blend
    assert "False" in blend  # not degenerate, since color differs


def test_build_blend_flags_degenerate_case():
    m = fresh_metta()
    c = "(Candidate contains blue red 10 2 (a) (b) (h v) (h))"
    blend = str(run_one(m, f"(buildBlend {c} {c})"))
    assert blend.rstrip(")").endswith("True")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
