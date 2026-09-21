"""
novelty.py

Interim, pre-library novelty assessment for blends. This is the novelty
half of the RFP Must Have "Development of algorithms to create novel
concepts based on existing data, evaluated for their novelty and
coherence" - coherence is blend_pipeline.check_coherence; this module
was the missing half.

SCOPE, READ BEFORE USE. The research plan's Stage 5 novelty score is
defined against a concept LIBRARY: "graded by approximate graph edit
distance to the nearest library concept." No library exists yet - the
iterated library-learning loop (extract, score, accept, re-encode,
repeat) is Milestone 3 work. With no library to compare against, the
only pre-existing "known concepts" available at this stage are:

  (a) the base vocabulary's own primitive relations - the encoder's
      anchor relations themselves, already defined in
      representation.metta, which a maximally-generalized blend simply
      restates without adding anything;
  (b) the two parent candidates the blend was built from, which is
      literally what the plan's phrase "or either parent" asks for.

When Milestone 3's library exists, extend assess_novelty to also
compare against accepted library concepts via graph edit distance, per
the plan. Until then, this module answers a narrower, honestly-scoped
question: is this blend anything more than a restatement of what was
already known before it was built?

WHY THIS CAN BE EXACT RATHER THAN APPROXIMATE. The plan calls for
"approximate graph edit distance ... networkx approximation is
sufficient at these sizes." Every candidate and every blend in the
current pipeline shares one fixed 7-atom schema (the anchor relation
plus 6 scalar property slots - see enumerate.py and
docs/decisions.md D7). Graph edit distance between two patterns of
identical, fixed shape reduces to counting which of the aligned slots
differ: an exact comparison over a 6-slot vector, not an approximation.
If the schema is ever generalized past D7's scoping (variable-length
relation chains, more than 2 objects), this reduction no longer holds
and real graph edit distance would be needed instead.

CROSS-CHECKED AGAINST REAL METTA OUTPUT, NOT JUST DESIGNED ON PAPER.
This module recomputes, in Python, the same Fixed/Generalized slot
decisions and the same symmetry-set intersection that
antiunify.metta's genOrDrop performs on the MeTTa side. That
duplication is a real risk - D7 documents more than one case where
MeTTa and a Python assumption about it quietly disagreed. So
test_novelty.py includes a golden-value test using the exact
GenericSpace docs/implementation/pipeline4.md quotes from a real run
of trace_pipeline.py against real ConceptARC data, not only synthetic
hand-built cases. Passing that test is evidence this module agrees
with MeTTa on at least one real case; it is not proof of agreement in
general. Treat this as a fast Python-side reporting and pre-filter
layer, not as replacing antiunify.metta as the authority on what a
blend contains, and re-derive the golden case whenever
antiunify.metta's symmetry handling changes.

WHY "SUBSUMED BY EITHER PARENT" REDUCES TO ONE CHECK HERE. The blend
is, by construction, always at least as general as needed to cover
both c1 and c2 (that is what anti-unification does), so it always
trivially matches both parents as ground instances - that is normal,
not a novelty failure. The blend can equal a specific parent's own
concept only if c1 and c2 agreed on literally everything, since
otherwise anti-unification would have generalized the disagreement.
So "identical to a parent" and "c1 and c2 are identical to each other"
are the same event given this mechanism, which is also what
blend.metta's isDegenerate flags. parent_echo below is designed to
match isDegenerate's verdict; the two should always agree, which is
worth asserting directly once a MeTTa-capable environment is
available (see the note in test_novelty.py). This was verified
against real output at scale: python/survey_novelty.py found
parent_echo agreeing with isDegenerate on all 8,794 valid same-relation
cross-task pairs checked for InsideOutside/contains (decisions.md D16).

SIZE-1 DISCOUNTING (added after D17). A qualitative human rating of 24
sampled blends found that 3 of 16 automated-`novel` verdicts were
judged, immediately and consistently, to restate nothing beyond a
structural artifact rather than a real invariant. In every one of the
three, the surviving content was a single-cell object's size, shape
signature, or six-axis symmetry claim - and every single-cell object
has size 1, the identical canonical shape signature (one point at its
own normalized origin), and is trivially symmetric under all six axes,
regardless of task or colour (D5, D11). The original trivial/novel
split treated any non-empty fixed-slot set or shared-symmetry set as
sufficient for `novel`; it did not check whether that surviving
content was itself fully explained by one contributing instance being
a lone cell.

`assess_novelty` now discounts, for the verdict decision only, exactly
two patterns: a fixed sizeR/shapeR pair where the fixed size is 1, and
a shared all-six-axis symmetry claim on a role where at least one
source candidate's object of that size is 1. Nothing else is
discounted - a colour coincidence, a partial (non-full) symmetry set,
or a fixed size other than 1 all still count as real content, since a
partial symmetry set cannot arise from intersecting with a size-1
object's trivially-full set (only a full-set result can be explained
that way) and a colour match is genuine one-in-ten luck rather than a
structural guarantee. This narrow scoping matches what the human
ratings actually supported: colour-coincidence blends stayed rated
"novel" throughout, and a blend with a size-1 trap on one role but real
content on the other (card 022: the trap on Y, a genuine partial
symmetry on X) was correctly rated "novel", not "trivial" - the fix
must not swallow that case, and the tests in test_novelty.py check it
directly. The raw `fixed_slots`, `shared_sym_x` and `shared_sym_y`
fields are NOT altered by this discount and still report the exact
MeTTa-matching intersection; only the verdict computation uses the
discounted view, via the new `size1_discounted_roles` field, which
records which role(s) had content discounted and why.

This changes D16's reported distribution (some pairs classified
`trivial` for the first time) and that survey has not yet been
re-run against this version - see decisions.md D17's open action items.
"""

from __future__ import annotations

from dataclasses import dataclass

from enumerate import Candidate, SCALAR_SLOTS, fixed_slot_names  # noqa: E402

ALL_AXES = frozenset({"h", "v", "d1", "d2", "rot90", "rot180"})


@dataclass(frozen=True)
class NoveltyResult:
    fixed_slots: frozenset       # subset of SCALAR_SLOTS that stayed ground
    n_fixed: int                 # len(fixed_slots), 0-6
    shared_sym_x: frozenset      # symmetry axes both candidates' X share
    shared_sym_y: frozenset      # symmetry axes both candidates' Y share
    size1_discounted_roles: frozenset  # subset of {"X","Y"}: which role(s)
                                        # had content excluded from the
                                        # verdict decision because a
                                        # contributing instance was a
                                        # single cell (see module docstring,
                                        # "SIZE-1 DISCOUNTING"). fixed_slots
                                        # and shared_sym_x/y above are NOT
                                        # altered by this - they always
                                        # report the raw MeTTa-matching
                                        # intersection.
    verdict: str                 # "parent_echo" | "trivial" | "novel"

    @property
    def n_generalized(self) -> int:
        return len(SCALAR_SLOTS) - self.n_fixed

    def describe(self) -> str:
        """One line, meant to be read by a person, not just a score.
        The RFP's Must Have for a qualitative evaluation framework asks
        for human assessment of novelty; this exists so a human has
        something legible to assess rather than a bare number."""
        if self.verdict == "parent_echo":
            return ("restates a parent exactly: the two source "
                    "instances agreed on every property, so nothing "
                    "was generalized")
        if self.verdict == "trivial":
            if self.size1_discounted_roles:
                roles = ", ".join(sorted(self.size1_discounted_roles))
                return (f"restates the bare anchor relation: the only "
                        f"surviving content ({roles}-side) is fully "
                        f"explained by a single-cell object in one of "
                        f"the two source instances, which is trivially "
                        f"true regardless of task or colour, so nothing "
                        f"real survives")
            return ("restates the bare anchor relation: every scalar "
                    "slot generalized and no symmetry constraint "
                    "survived, so the blend adds nothing beyond a "
                    "relation already in the vocabulary")
        bits = []
        if self.n_fixed:
            bits.append(f"{self.n_fixed} ground propert"
                        f"{'y' if self.n_fixed == 1 else 'ies'} "
                        f"({', '.join(sorted(self.fixed_slots))})")
        if self.shared_sym_x:
            note = " (all six axes - check this isn't just a small, " \
                   "trivially symmetric shape)" if self.shared_sym_x == ALL_AXES else ""
            bits.append(f"X-side symmetry {sorted(self.shared_sym_x)}{note}")
        if self.shared_sym_y:
            note = " (all six axes - check this isn't just a small, " \
                   "trivially symmetric shape)" if self.shared_sym_y == ALL_AXES else ""
            bits.append(f"Y-side symmetry {sorted(self.shared_sym_y)}{note}")
        content = "; ".join(bits) if bits else "no surviving content"
        discount_note = ""
        if self.size1_discounted_roles:
            roles = ", ".join(sorted(self.size1_discounted_roles))
            discount_note = (f" (note: {roles}-side content was partly "
                            f"discounted as single-cell-explained but "
                            f"real content survives elsewhere)")
        return f"novel: carries {content} beyond the bare relation{discount_note}"


def assess_novelty(c1: Candidate, c2: Candidate) -> NoveltyResult:
    """Classifies a blend of c1 and c2 into exactly one of three cases.

    parent_echo - c1 and c2 agree on every scalar slot AND on every
    symmetry axis. The blend is identical to both parents; nothing was
    generalized. Should always agree with blend.metta's isDegenerate
    (verified over 8,794 real pairs - decisions.md D16).

    trivial - after discounting content fully explained by a single
    cell in either source instance (see module docstring, "SIZE-1
    DISCOUNTING"), nothing real survives beyond the bare anchor
    relation.

    novel - anything in between: at least one ground property or one
    shared symmetry axis survives the discount. Reported with its full
    profile rather than collapsed to a single score. describe() still
    flags a surviving all-six symmetry set even when it wasn't size-1
    discounted (e.g. two genuinely large objects both happening to be
    fully symmetric is rare but real - see cards 009/010/011 in D17,
    all correctly rated novel by a human reader), since "all six axes"
    is worth a second look even when it isn't the size-1 artifact.
    """
    fixed = fixed_slot_names(c1, c2)
    shared_sym_x = c1.sym_x & c2.sym_x
    shared_sym_y = c1.sym_y & c2.sym_y

    # Size-1 discount: a fixed sizeR/shapeR pair is fully explained by
    # both instances' role R being a lone cell iff the (equal) fixed
    # size is 1 - every size-1 object shares the identical canonical
    # shape signature, so shapeR is necessarily fixed too whenever
    # sizeR is fixed at 1. A shared all-six symmetry set is similarly
    # discounted only when at least one CONTRIBUTING instance's role R
    # has size 1, since that alone guarantees full symmetry regardless
    # of the other instance. A shared symmetry set that is a PROPER
    # SUBSET of all six axes is never discounted: intersecting with a
    # size-1 object's (always-full) symmetry set cannot shrink the
    # result, so a subset result can only come from the other,
    # non-size-1 instance's genuine, restrictive symmetry.
    discounted_roles = set()
    eff_fixed = set(fixed)
    if "sizeX" in fixed and c1.size_x == 1:
        eff_fixed -= {"sizeX", "shapeX"}
        discounted_roles.add("X")
    if "sizeY" in fixed and c1.size_y == 1:
        eff_fixed -= {"sizeY", "shapeY"}
        discounted_roles.add("Y")
    eff_sym_x = shared_sym_x
    if shared_sym_x == ALL_AXES and (c1.size_x == 1 or c2.size_x == 1):
        eff_sym_x = frozenset()
        discounted_roles.add("X")
    eff_sym_y = shared_sym_y
    if shared_sym_y == ALL_AXES and (c1.size_y == 1 or c2.size_y == 1):
        eff_sym_y = frozenset()
        discounted_roles.add("Y")

    if (len(fixed) == len(SCALAR_SLOTS)
            and shared_sym_x == c1.sym_x == c2.sym_x
            and shared_sym_y == c1.sym_y == c2.sym_y):
        verdict = "parent_echo"
    elif not eff_fixed and not eff_sym_x and not eff_sym_y:
        verdict = "trivial"
    else:
        verdict = "novel"

    return NoveltyResult(
        fixed_slots=fixed,
        n_fixed=len(fixed),
        shared_sym_x=shared_sym_x,
        shared_sym_y=shared_sym_y,
        size1_discounted_roles=frozenset(discounted_roles),
        verdict=verdict,
    )
