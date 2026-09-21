[Contents](../index.md) · Previous: [Diversity-based pair selection](analysis3.md) · Next: [Negative results and limitations](analysis5.md)

# Analysis, 4: Novelty and human evaluation

This section reports the results addressing the RFP's requirement for
"algorithms to create novel concepts... evaluated for their novelty and
coherence" and its requirement for "a qualitative evaluation framework...
focusing on human assessment of novelty and logical consistency." Coherence
evaluation is reported in Section 3. This section covers novelty and the
human evaluation framework.

## 4.1 Method

**Automated novelty scoring.** No concept library exists yet. The
iterated library-learning loop described in the research plan is Milestone
3 work. Without a library to compare against, novelty is assessed relative
to the two references available at this stage, the base vocabulary's own
primitive relations and the two parent candidates a blend was built from.
`python/novelty.py` classifies a blend into one of three categories.
`parent_echo` applies when the two parent candidates agree on every
property, so nothing was generalized. `trivial` applies when nothing
survives beyond the bare anchor relation. `novel` applies otherwise, with
its result reported alongside the specific properties retained. A blend
retaining a fixed scalar property, a colour or size that happened to match
between the two parents, is reported separately from a blend retaining
only a shared symmetry constraint, since decisions.md D11 found these carry
different implications for held-out generalization.

**Human evaluation.** `docs/rating/rubric.md` defines three dimensions,
each scored 1 to 3: novelty, whether the blend adds structure beyond
existing primitives, logical consistency, whether the retained properties
form one coherent claim rather than an arbitrary conjunction, and value,
whether the concept would plausibly assist in representing or solving
ARC-style tasks. 24 blends were sampled from InsideOutside/`contains`,
stratified across the three automated verdict categories, and rated
against this rubric. The automated verdict, coherence match count, and MDL
gain for each blend were withheld until rating was complete.

The rating exercise was assisted rather than fully independent. Cards were
presented with structurally relevant facts drawn from the card's own
content, such as which object in a symmetry claim was a single cell, and
in two of the 24 cases the automated match count had been discussed prior
to formal rating. This is reported as a first pass establishing the
rubric's usability and the informativeness of comparing human and
automated scores, rather than as a fully blinded study.

## 4.2 Automated novelty verdict, validated and distributed

The correspondence between `novelty.py`'s `parent_echo` verdict and
`blend.metta`'s `isDegenerate` flag was checked against every valid
same-relation cross-task pair in InsideOutside, 8,794 pairs. The two agreed
on all 8,794.

Table 6 reports the verdict distribution across the same 8,794 pairs, prior
to the correction described in Section 4.3.

**Table 6.** Novelty verdict distribution, InsideOutside/`contains`, 8,794 pairs.

| Verdict | Count | Share |
|---|---|---|
| `parent_echo` | 0 | 0.0% |
| `trivial` | 344 | 3.9% |
| `novel`, symmetry content only | 3,513 | 39.9% |
| `novel`, with a retained scalar property | 4,937 | 56.1% |

Decisions.md D11 found that retaining a scalar property, the condition
defining the fourth row of Table 6, predicts worse held-out generalization
in a controlled comparison. That condition is also the single largest
category in the full pair space. A blend that retains more content than
the bare relation is not, on this evidence, more likely to generalize. It
is more likely to be exactly the coincidental-agreement pattern D11
identified.

## 4.3 A degeneracy the automated verdict initially missed

Three of the 24 rated blends were scored automated-`novel` but rated
human novelty 1, the rubric's lowest point, indicating no content beyond
the bare relation. All three shared one property, the retained content was
a single-cell object's size, shape, or full symmetry claim, each of which
holds trivially for any single-cell object regardless of task or colour.
This affected 3 of 16 automated-`novel` blends in the sample, 18.75%.

`novelty.py` was revised to discount this specific case, a fixed size or
shape property equal to the canonical single-cell value, or a full
six-axis symmetry claim where a contributing object has size one, when
these are the only content a blend retains. Colour coincidences and
partial symmetry claims, which carry no equivalent structural guarantee,
are not discounted. The revised classifier was tested against a case
retaining both a discounted single-cell property and a genuine, undiscounted
property on the blend's other object, confirming the discount does not
extend beyond the specific pattern identified.

The revised classifier was then run against the same 8,794-pair space.
1,661 of the 8,450 pairs previously classified `novel` were reclassified
`trivial`, 19.66%. The 24-blend sample predicted 18.75%. The two figures
differ by 0.91 percentage points, obtained from a sample roughly two
orders of magnitude smaller than the population it predicted.

## 4.4 Value assessment separates two distinct failure modes

Table 7 reports held-out coherence match rate grouped by the human value
rating assigned to each blend.

**Table 7.** Coherence match rate by human value rating, 24 rated blends.

| Group | n | Pooled match rate |
|---|---|---|
| Value 1, matches most held-out grids | 9 | 48.3% (144/298) |
| Value 1, matches almost no held-out grids | 2 | 0.0% (0/66) |
| Value 2 | 13 | 34.1% (152/446) |

Low value occurs at both extremes of match rate. A blend retaining no
content beyond the bare relation matches nearly half of held-out grids,
because it constrains nothing, and is rated low value for that reason. A
blend retaining only the single-cell coincidence described in Section 4.3
matches almost no held-out grids, because the coincidence rarely recurs,
and is rated low value for the opposite reason. Two blends in the sample
illustrate the distinction directly. Both retain an identical single-cell
property on one object and match zero held-out grids. One additionally
retains a genuine partial symmetry constraint on its other object and was
rated value 2. The other retains nothing further and was rated value 1.
Match rate alone does not separate these two blends. The retained content
does.

Human consistency ratings showed no comparable relationship to MDL
acceptance. Mean consistency was 2.76 for blends with positive MDL gain
and 2.67 for blends with negative gain. MDL gain is computed from match
count and description length. Consistency, as defined in the rubric,
concerns whether a blend's retained properties form one coherent claim.
The rubric does not predict these should agree, and the results do not
show them agreeing.

No blend in the 24-blend sample was rated value 3. This may reflect the
specific sample drawn, or a property of the two-object, single-relation
candidate schema described in Section 1.1, which has limited room for the
kind of multi-relation structure a reusable building block would need.
This is not yet distinguished and is reported as an open question in
Section 5.

## 4.5 Summary against the RFP requirement

Novelty and coherence are both implemented and both evaluated
quantitatively. The novelty classifier's principal limitation, failure to
discount a specific structural coincidence, was identified through human
evaluation, corrected, and the correction verified at full scale against
independent evidence, the 19.66% reclassification rate against the
sample's 18.75% prediction. The qualitative evaluation framework required
by the RFP is implemented, applied, and shown in this instance to have
identified a genuine defect in the automated criterion it was built to
check.

Next: [Negative results and limitations](analysis5.md)
