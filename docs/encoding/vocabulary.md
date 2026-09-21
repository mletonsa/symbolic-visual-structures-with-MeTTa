# The Vocabulary: what the encoder says about a grid, and why

This is a design document that records why each predicate is
in the vocabulary, which ones are not earning their place, and what is missing.
The per-predicate reference belongs in the tutorial pages; this is the argument
behind it.

The context for the argument is that representational coverage, rather than
search depth, appears to be the dominant limit on this kind of work.
Independent analyses of DSL-based ARC solvers have found that on 229 of 400
ARC-AGI-1 evaluation tasks the primitive library produces no valid transition
from the input grid at all, a failure that is invariant to search budget.
Our own D14 measurement is the same thing at group scale: 46 of 80
InsideOutside grids carry containment structure, so 57.5% is the ceiling before
any blending runs. Adding compute moves neither number. Adding vocabulary does.

## The rule for inclusion

The research plan states it: every predicate must be used by at least one
experiment or it gets cut. Three things follow that are worth making explicit.

**A predicate must be reachable from candidate extraction.** A fact that no
candidate schema can mention is invisible to blending no matter how faithfully
the encoder computes it. This is a stricter test than "an experiment uses it",
and some of the current vocabulary fails it.

**A predicate must discriminate.** One that holds almost everywhere adds no
information to a pattern and invites the coincidental-agreement problem D11
documented, where two candidates agreeing on a near-universal value produced an
over-narrow blend that matched nothing. Frequency of occurrence is a design
input, not an afterthought.

**A predicate should mean what it is called.** Future readers apply the name,
not the implementation. Two of ours currently do not, and both are documented
below rather than renamed, which is a debt.

## The three layers

**Cells.** `cell`, `coord`, `color`, `adj`. Complete and reversible: the grid
can be rebuilt from these alone. Over 90% of atom volume on a full-size grid.
Blending does not use them.

They stay for two reasons. Object facts are derived from them, and inspection
of surprising results starts here. The exported corpus drops them, which is why
every exported grid carries an ASCII picture above its facts.

**Object properties.** `object`, `member`, `objColor`, `size`, `bbox`, `shape`,
`holes`, `symmetric`. An object is a 4-connected same-coloured component over
non-background cells, with background fixed at colour 0 (D1).

This is where blending operates, and the reason is arithmetic. Pairwise
relations are quadratic in object count, and a typical grid has ten to twenty
objects against nine hundred cells. D2 records the failure case: one ARC-AGI-1
task with 441 single-cell objects produced roughly 135,000 atoms from a single
grid, which is why `max_pairwise_objects` caps the pairwise step at 60. That
cap fires on 3.4% of ARC-AGI-1 grids and 0.1% of ConceptARC grids.

**Object relations.** `sameShape`, `sameColor`, `contains`, `alignedRow`,
`alignedCol`. These are the anchors candidate extraction is built on (D7), so
in practice this short list is the vocabulary that matters.

**Grid level.** `gridSymmetric`, plus `tooManyObjects` as a bookkeeping flag.

## Note about predicate names

**`contains` is bounding-box enclosure, not cell containment.** An object whose
bbox encloses another's contains it, even if their cells never nest. D13 fixed
the direction bug that made this scan-order dependent, and the strictness
clause means identical bboxes emit nothing, which never occurs in practice.

**`gridSymmetric` is not about the grid.** It normalises the foreground to its
own bounding box, so it reports whether the non-background cells form a
symmetric shape in isolation, with position quotiented out. A symmetric shape
parked off-centre still fires. It is also colour-blind. D13 measured the gap
against the grid-frame reading: 29.1% of atoms across the three corpora are
position-insensitive matches that grid-frame would reject, rising to 36.9% on
ConceptARC.

**`alignedRow` means shared bbox edge**, either top or bottom, so a single cell
at the top-left aligns with a large block spanning several rows.

**`holes` counts against the object's own cells only**, so a hole occupied by a
nested object still counts. Defensible for InsideOutside and worth stating.

## Some design decisions

The inclusion rule applies to what is already here. Two candidates:

`gridSymmetric` does not appear in `enumerate.py` at all, so it is unreachable
from the Sprint B candidate schema and contributes nothing to any experiment
run so far. It also fires on 3,396 of 6,604 grids, slightly over half, which is
a high base rate for something anti-unification would treat as invariant. Both
facts point the same way: it is either for the transformational experiment or
it is cut.

`holes` and `member` should be checked the same way. A grep of `enumerate.py`
and `scoring.py` for each predicate is a ten-minute exercise and would settle
which of the current vocabulary is load-bearing and which is decoration.

## What is missing

Ordered by how much of ConceptARC they unlock relative to cost.

**1. Directional ordering.** There is no way to say one object is above,
below, left of, or right of another. D7 records this concretely: InsideOutside
was chosen over AboveBelow and Center precisely because `contains` already
existed while those groups need predicates the vocabulary does not have. Two
ConceptARC groups are named in our own notes as blocked on this, and the
top/bottom groups are plausibly blocked too.

This is cheap. Bounding-box comparison gives it, exactly like `alignedRow`,
at no additional asymptotic cost since the pairwise loop already runs.

**2. Transitive reach.** `adj` says cells touch. Nothing says one cell is
somewhere to the left of another at any distance. The 1D worked examples make
the case: filling the gap between two marks is not expressible by any
neighbourhood relation, however wide, because the gap can be as long as the
row. The same shape covers extending to a boundary, gravity, and ray-casting,
which is a real ARC family.

Cost is the concern. Transitive closure is quadratic in cells, not objects, so
on a 30x30 grid it is the same class of blowup D2 already had to cap. Object
level is affordable; cell level needs a decision.

**3. Grid size.** No predicate records grid dimensions. A 5x5 grid and a 7x9
grid containing the same shape at the same position produce byte-identical
object-level atoms. Nothing in the current experiments needs this, since we ask
what structure a grid has rather than rebuilding one. Anything producing an
output grid needs it first, and ARC outputs frequently differ in size from
their inputs. One atom per grid, effectively free.

Note the tension with the pattern-frame decision: `gridSymmetric` deliberately
discards position and size while `gridSize` records size. They answer different
questions, and the vocabulary should say so rather than look inconsistent.

**4. Centre and counting.** D7 names a near-centre predicate as the other
blocker for the Center group. Counting predicates (how many objects, how many
of a colour) are an obvious family we have nothing for. Both are speculative
until the coverage matrix below says otherwise.

## Deciding empirically rather than by intuition

The above is reasoning from four groups we happen to have looked at. The honest
way to prioritise is to measure, and the tool exists.

Running `check_group_relation_coverage.py` for each ConceptARC group against
each of the five anchor relations produces a coverage matrix: which groups have
structure the current vocabulary can express, and which come back empty. It is
16 groups by 5 relations, it uses the encoder directly, and it takes minutes.

Two things would come out of it. Groups with good coverage on some relation are
candidates for extending the experimental suite beyond InsideOutside and
SameDifferent, which currently carry every result we have. Groups that come
back empty across all five relations are the empirical version of the argument
above, and they say which predicate to add first with evidence rather than
intuition.

The input/output split matters here too. D14 found 85% of InsideOutside input
grids carry containment against 30% of outputs, which explains an asymmetry
visible in every sweep. Whether that holds across groups is worth knowing
before it goes in the manuscript as a general property of the benchmark.

Return to [Contents](../index.md)
