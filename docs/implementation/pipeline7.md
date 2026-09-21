[Contents](../index.md) · Previous: [Checking the blend holds](pipeline6.md)

# How the pipeline works, 7: scoring, and the map of the code

The coherence check says the blend holds somewhere. The second half of Stage 5
asks whether keeping it is worth anything, and the currency is description
length: a concept earns its place if adding it to the library makes the corpus
shorter to write down.

## The MDL arithmetic

`python/scoring.py` implements the plan's formula. Every atom costs
`(arity + 1) * log2(|symbols|)` bits, one symbol's worth for the predicate and
one per argument, under a uniform code over the symbol vocabulary. With the
trace's vocabulary size of 64, a symbol costs 6 bits and a two-argument atom
18.

Without the concept, every matching instance in the corpus is written out as
the pattern's seven raw atoms. With it, the concept's definition is paid once,
and each instance is rewritten as a single concept-instance atom whose
arguments are the pattern's free variables plus the two roles.

For this run's blend and its 19 match instances:

```
dl_raw_per_instance    126.0 bits     7 atoms x 18 bits
dl_definition          126.0 bits     the definition is the pattern, paid once
dl_rewritten_per_inst   54.0 bits     6 variables + 2 roles + predicate, x 6 bits
dl_gain               1242.0 bits     19 x 126 - (126 + 19 x 54)
worth_it              True
```

The definition cost is what gives the score its honest shape. A blend that
matches only the two instances it was built from essentially never pays for
itself, because the one-time definition is not amortised over enough
occurrences. A concept that does not generalise scores badly by construction,
which is the intended behaviour rather than a defect.

## What the number does and does not say

Three properties of this score matter when reading experiment results, all
established empirically in the decisions log (D10, D12).

Within a single schema, MDL gain is a linear function of match count, since
every candidate has the same seven atoms. It adds ranking information only
when comparing structurally different patterns, which the current fixed-schema
pipeline does not yet produce.

The formula does not distinguish a ground constant from a variable at the
same position, so a narrow pattern and a general one with equal match counts
score identically. The formula's only lever against a non-generalising blend
is its low match count, and the measured break-even for a seven-atom pattern
sits between one and two matches, a genuinely low bar.

And the 19 above counts total match instances, not matched grids. A pattern
matching few grids but many object pairs within each can out-score one
matching every grid once. Both numbers answer real questions, how much
redundant structure the concept compresses away versus how widely it
generalises, and the experiment reports carry both rather than choosing.

The full library loop the plan describes, accept a concept, re-encode the
corpus with it as a primitive, repeat, is Milestone 3 work. This module is the
scoring primitive that loop will call.

## Where everything lives

```
metta/
  representation.metta   vocabulary, type declarations, derivation rules
  antiunify.metta        Stage 3: genOrDrop, antiunifyPair, isDegenerate
  blend.metta            Stage 4: materializePattern, buildBlend

python/
  encoder.py             grids to atoms; GridEncoder, Atom
  export_corpus.py       datasets to readable .metta files, with manifest
  enumerate.py           Stages 1-2: Candidate, extraction, pair selection
  blend_pipeline.py      drives Stages 3-5a; runtimes, pattern_to_query,
                         check_coherence
  scoring.py             Stage 5b: MDL gain
  trace_pipeline.py      reproduces every number in this chapter
  experiment_*.py        the sweep drivers used in the experiment chapters

tests/                   encoder fixtures and property tests, anti-unifier
                         and blend cases
docs/decisions.md        the running log this chapter cites as D1, D2, ...
exports/                 generated corpus files; regenerated, not committed
```

The trace behind this chapter is one command from the repository root:

```
python3 python/trace_pipeline.py
```

[Contents](../index.md)
