[Contents](../index.md) · Next: [Coverage of the relational vocabulary](analysis2.md)

# Analysis, 1: Scope and requirements mapping

This document reports the results obtained during Milestone 2 and evaluates
them against the functional requirements stated in the RFP. It is the third
of three deliverables specified for this milestone: draft implementation,
initial testing results, and analysis of the results. The implementation is
described in [How the pipeline works](../implementation/pipeline1.md).
Testing methodology and coverage are described in
[How we know it works](../implementation/testing1.md) and
[Running the experiments](../implementation/experiments1.md). This document
assumes familiarity with the vocabulary and pipeline stages described there
and does not repeat their content.

## 1.1 The blending mechanism relative to its conceptual basis

The project implements concept blending following the network model
formalized by Goguen and Eppe, an operationalization of Fauconnier and
Turner's conceptual blending theory. The model defines four spaces: two
input spaces, a generic space computed from their shared structure, and a
blend space formed by selective projection from the inputs. An optional
completion step can surface emergent structure not present in either input
alone. Table 1 maps each space to its implementation.

**Table 1.** Blending-network spaces mapped to implementation components.

| Conceptual space | Implementation | Reference |
|---|---|---|
| Input space | A `Candidate`: one binary relation between two objects in a single grid, together with each object's colour, size, shape and symmetry properties | `enumerate.py`, Stage 1 |
| Generic space | The result of anti-unifying two candidates. Each property slot where the candidates agree is retained as a ground value (`Fixed`); each slot where they disagree becomes a free variable (`Generalized`) | `antiunify.metta`, Stage 3 |
| Blend | The generic space instantiated into a concrete MeTTa pattern. `Fixed` slots become literal values; `Generalized` slots become fresh variables | `blend.metta`, Stage 4 |
| Emergent structure | Not implemented. Completion would run the representation's derivation rules over the blend's projected atoms to surface facts entailed by the combination but present in neither input | decisions.md, D8 |

Two properties of this implementation follow from the fixed schema chosen
for the candidate representation (decisions.md, D7). First, because every
candidate has the same slots in the same order, every element of one input
space corresponds to an element of the other by construction. The general
model allows an element from one input to project into the blend with no
counterpart in the other input; this schema does not produce that case.
Second, projection reduces to a fixed rule applied per slot, retain if the
two inputs agree, generalize if they do not, rather than a selection
process that could retain a disagreeing slot as ground by choosing one
input's value over the other. Both properties are consequences of the
schema restriction documented in D7, adopted to make a working MeTTa
implementation tractable within the milestone timeline, and are reported
here as scope rather than as limitations discovered after the fact.

Coherence checking and information-theoretic scoring, named in the RFP's
first functional requirement, are implemented independently of blend
construction. Coherence is tested by matching the blend's pattern against
held-out grid instances (`blend_pipeline.check_coherence`); this is the
mechanism behind every sweep result reported in Section 3. Minimum
description length scoring (`scoring.py`) implements the formula stated in
the research plan,

```
DL(atom) = (arity + 1) * log2(|symbols|)
```

and computes the compression gain from adding a candidate blend to a
concept library. Its properties and a documented limitation, that the
formula does not distinguish a ground constant from a variable at the same
argument position, are recorded in decisions.md D10.

## 1.2 RFP functional requirements

The RFP states three Must Have requirements, two Should Have requirements,
and two Could Have requirements applicable to this component of the work.
Table 2 records the status of each against the current implementation.

**Table 2.** RFP functional requirements and their status at Milestone 2.

| Requirement | Priority | Status | Evidence |
|---|---|---|---|
| Concept blending with an information-theoretic criterion, or uncertain FCA | Must | Met (blending path) | `scoring.py`; decisions.md D10 |
| Algorithms creating novel concepts, evaluated for novelty and coherence | Must | Met | Coherence: `blend_pipeline.py`. Novelty: `novelty.py`, verified against MeTTa output on 8,794 pairs (D16), corrected after human evaluation (D17) |
| Qualitative evaluation framework for creativity and value, human assessment of novelty and logical consistency | Must | Met | `docs/rating/rubric.md`; 24-blend rating exercise, D17 |
| Exploration of LLM-based evaluation | Should | Not implemented | Scoped as a direct extension of the existing rating protocol; D17, action item 5 |
| Parallel testing of concept blending against uncertain FCA | Should | Not attempted | The project committed to the concept blending path, which the Must Have requirement permits as an alternative to FCA |
| Multi-agent LLM evaluation | Could | Not implemented | Depends on the LLM-based evaluation extension above |
| Information-theoretic refinement balancing novelty and coherence | Could | Partially met | Novelty and MDL gain are computed per blend (D10, D16) but not yet combined into a single acceptance criterion; planned for the Milestone 3 library-learning loop |

All three Must Have requirements are met. Of the two Should Have
requirements, one is not attempted because the project committed to a
single evaluation path at proposal stage, and one is identified as a scoped
extension of existing infrastructure rather than unaddressed work.

## 1.3 Document structure

Section 2 reports coverage of the encoder's relational vocabulary across
the ConceptARC benchmark and establishes the ceiling that bounds any
subsequent match-rate result. Section 3 reports the diversity-based pair
selection result and its replication across three concept groups and three
anchor relations. Section 4 reports the novelty scoring and human
evaluation results. Section 5 reports negative results, states limitations
of the current implementation, and describes experiments planned for
Milestone 3.

Next: [Coverage of the relational vocabulary](analysis2.md)
