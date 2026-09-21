"""
test_scoring.py

Hand-checked unit tests for scoring.py's MDL calculation.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from scoring import dl_of_atom, split_pattern_atoms, mdl_gain, _atom_arity  # noqa: E402


def test_atom_arity():
    assert _atom_arity("(contains X Y)") == 2
    assert _atom_arity("(objColor X blue)") == 2
    assert _atom_arity("(size X 10)") == 2
    assert _atom_arity("(shape X (a b))") == 2  # nested arg counts as ONE argument
    assert _atom_arity("(foo)") == 0


def test_split_pattern_atoms():
    pattern = "((contains X Y) (objColor X blue) (shape X (a b)))"
    atoms = split_pattern_atoms(pattern)
    assert atoms == ["(contains X Y)", "(objColor X blue)", "(shape X (a b))"]


def test_dl_of_atom_matches_hand_calculation():
    # arity 2 atom, vocab size 16 -> (2+1) * log2(16) = 3*4 = 12 bits
    assert dl_of_atom("(contains X Y)", 16) == 12.0


def test_mdl_gain_positive_for_frequently_matching_generalizing_blend():
    """A blend with 2 fully-generalized property slots (colors) that
    matches many held-out instances should have positive MDL gain -
    the concept pays for itself many times over."""
    pattern = "((contains X Y) (objColor X $c1) (objColor Y $c2) (size X 10) (size Y 2) (shape X (a)) (shape Y (b)))"
    result = mdl_gain(pattern, n_matches=20, symbol_vocab_size=32)
    assert result.worth_it
    assert result.dl_gain > 0


def test_mdl_gain_negative_when_a_blend_only_matches_its_own_construction():
    """A blend matching only 1 instance (i.e. not even generalizing to
    a second occurrence) should have negative gain - the one-time
    definition cost isn't paid back at all.

    NOTE on what this test does NOT claim: it would be natural to
    expect a "narrow, fully-ground, non-generalizing" pattern to score
    worse than a "broadly generalized" one at the SAME match count -
    but the plan's literally-specified MDL formula, DL(atom) =
    (arity+1)*log2|symbols|, does not actually distinguish a ground
    constant from a variable at the same argument position; arity is
    identical either way. So this formula's only lever against
    non-generalizing blends is LOW MATCH COUNT, not narrowness per se -
    see docs/decisions.md D10 for the fuller discussion and why this
    was kept faithful to the plan's stated formula rather than quietly
    "improved" to add a ground-vs-variable distinction the plan didn't
    specify. Confirmed by direct calculation: break-even for the
    pattern below is between 1 and 2 matches - n_matches=1 is negative,
    n_matches=2 is already positive, which is a genuinely low bar and
    is exactly the "MDL sensitivity on small corpora" risk the research
    plan's own risk section anticipated.
    """
    pattern = "((contains X Y) (objColor X blue) (objColor Y red) (size X 10) (size Y 2) (shape X (a)) (shape Y (b)))"
    result = mdl_gain(pattern, n_matches=1, symbol_vocab_size=32)
    assert result.dl_gain < 0


def test_more_matches_increases_gain_monotonically():
    pattern = "((contains X Y) (objColor X $c1) (objColor Y $c2) (size X $s1) (size Y $s2) (shape X (a)) (shape Y (b)))"
    r_low = mdl_gain(pattern, n_matches=3, symbol_vocab_size=32)
    r_high = mdl_gain(pattern, n_matches=30, symbol_vocab_size=32)
    assert r_high.dl_gain > r_low.dl_gain


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
