[Contents](../index.md) · Previous: [Coverage of the relational vocabulary](analysis2.md) · Next: [Novelty and human evaluation](analysis4.md)

# Analysis, 3: Diversity-based pair selection

## 3.1 Method

Each sweep reported in this section follows a leave-one-out design over a
set of usable tasks, tasks carrying the anchor relation in at least one
grid. One task is held out. From the remaining tasks, every task pair
contributes one candidate pair, selected from the two tasks' candidate
pools by one of two strategies. The resulting blend is checked for
coherence against every grid of the held-out task. This is repeated with
each usable task held out in turn. The mechanism is described in full in
[How the pipeline works](../implementation/pipeline1.md) and
[Running the experiments](../implementation/experiments1.md).

Two pair selection strategies are compared. The baseline strategy takes the
first candidate extracted from each of the two tasks' pools, with no
further selection. The diverse-pair strategy, introduced in decisions.md
D11, selects the pair minimizing the number of scalar property slots on
which the two candidates coincidentally agree, computed without invoking
MeTTa. D11 found this count predicts held-out match rate closely in a
small controlled comparison. This section reports the result of applying
both strategies at full sweep scale across three distinct groups and
relations.

## 3.2 Results across three groups and relations

Table 5 reports the outcome for all three group and relation combinations
tested to date. Ceiling is the ceiling established in Section 2.1,
computed from the same held-out task set as the sweep. Where the ceiling
was not computed for a given sweep, the cell is marked accordingly rather
than left implying a value of 100%.

**Table 5.** Diversity-based pair selection results across three groups and relations.

| Group / Relation | Baseline | Diverse-pair | Ceiling | Gain | Baseline as % of ceiling |
|---|---|---|---|---|---|
| InsideOutside / `contains` | 31% (377/1200) | 54% (654/1200) | 57.5% (690/1200) | +23 pts | 54.6% |
| SameDifferent / `sameShape` | 52% (187/360) | 77% (276/360) | not computed | +25 pts | not computed |
| Copy / `sameColor` | 63.8% (199/312) | 84.6% (264/312) | 84.6% (264/312) | +20.8 pts | 75.4% |

Sources: InsideOutside, decisions.md D9, D11, D14. SameDifferent, D10, D12.
Copy, D18. All three sweeps reported zero degenerate blends, pairs whose
two source candidates agreed on every property with nothing generalized.

The InsideOutside sweep was re-run against the corrected encoder described
in decisions.md D13 and returned counts identical to those reported in D11
and D14. The figures in Table 5 reflect the current implementation.

## 3.3 The point-gain from diversity selection is consistent across relations

The absolute gain in match rate from baseline to diverse-pair selection
falls within a five-point band across all three tests: 23 points for
`contains`, 25 points for `sameShape`, 20.8 points for `sameColor`. This
consistency was not established by the first result alone. D11 validated
the mechanism on one relation. D12 confirmed it on a second, structurally
different relation. This section reports a third confirmation on a third
relation, drawn from a different concept group and using a different
anchor relation from the first two.

The quantity that is not consistent across the three tests is how much of
the gap to ceiling the baseline strategy leaves for diverse selection to
close. InsideOutside's baseline reaches 54.6% of ceiling. Copy's baseline
reaches 75.4% of ceiling. Decisions.md D11 attributes
InsideOutside's low baseline performance to a specific structural property
of the `contains` relation as encoded. Every single-cell object shares an
identical shape signature and is symmetric under all six axes, a
consequence of there being exactly one way to represent one cell,
independent of task or colour. A first-candidate pairing is exposed to
this coincidence whenever either candidate's contained object happens to
be a single cell, and the resulting blend over-narrows on a property that
carries no information. `sameColor` has no equivalent structural
guarantee. Two arbitrary objects can share a colour, but this agreement
is not structurally forced the way the single-cell shape signature is.
The baseline strategy for `sameColor` is therefore exposed to ordinary
variance rather than the same systematic trap, which accounts for its
higher starting point relative to ceiling.

## 3.4 Diverse-pair selection reaches ceiling exactly for Copy / `sameColor`

The diverse-pair result for Copy, 126 of 156 input checks matched and 138
of 156 output checks matched, equals the ceiling for the same five-task
sample exactly rather than approximately. The ceiling is `6 x` the number
of held-out grids carrying `sameColor` structure at all, six being the
number of candidate pairs checked against each held-out task. 21 of 26
input grids and 23 of 26 output grids in this sample carry the relation,
giving `6 x 21 = 126` and `6 x 23 = 138`, both of which the diverse-pair
sweep reached without exception.

This follows from the relation's own structure rather than from a
difference in how well the pipeline performs on the two relations. A
maximally general `sameColor` blend places no constraint beyond the
relation itself, and matches any grid containing any pair of
same-coloured objects. Diverse selection converges on this maximally
general blend for the same reason D11 established for `contains`,
favouring the pair with the fewest coincidentally agreeing properties.

An exact match to ceiling is not evidence that the blend captures
anything beyond the bare `sameColor` relation. It is the clearest
instance in this document of the mechanism addressed directly in Section
3.6, that the selection strategy reliably recovers a primitive already
present in the vocabulary. A perfect match rate here demonstrates that
recovery with unusual precision. It does not demonstrate a discovery
beyond it.

## 3.5 Input and output coverage reverse for Copy relative to InsideOutside

Every sweep prior to Copy showed higher match rates on input grids than
output grids. InsideOutside: 81% against 28%. SameDifferent: 97% against
57%. Copy reverses this, with output checks matching at a higher rate than
input checks, 88.5% against 80.8% in the diverse-pair result.

Decisions.md D14 established, for InsideOutside, that this asymmetry is
present in the raw encoder output before any blending, not an artifact of
the blending mechanism. The same check applied to Copy confirms the same
property in the reversed direction. Raw `sameColor` coverage across all
ten Copy tasks is 69.8% on input grids and 94.3% on output grids, a
24.5-point gap in the same direction as the blend-level result.

A plausible account for the direction of the reversal is that
InsideOutside's transformations typically remove structure, retaining only
an inner or outer object and discarding the containment relation, while
Copy's transformations plausibly duplicate an object, which creates or
preserves a same-colour pair rather than removing one. This account is
consistent with the two groups' names and with the coverage data reported
above. It has not been verified against the per-task transformation
pattern the way D14 verified InsideOutside's asymmetry by classifying each
of its seven usable tasks individually. That classification is reported as
an open item in Section 5.

## 3.6 Interpretation: near-ceiling performance and primitive recovery

For these two relations, the highest match rates are obtained when the
blend reduces to the bare anchor relation, with the remaining property
slots generalized to unconstrained variables. D11 established this
pattern for `contains`. The diverse-pair selection strategy consistently
favours exactly this outcome, since a maximally general blend is
definitionally the pair with the fewest coincidentally agreeing scalar
slots.

This bears on how the match-rate results in this section should be read.
A blend that recovers the bare anchor relation will match any grid
carrying that relation, by construction, and will score well on any metric
built from match count. High match rate in this section therefore
demonstrates that the selection mechanism reliably recovers a primitive
already present in the encoder's vocabulary. It does not, on its own,
demonstrate that blending discovers relational structure beyond what the
vocabulary already provides. This is the distinction the novelty scoring
mechanism reported in Section 4 is designed to address, and decisions.md
D16 reports a directly relevant finding: `n_fixed`, the count of scalar
slots a blend retains as ground values, is both the majority outcome
across the full space of possible pairs and the property D11 identified as
predicting worse held-out generalization. A high match rate and a genuinely
novel concept are not the same claim, and the results in this section
support the first without, by themselves, supporting the second.

Next: [Novelty and human evaluation](analysis4.md)
