[Contents](../index.md) · Previous: [From grid to candidates](pipeline2.md) · Next: [The generic space](pipeline4.md)

# How the pipeline works, 3: choosing pairs

Blending needs two inputs. Stage 2 decides which two.

The run has 9 `contains` candidates from InsideOutside1 and 60 from
InsideOutside4, giving 540 valid pairs. A pair is valid when the candidates
come from different tasks and anchor on the same relation. The cross-task
condition is the point of the exercise: a pattern that survives being combined
across tasks is evidence of something the concept group shares, rather than a
quirk of one puzzle. The same-relation condition is this implementation's
scope, since the per-slot anti-unifier needs both inputs to share a schema,
and the schema starts with the relation.

540 is too many to blend. Each blend plus its coherence check costs roughly 2
to 4 seconds of MeTTa time, so checking every pair of one task-pair would take
half an hour, and a leave-one-out sweep multiplies that by hundreds. Stage 2
therefore ranks pairs and spends the MeTTa budget on the best one.

## What makes a pair good

The ranking is built on an observation about what goes wrong. When two
candidates happen to agree on a slot, the anti-unifier keeps that value as an
invariant of the blend. Sometimes the agreement is meaningful. Often it is a
coincidence, and the worst offender is systematic: every single-cell object in
the vocabulary has size 1 and the identical shape signature `((SC 0 0))`,
whatever its task or colour, because there is only one way to be one cell. Two
candidates whose inner objects are both single cells will agree on two slots
for no reason at all, and the blend inherits "the inner object is exactly one
cell" as a requirement. Most containment instances fail it, and the blend
matches almost nothing.

So the pipeline counts, for each pair, how many of the six scalar slots are
exactly equal (`n_coincidental_fixed_slots` in `python/enumerate.py`). This
is pure Python over already-extracted data, no MeTTa involved, effectively
free. In the sweep where this was validated, the count predicted held-out
performance well and monotonically: zero coincidental agreements
matched 7 of 12 held-out grids, one matched 3, two or more matched none
(decisions log, D11).

`select_most_diverse_pair` picks the pair with the lowest count. In this run
the first few pairs score 0, 2, 4, 0, 2, 4, 1, 3, and the selected pair
scores 0:

```
A: (Candidate contains red  blue  20  1  <frame shape>  <single cell>  ...)
B: (Candidate contains blue green 38 20  <larger frame>  <frame shape>  ...)
```

Every scalar slot differs: colours, sizes, shapes, all of it. The only things
these two candidates have in common are the anchor relation and some symmetry
axes, which is exactly what a pair should look like if the goal is a blend
constrained by structure rather than by coincidence.

Selection changed the sweep results more than any other single decision.
Replacing "first candidate from each task" with the diverse pair took the
InsideOutside leave-one-out match rate from 31% to 54% overall, and input
grids from 46% to 81%, at zero additional MeTTa cost, since the same number of
blends is built either way (D11, confirmed on a second group in D12).

Next: [The generic space](pipeline4.md)
