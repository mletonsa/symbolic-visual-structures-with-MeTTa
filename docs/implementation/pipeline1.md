[Contents](../index.md) · Next: [From grid to candidates](pipeline2.md)

# How the pipeline works, 1: the shape of the system

The pipeline turns encoded grids into scored concepts in five stages:

```
grids ──> atoms ──> candidates ──> pairs ──> generic space ──> blend ──> checked, scored blend
        encoder    Stage 1        Stage 2   Stage 3           Stage 4   Stage 5
        (Python)   (Python)       (Python)  (MeTTa)           (MeTTa)   (Python + MeTTa)
```

Stage 1 extracts small relational patterns from each task's grids. Stage 2
decides which patterns from different tasks are worth combining. Stage 3
computes what a chosen pair has in common. Stage 4 builds the combined
concept, the blend. Stage 5 checks whether the blend holds on grids it was
not built from, and measures whether keeping it would pay for itself.

This chapter walks one real run through all five stages, start to finish. The
task is ConceptARC's InsideOutside1, its candidates are paired against
InsideOutside4, and the resulting blend is tested on InsideOutside5, which
neither of them has seen. Every number and every atom shown in these pages is
taken from that run, which `python/trace_pipeline.py` reproduces.

## Where Python ends and MeTTa begins

The split is deliberate, and it is not the obvious one of Python for glue and
MeTTa for everything interesting.

MeTTa owns the conceptual core: the representation vocabulary
(`metta/representation.metta`), anti-unification
(`metta/antiunify.metta`), and blend construction (`metta/blend.metta`).
These are the operations the project is actually about, and they are pattern
manipulations, which is what the language is for. A blend built in MeTTa is
itself a MeTTa pattern, immediately usable as a query.

Python owns everything that iterates or counts: encoding grids into atoms
(`python/encoder.py`), enumerating candidates and selecting pairs
(`python/enumerate.py`), driving the MeTTa stages and checking coherence
(`python/blend_pipeline.py`), and MDL scoring (`python/scoring.py`).

The reason is the current performance profile of the MeTTa interpreter.
Enumerating candidates over a corpus, or counting a pattern's occurrences
across hundreds of grids, is bulk work that the interpreter handles slowly
enough to change what experiments are practical, so those loops run in Python
over the same atom data the encoder produces. The conceptual operations run on
small inputs, two candidates or one grid at a time, where the interpreter is
comfortable.

One infrastructure detail follows from the same constraint and shows up in
`blend_pipeline.py`: the pipeline keeps two MeTTa runtimes with different
lifetimes. Blending is pure computation, so one persistent runtime serves
every call. Coherence checking mutates spaces, so its runtime is torn down and
rebuilt every 50 uses to keep accumulated state bounded. The history behind
that arrangement is in the decisions log (D6, D9); for reading this chapter it
is enough to know the two runtimes exist and why.

## The five stages against the research plan

The research plan describes each stage in general form. What is implemented is
a deliberately narrowed version, scoped in the decisions log (D7): candidates
are fixed-schema patterns of exactly two objects and one anchoring relation,
rather than arbitrary relational subgraphs, and anti-unification is a per-slot
comparison rather than a graph-alignment search. The narrowing is what made a
working MeTTa implementation tractable, and the pages that follow describe the
narrowed version that actually runs, noting at each stage what the general
form would add.

Next: [From grid to candidates](pipeline2.md)
