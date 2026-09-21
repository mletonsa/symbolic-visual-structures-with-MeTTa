# Detailed Research Plan: Milestones 2 and 3

**Project:** Pattern Discovery in Symbolic Visual Structures (Concept Blending in MeTTa)
**Status:** Milestone 1 complete. This document is the operational plan for executing Milestones 2 and 3.
**Relation to the Milestone 1 plan:** The Milestone 1 research plan defines the scope and philosophy. This document commits to concrete representations, algorithms, experiments, and a re-baselined schedule so that implementation can start immediately.

---

## 1. Re-baselined Schedule

The original schedule placed Milestone 2 in February-May 2026 and Milestone 3 ending 31 August 2026. Since implementation is starting now (late July 2026), the schedule below compresses Milestone 2 into seven weeks and moves Milestone 3 completion to the end of November 2026. Two practical notes:

1. **Communicate the revision to Deep Funding early.** Milestone deadlines in Deep Funding projects are generally renegotiable when communicated proactively. A short note explaining the delay and attaching this plan is better than silence followed by a late deliverable.
2. **AGI-26 has passed as a publication target.** The AGI-26 paper deadline was 20 April 2026 and the conference ran 27-30 July 2026 in San Francisco. The realistic dissemination route is: (a) an arXiv preprint at the end of Milestone 3, which satisfies the "preprint or submission-ready manuscript" deliverable, and (b) submission to AGI-27 when its CFP opens (historically late winter / early spring), with PRICAI or a cognitive-systems venue as alternatives. Notably, AGI-26 ran special sessions on neural-symbolic and hybrid methods, which is exactly this project's category, so AGI-27 remains a well-matched target.

| Phase | Dates (indicative) | Content |
|---|---|---|
| Sprint A | 28 Jul - 9 Aug | Repo scaffold, environment, grid encoder, representation validation |
| Sprint B | 10 Aug - 23 Aug | Anti-unification and blend construction in MeTTa |
| Sprint C | 24 Aug - 13 Sep | Scoring (MDL, coherence, novelty, reuse), experiment harness, experiments E1-E2 |
| Sprint D | 14 Sep - 20 Sep | Milestone 2 consolidation and submission |
| Sprint E | 21 Sep - 11 Oct | Refinement, library-learning loop, experiments E3-E4 |
| Sprint F | 12 Oct - 1 Nov | Full experimental suite, ablations, analysis |
| Sprint G | 2 Nov - 30 Nov | Report, preprint, documentation, tutorial, repo release, Milestone 3 submission |

Milestone 2 deliverables (20 Sep): draft MeTTa implementation, initial experimental results, draft analysis.
Milestone 3 deliverables (30 Nov): final report, documented open-source release, arXiv preprint / submission-ready manuscript.

---

## 2. System Architecture

Three layers, with a deliberate division of labor between Python and MeTTa. This hybrid split is a documented design decision, motivated by the current performance profile of the hyperon-experimental interpreter: MeTTa is the canonical representation and the home of the blending operators, while combinatorially heavy enumeration and numeric scoring run in Python over the same atom data.

```
+---------------------------------------------------------------+
| Layer 3: Experiment harness (Python)                          |
|  task selection, run configs, logging, metrics, plots         |
+---------------------------------------------------------------+
| Layer 2: Blending core                                        |
|  MeTTa: representation vocabulary, pattern matching,          |
|         anti-unification, blend construction, coherence rules |
|  Python: candidate subgraph enumeration, MDL / novelty /      |
|          reuse scoring, library management                    |
+---------------------------------------------------------------+
| Layer 1: Perception front-end (Python)                        |
|  ARC JSON -> atoms: cells, colors, adjacency, components,     |
|  bounding boxes, shape descriptors, symmetry facts            |
+---------------------------------------------------------------+
```

**Environment.** Two supported execution paths, both documented in the README:
- `pip install hyperon` (pin the version current at implementation time; 0.2.10 as of late July 2026) inside a Python 3.11+ virtualenv. This is the primary development path because it lets Python and MeTTa share one process via the `hyperon` Python API (`MeTTa()` runner, `space.add_atom`, `metta.run`).
- The `trueagi/hyperon` Docker image for reproducibility, with the tag pinned in the Dockerfile (avoid `latest` in committed artifacts; record the digest).

Optional exploration if interpreter throughput becomes a bottleneck on larger corpora: MORK (MeTTa Optimal Reduction Kernel) as a faster backend for bulk pattern queries. This is a stretch item, only worth touching in Sprint E if profiling justifies it.

---

## 3. Representation Specification (Layer 1)

The encoder converts each ARC grid into a fixed vocabulary of ground atoms. The vocabulary is small by design; every predicate below must be used by at least one experiment or it gets cut.

### 3.1 Ground facts per grid

```metta
; Identity and geometry
(cell <task> <grid> <id>)             ; grid in {in-0, out-0, in-1, ...}
(coord <id> (C <x> <y>))
(color <id> <c>)                      ; c in {black ... maroon}, ARC palette 0-9

; Local relations (4-neighborhood; 8-neighborhood behind a flag)
(adj <id1> <id2> <dir>)               ; dir in {up, down, left, right}

; Derived objects (connected components per color, background excluded)
(object <task> <grid> <oid>)
(member <oid> <id>)
(objColor <oid> <c>)
(size <oid> <n>)
(bbox <oid> (C <x1> <y1>) (C <x2> <y2>))
(shape <oid> <sig>)                   ; normalized cell-offset signature
(holes <oid> <n>)                     ; for hollow-shape concepts

; Object-level relations
(sameShape <oid1> <oid2>)
(sameColor <oid1> <oid2>)
(contains <oid1> <oid2>)              ; bbox containment
(alignedRow <oid1> <oid2>) (alignedCol <oid1> <oid2>)
(symmetric <oid> <axis>)              ; axis in {h, v, d1, d2, rot90, rot180}
(gridSymmetric <grid> <axis>)
```

### 3.2 Design rules

- **Cell-level atoms are generated but excluded from blending by default.** Blending operates on the object level and above; cell atoms exist for inspection and for computing derived facts. This is the main defense against hypergraph blow-up (a 30x30 grid is 900 cell atoms but typically fewer than 15 objects).
- **Everything is inspectable.** A `pretty` utility renders any object or concept back to an ASCII grid fragment, used in all logs and in the paper's figures.
- **1D-ARC uses the same vocabulary** with y fixed to 0, which is what makes it useful as a debugging domain.
- The encoder is deterministic and unit-tested against hand-encoded fixtures (at least 5 grids with known object counts, adjacencies, and symmetry facts).

---

## 4. Blending Mechanism Specification (Layer 2)

The mechanism follows the Fauconnier-Turner network structure operationalized in the Goguen / Eppe tradition: input spaces are relational subgraphs, the generic space is computed by anti-unification, and the blend is a selective merge scored by information-theoretic utility. Five stages:

### Stage 1: Candidate extraction

From each task's encoded examples, enumerate connected relational subgraphs anchored on objects, with 1-2 object variables and up to k relation atoms (start k=4). Enumeration runs in Python over the exported atom lists; each candidate is stored back as a MeTTa pattern:

```metta
(pattern p017
  ((object $t $g $o1) (object $t $g $o2)
   (sameColor $o1 $o2) (alignedRow $o1 $o2)))
```

Frequency filtering: keep patterns matching at least m instances (start m=3) across the corpus slice under study. This is the pool of "input space" candidates.

### Stage 2: Pair selection

Blending all pairs is quadratic and mostly useless. Pairs are selected when they (a) share at least one predicate symbol but are not identical, and (b) come from different tasks or different ConceptARC concept groups (the cross-group condition is Experiment E2's manipulation). A cap of N pairs per run (start N=500) keeps runs bounded.

### Stage 3: Generic space via anti-unification

Compute the least general generalization of the two patterns: align atoms by predicate, unify aligned arguments where equal, replace disagreements with fresh variables, drop unalignable atoms. Implemented as a MeTTa function `(antiunify $p1 $p2)` with the alignment search assisted from Python when patterns exceed a size threshold. The output is the generic space G plus the two morphisms (variable substitutions) G -> p1, G -> p2.

### Stage 4: Blend construction

The blend is the union of p1 and p2 quotiented by the generic-space correspondences, with selective projection:

- Corresponding atoms merge to their generalization.
- Non-corresponding, non-clashing atoms project into the blend.
- Clashing ground atoms (e.g. `(objColor $o red)` vs `(objColor $o blue)`) resolve by generalizing to a shared variable; if generalization is type-inconsistent, the atom pair is dropped and the drop is logged.
- An optional completion step runs the encoder's derivation rules forward on the blend to surface emergent structure (e.g. two projected alignment facts jointly implying a symmetry fact that was in neither input). Emergent atoms are tagged, since they are the theoretically interesting output.

Each blend is materialized as a named concept with its provenance:

```metta
(concept b042 (blendOf p017 p203) <pattern> (emergent <atoms>))
```

### Stage 5: Scoring and library update

Four scores per blend, combined lexicographically (coherence is a gate, then MDL gain, then novelty as tiebreaker; reuse is measured, not optimized):

- **Coherence (gate):** the blend pattern is satisfiable, type-consistent, and matches at least one instance in a held-out slice of tasks it was not extracted from. Blends failing the gate are logged as negative results, never silently discarded.
- **Compression (MDL gain):** description length of the corpus slice when the concept is added to the library and matched occurrences are rewritten as single concept-instance atoms, versus without it. DL is measured in bits with a uniform code over the symbol vocabulary: DL(atom) = (arity + 1) * log2 |symbols|. Gain must exceed the encoding cost of the concept definition itself. This is the DreamCoder-style MDL objective transposed to the Atomspace.
- **Novelty:** the blend is not subsumed by (an instance or renaming of) any existing library concept or either parent; graded by approximate graph edit distance to the nearest library concept (networkx approximation is sufficient at these sizes).
- **Reuse:** number of distinct tasks whose encoding matches the concept, and a search-reduction proxy: the reduction in candidate-pattern enumeration size when the concept is available as a primitive in Stage 1 of the next iteration.

Accepted blends enter the library; the corpus is re-encoded with library concepts as primitives; Stages 1-5 iterate. Two to three iterations is the target for Milestone 3 ("ladder of abstractions" demonstration); one iteration suffices for Milestone 2.

---

## 5. Experiments

Data: ConceptARC (primary, concept-grouped), ARC-AGI-1 training set (reference), 1D-ARC and Mini-ARC (development), Re-ARC (procedural variants). All fetched by a `make data` script with pinned commits.

| ID | Question | Setup | Output |
|---|---|---|---|
| E0 | Does the representation faithfully and inspectably encode grids? | Encoder round-trip on 1D-ARC + Mini-ARC + 10 hand-checked ConceptARC tasks; atom counts, timing | Validation report, fixture tests (Sprint A) |
| E1 | Do within-group blends recover the group's defining concept? | 4-6 ConceptARC groups (e.g. AboveBelow, InsideOutside, SameDifferent, Center); blend candidates within each group; inspect top-MDL concepts against the group's known concept | Table: recovered concepts per group, MDL gains, examples (Sprint C) |
| E2 | Do cross-group blends produce concepts neither group contains? | Blend across group pairs; test matches on a third group and on ARC training tasks; count emergent atoms | Cross-group concept catalog with provenance (Sprint C) |
| E3 | Does the learned library compress and transfer? | Iterated library learning on a 40-60 task corpus; DL of corpus per iteration; reuse counts; search-reduction proxy | Compression curves, reuse histograms (Sprint F) |
| E4 | Are learned concepts stable under task perturbation? | Re-ARC: 50-100 generated variants of 5-10 tasks; concept match rates across variants | Stability table per concept (Sprint F) |
| E5 (optional) | Are learned concepts human-interpretable? | LLM labels each learned concept from its pattern + example matches; author verifies labels | Qualitative appendix, explicitly supplementary |

**Ablations (Sprint F):** (a) scoring off, accept random coherent blends, to show MDL selection matters; (b) anti-unification replaced by naive union, to show the generic space matters; (c) k and m sensitivity; (d) blending restricted to within-task only, to isolate the contribution of cross-task input spaces.

**Negative-result policy:** every gated-out blend and every experiment where blending yields no MDL gain is reported. The RFP framing treats these as valid findings, and E1 failing on a given group is itself a result about which ARC concepts are reachable by structural blending.

---

## 6. Repository and Engineering Plan

```
symbolic-visual-structures-with-MeTTa/
  README.md            install, quickstart, reproduction commands
  Dockerfile           pinned hyperon image + python deps
  Makefile             data, test, experiment targets
  metta/
    representation.metta   vocabulary, derivation rules
    antiunify.metta        generic-space computation
    blend.metta            blend construction, completion
    concepts.metta         learned library (generated, versioned per run)
  python/
    encoder.py             ARC JSON -> atoms
    enumerate.py           Stage 1-2 candidate/pair generation
    scoring.py             MDL, novelty, reuse
    harness.py             experiment runner, config-driven
    pretty.py              ASCII rendering of atoms/concepts
  experiments/
    configs/*.yaml         one per experiment ID
    results/               logs, metrics, concept catalogs (committed)
  tests/                   encoder fixtures, antiunify unit tests, blend cases
  docs/                    design notes, tutorial (Milestone 3)
```

Engineering rules: every sprint ends with `make test` green and at least one committed experiment artifact; results directories are append-only with run IDs; design decisions and dead ends go into `docs/decisions.md` as they happen, which later becomes the report's methods narrative and the blog material.

---

## 7. Manuscript Plan (Milestone 3)

Working title: *Concept Blending for Abstraction Discovery in Symbolic Visual Structures: Experiments in MeTTa*. Target length: AGI conference full paper (up to 15 pages LNCS). Skeleton, mapped to already-existing material:

1. Introduction and motivation (from the proposal)
2. Background: blending theory, Goguen/Eppe formalization, DreamCoder, ARC (condensed from the Milestone 1 literature review)
3. Representation and blending mechanism in MeTTa (Sections 3-4 of this plan, with real code)
4. Experiments E1-E4 with ablations
5. Discussion: which ARC concept classes are reachable by structural blending, limitations, MeTTa-specific lessons (interpreter performance, hybrid architecture)
6. Related work and conclusion

Route: arXiv preprint by end of November 2026 (satisfies the deliverable), then AGI-27 submission when the CFP opens, with the neural-symbolic special-session track in mind. PRICAI or Advances in Cognitive Systems are fallbacks depending on final emphasis.

---

## 8. Risks Specific to This Plan

- **MeTTa interpreter throughput.** Mitigated by the hybrid architecture, object-level (not cell-level) blending, candidate caps, and MORK as a fallback. Profiling checkpoint at end of Sprint C decides whether corpus sizes for E3 need reduction.
- **Anti-unification alignment blow-up.** Mitigated by pattern size cap k, predicate-overlap pair filtering, and Python-side alignment for large patterns.
- **Blends that are coherent but trivial** (e.g. rediscovering `sameColor`). Handled by the novelty score and reported honestly; the ablation (a) makes the selection mechanism's contribution explicit either way.
- **Compressed calendar.** Sprint C is the schedule's load-bearing element; if it slips more than a week, E4 shrinks (fewer Re-ARC variants) before anything else does, and E5 is dropped first.
- **Milestone renegotiation.** Contact Deep Funding in week 1 with the revised dates rather than at the Milestone 2 deadline.
