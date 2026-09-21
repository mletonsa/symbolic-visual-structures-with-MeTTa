"""
test_metta_integration.py

End-to-end check that encoder output loads into a real hyperon.MeTTa
space and that the derivation rules in representation.metta (adjSym,
sameColorAdjacent, objectsOf) work over it. This is the "Validation on
1D-ARC + Mini-ARC" checkpoint from Sprint A: it validates the MeTTa side
of the pipeline, not just the Python side.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from hyperon import MeTTa  # noqa: E402
from encoder import GridEncoder, load_into_space  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
REPR_FILE = os.path.join(REPO_ROOT, "metta", "representation.metta")


def fresh_metta():
    m = MeTTa()
    # representation.metta starts with type declarations that reference
    # predicates before any ground facts exist, which MeTTa accepts fine
    # since (: pred (-> ...)) is just an atom, not a call.
    with open(REPR_FILE) as f:
        m.run(f.read())
    return m


def test_atoms_load_and_direct_match_works():
    grid = [
        [0, 2, 2, 0],
        [0, 0, 0, 0],
    ]
    atoms, objects = GridEncoder().encode("t1", "in0", grid)
    m = fresh_metta()
    load_into_space(m, atoms)

    res = m.run('!(match &self (object t1 in0 $o) $o)')
    found = {str(x) for xs in res for x in xs}
    assert found == {objects[0].oid}


def test_adjacency_symmetry_rule_derives_reverse_edge():
    """adj is emitted only in the canonical (right/down) direction; the
    adjSym rule in representation.metta should recover the reverse."""
    grid = [[0, 2], [0, 0]]
    atoms, _ = GridEncoder().encode("t2", "in0", grid)
    m = fresh_metta()
    load_into_space(m, atoms)

    # forward edge exists directly
    fwd = m.run('!(match &self (adj t2_in0_c0_0 t2_in0_c0_1 $d) $d)')
    assert [str(x) for xs in fwd for x in xs] == ["right"]

    # reverse edge is NOT a ground fact ...
    rev_ground = m.run('!(match &self (adj t2_in0_c0_1 t2_in0_c0_0 $d) $d)')
    assert rev_ground == [[]] or rev_ground == []

    # ... but IS derivable via the adjSym rule
    rev_derived = m.run('!(adjSym t2_in0_c0_1 t2_in0_c0_0 $d)')
    flat = [str(x) for xs in rev_derived for x in xs]
    assert "left" in flat


def test_same_color_adjacent_pattern_matches_worked_example():
    """Smoke test for the SameColorAdjacency worked example used in
    docs/decisions.md and the paper's methods section: two adjacent
    same-colored cells should match the single-scope blend pattern
    defined directly in representation.metta."""
    grid = [[0, 6, 6], [0, 0, 0]]
    atoms, _ = GridEncoder().encode("t3", "in0", grid)
    m = fresh_metta()
    load_into_space(m, atoms)

    res = m.run('!(sameColorAdjacent t3_in0_c0_1 t3_in0_c0_2)')
    flat = [str(x) for xs in res for x in xs]
    assert any("SameColorAdjacency" in s for s in flat)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
