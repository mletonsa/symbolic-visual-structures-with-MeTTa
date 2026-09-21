[Contents](../index.md) · Previous: [Novelty and human evaluation](analysis4.md)

# Analysis, 5: Negative results, limitations, and possible extensions

The research plan commits to reporting negative results as findings rather
than omitting them, on the basis that a structural limit on what blending
can reach is itself informative about the benchmark and the vocabulary.
This section reports the negative results obtained to date, states the
limitations of the current implementation, and identifies possible
extensions Milestone 3 could pursue in response to both.

## 5.1 Negative results

**A concept group's name does not guarantee its concept is structurally
present in every task.** Three of InsideOutside's ten tasks carry no
`contains` atoms at all (decisions.md D7, confirmed against the corrected
encoder in D13 and D14). The group is labelled by a human-assigned concept
name. The relation the vocabulary associates with that concept is absent
from three tasks out of ten. This was verified by direct inspection of
encoder output, not inferred from a failure to match.

**No rated blend in the 24-blend human evaluation sample reached the
rubric's highest value score.** Section 4.4 reports this without
attributing a cause. Two explanations are consistent with the data
available. The stratified sample, drawn to cover the automated novelty
verdict categories rather than to search for high-value concepts
specifically, may not have included one. Alternatively, the two-object,
single-relation candidate schema described in Section 1.1 may have no
route to a blend rich enough to earn the top score, since that score's
rubric definition, a reusable building block generalizing across a task
family, plausibly requires more structure than one relation plus two
objects' unary properties can express. These two explanations are not
distinguished by the current evidence.

**Diversity-based pair selection reliably recovers the anchor relation
itself rather than a specific enrichment of it.** Section 3.6 reports this
as an interpretive point rather than a negative result in isolation, but it
is the most consequential finding of this kind obtained to date. A
selection method validated for improving held-out match rate does so by
converging on the least specific blend available. This is a property of
the mechanism as currently scored, not a failure of the sweep methodology,
and it directly motivates the scoring change described in Section 5.3.

## 5.2 Limitations

Table 8 lists the limitations of the current implementation with the
reference documenting each.

**Table 8.** Limitations of the Milestone 2 implementation.

| Limitation | Consequence | Reference |
|---|---|---|
| Candidate schema fixed to one binary relation and two objects' unary properties | No relation chains, no patterns over three or more objects. Every blend answers a two-object question | decisions.md D7 |
| Emergent structure via completion not implemented | The blend space is realized. The fourth space in the Fauconnier-Turner model, entailed facts surfaced by combining projected atoms, is not | decisions.md D8, Section 1.1 |
| Diversity-selection replication covers three of 16 ConceptARC groups and three of five anchor relations | 71 group and relation pairs meet the usable-task threshold identified in Section 2.5. The three tested here account for three of them, leaving 68 untested | Section 2.5 |
| Ceiling not computed for the SameDifferent/`sameShape` sweep | The baseline-as-percentage-of-ceiling comparison in Table 5 is available for two of three sweeps, not all three | Section 3.2 |
| Copy's input/output asymmetry not verified per task | The InsideOutside asymmetry was confirmed by classifying each usable task's transformation individually (D14). The equivalent classification for Copy has not been performed | Section 3.5 |
| Human evaluation used one rater with card-level assistance, on one group and relation | Section 4.1 states the assistance given. The finding in Section 4.3 was independently confirmed at full automated scale, which bears on the finding's reliability. The assistance itself has not been varied or removed to test its effect on the rating process | Section 4.1 |
| No comparison against an alternative concept-discovery method | The ablations specified in the research plan (scoring disabled, anti-unification replaced by naive union, parameter sensitivity, within-task restriction) test internal components of the blending pipeline. None compares blending's output against an unrelated method, such as frequent subgraph mining, applied to the same candidate data | Research plan, Section 5 |
| Novelty assessed against the base vocabulary and two parent candidates, not a concept library | No library exists yet. The library-learning loop specified in the research plan is Milestone 3 work | `novelty.py`, module documentation |

## 5.3 Possible extensions

**Transformational blending.** The static blends reported in this document
represent structure within one grid. None represents a transformation from
input to output. Decisions.md D14 identifies InsideOutside4, in which every
grid carries `contains` structure, and InsideOutside10, in which
containment increases from input to output (2 of 5 input grids against 3
of 5 output grids), as tasks where a before-and-after pattern pair would
have both sides available to blend from. These are the first targets for
this work.

**Directional and reachability predicates.** Decisions.md D7 records that
the AboveBelow and Center concept groups require predicates the current
vocabulary does not provide, a directional ordering between objects and a
proximity-to-centre relation respectively. Section 2.3 confirms both
groups have substantial coverage under the existing relations, `sameColor`
at 72% for AboveBelow and 55% for Center, so the groups are not
unreachable in general. The specific concepts named by their groups remain
unaddressed by the current vocabulary.

**The library-learning loop.** Implementing the accept, re-encode, and
iterate cycle specified in the research plan would allow novelty
assessment against an actual set of accepted concepts, replacing the
interim base-vocabulary and parent-candidate comparison described in
Section 4.1.

**Extension of the human evaluation protocol.** The RFP lists LLM-based
creativity evaluation as a Should Have requirement. Decisions.md D17
identifies applying the existing rubric to the same sample with an LLM
rater, compared against both the human ratings and the automated verdict,
as a direct extension of the infrastructure built for Section 4.

**Further coverage-matrix candidates.** Section 2.5 identifies 71 group and
relation pairs meeting the usable-task threshold. Extending the
diversity-selection replication to additional pairs from this list, and
computing the ceiling for the SameDifferent sweep to complete Table 5,
would extend the evidence base reported in Section 3 beyond three points.
