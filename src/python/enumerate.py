"""
enumerate.py

Stage 1 (candidate extraction) and Stage 2 (pair selection) of the
blending pipeline, scoped for Sprint B's validation pass: 2-object
relational candidate patterns extracted from a single ConceptARC group.

A Candidate anchors on a pair of objects (X, Y) connected by one of the
binary relations already in the encoder's vocabulary (contains,
sameColor, sameShape, alignedRow, alignedCol), plus each object's own
unary properties (color, size, shape, symmetry axes). Object identity
is discarded immediately (X/Y are roles, not specific object ids) - the
candidate already IS a pattern with two free "slots," which is what
Stage 3 (antiunify.metta) anti-unifies across instances.

This is deliberately narrower than the research plan's general Stage 1
(which enumerates arbitrary relational subgraphs up to k relation atoms
and 1-2 object variables): fixed at exactly one anchor relation and the
unary facts about its two endpoints. See docs/decisions.md D7 for why
this scoping was chosen for the Sprint B validation pass, and what
generalizing it (variable k, chains of 3+ objects) would need.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from encoder import Atom, GridEncoder  # noqa: E402


ANCHOR_RELATIONS = ("contains", "sameColor", "sameShape", "alignedRow", "alignedCol")


@dataclass(frozen=True)
class Candidate:
    relation: str
    color_x: str
    color_y: str
    size_x: int
    size_y: int
    shape_x: tuple
    shape_y: tuple
    sym_x: frozenset
    sym_y: frozenset
    # provenance, not used in matching - purely for tracing a candidate
    # back to the grid it came from when inspecting results
    task: str
    grid: str
    obj_x: str
    obj_y: str

    def to_metta(self) -> str:
        """MeTTa literal for this candidate, consumed by antiunify.metta.
        Shape signatures and symmetry sets are passed through as MeTTa
        list literals; antiunify.metta only needs to compare them for
        equality or intersect them, not interpret their internals."""
        def sym_metta(s):
            return "(" + " ".join(sorted(s)) + ")"

        def shape_metta(s):
            # s is a tuple of (row, col) offset pairs, as produced by
            # encoder.ObjectInfo.shape_signature
            return "(" + " ".join(f"(SC {r} {c})" for r, c in s) + ")"

        return (f"(Candidate {self.relation} "
                f"{self.color_x} {self.color_y} "
                f"{self.size_x} {self.size_y} "
                f"{shape_metta(self.shape_x)} {shape_metta(self.shape_y)} "
                f"{sym_metta(self.sym_x)} {sym_metta(self.sym_y)})")


def _index_facts(atoms):
    """Builds lookup dicts from an object id to its unary properties."""
    color, size, shape, sym = {}, {}, {}, {}
    for a in atoms:
        if a.predicate == "objColor":
            color[a.args[0]] = a.args[1]
        elif a.predicate == "size":
            size[a.args[0]] = a.args[1]
        elif a.predicate == "shape":
            # a.args[1] is ("Shape", tuple_of_offsets)
            shape[a.args[0]] = a.args[1][1]
        elif a.predicate == "symmetric":
            sym.setdefault(a.args[0], set()).add(a.args[1])
    return color, size, shape, sym


def extract_candidates(qualified_task_id: str, grid_label: str, atoms) -> list:
    """Stage 1: extract one Candidate per (anchor relation, object pair)
    found in a single grid's atoms. Returns a list of Candidate."""
    color, size, shape, sym = _index_facts(atoms)
    out = []
    for a in atoms:
        if a.predicate not in ANCHOR_RELATIONS:
            continue
        ox, oy = a.args[0], a.args[1]
        if ox not in color or oy not in color:
            continue  # defensive: shouldn't happen, every object has a color
        out.append(Candidate(
            relation=a.predicate,
            color_x=color[ox], color_y=color[oy],
            size_x=size.get(ox, 0), size_y=size.get(oy, 0),
            shape_x=tuple(shape.get(ox, ())), shape_y=tuple(shape.get(oy, ())),
            sym_x=frozenset(sym.get(ox, set())), sym_y=frozenset(sym.get(oy, set())),
            task=qualified_task_id, grid=grid_label, obj_x=ox, obj_y=oy,
        ))
    return out


def extract_from_task_json(task_json: dict, qualified_task_id: str,
                            encoder: GridEncoder = None) -> list:
    """Convenience wrapper: encodes every grid in a task's train+test
    pairs and extracts candidates from each. Returns a flat list."""
    encoder = encoder or GridEncoder()
    out = []
    for split in ("train", "test"):
        for i, pair in enumerate(task_json.get(split, [])):
            for gname in ("input", "output"):
                if gname not in pair:
                    continue
                grid = pair[gname]
                label = f"{split}{i}_{gname}"
                atoms, _ = encoder.encode(qualified_task_id, label, grid)
                out.extend(extract_candidates(qualified_task_id, label, atoms))
    return out


def select_pairs(candidates_a: list, candidates_b: list, same_relation_only: bool = True):
    """Stage 2: pair selection. Yields (c1, c2) pairs from two candidate
    pools (e.g. two different tasks) that share a relation and are not
    from the same task (the plan's cross-task condition). Restricting to
    same_relation_only=True is this Sprint's scope (see module docstring);
    cross-relation pairing is future work (E2-style cross-group blending).
    """
    for c1 in candidates_a:
        for c2 in candidates_b:
            if c1.task == c2.task:
                continue
            if same_relation_only and c1.relation != c2.relation:
                continue
            if not same_relation_only and c1.relation == c2.relation:
                continue  # this call already covered by a same_relation_only pass
            yield c1, c2


SCALAR_SLOTS = ("colorX", "colorY", "sizeX", "sizeY", "shapeX", "shapeY")


def fixed_slot_names(c1: Candidate, c2: Candidate) -> frozenset:
    """Which of the 6 scalar slots would stay Fixed (ground) if c1 and c2
    were anti-unified: the ones where the two candidates happen to agree.
    This is the same comparison n_coincidental_fixed_slots (below) counts;
    this version names the slots rather than just counting them, which
    novelty.py needs and a bare count doesn't provide.

    Order-independent (a frozenset), and 100% consistent with
    n_coincidental_fixed_slots by construction: that function is now
    defined as len(fixed_slot_names(c1, c2)), the same six comparisons
    as before, so its return value is unchanged for every existing
    caller and every value in test_diversity_selection.py's golden
    table."""
    out = set()
    if c1.color_x == c2.color_x:
        out.add("colorX")
    if c1.color_y == c2.color_y:
        out.add("colorY")
    if c1.size_x == c2.size_x:
        out.add("sizeX")
    if c1.size_y == c2.size_y:
        out.add("sizeY")
    if c1.shape_x == c2.shape_x:
        out.add("shapeX")
    if c1.shape_y == c2.shape_y:
        out.add("shapeY")
    return frozenset(out)


def n_coincidental_fixed_slots(c1: Candidate, c2: Candidate) -> int:
    """Cheap, Python-only (no MeTTa) proxy for how narrowly a blend of
    c1 and c2 will generalize, computed BEFORE running antiunify at all.

    Counts how many of the 6 scalar slots (color_x, color_y, size_x,
    size_y, shape_x, shape_y) happen to be EXACTLY equal between the two
    candidates - these are exactly the slots antiunify.metta's genOrDrop
    would keep as ground (Fixed) rather than generalizing to a variable.

    Found empirically (see docs/decisions.md D11) to correlate almost
    perfectly, in a small controlled comparison, with how poorly a blend
    generalizes to held-out data: 0 coincidentally-fixed slots -> 7/12
    held-out grids matched; 1 -> 3/12; 2 or 3 -> 0/12, every time. The
    mechanism is straightforward once seen: a "coincidence" like both
    source objects happening to be a single cell (size=1, which
    normalizes to the SAME shape signature `((0,0))` for literally every
    single-cell object in the vocabulary, regardless of which task or
    color) gets treated by anti-unification as a genuine invariant,
    over-narrowing the blend to require an exact match on a slot that
    was never actually meaningful - it was just common. This is the same
    "trivial conjunctions dominate early rankings" risk the research
    plan's own risk section anticipated for MDL scoring, showing up here
    in coherence matching instead.

    Use this to RANK candidate pairs before spending an expensive
    MeTTa blend+coherence check on any of them (~2-4s each) - lower
    scores are the ones actually worth checking first, since they are
    the ones most likely to generalize.
    """
    return len(fixed_slot_names(c1, c2))


def select_most_diverse_pair(candidates_a: list, candidates_b: list, same_relation_only: bool = True):
    """Among all valid pairs from the two candidate pools (see
    select_pairs), returns the one with the FEWEST coincidentally-fixed
    slots (see n_coincidental_fixed_slots) - the pair predicted to
    generalize best, found without running MeTTa at all. Returns
    (c1, c2, n_coincidental_fixed) or (None, None, None) if no valid
    pair exists."""
    best = None
    best_score = None
    for c1, c2 in select_pairs(candidates_a, candidates_b, same_relation_only):
        score = n_coincidental_fixed_slots(c1, c2)
        if best_score is None or score < best_score:
            best, best_score = (c1, c2), score
    if best is None:
        return None, None, None
    return best[0], best[1], best_score
