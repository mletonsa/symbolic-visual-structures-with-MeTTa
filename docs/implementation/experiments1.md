[Contents](../index.md) · Next: [Baselines and controlled comparisons](experiments2.md)

# Running the experiments, 1: start from the ceiling

Every experiment in this project reports its results against what the
representation allows, not against a perfect score. This page explains the
habit, because it changes how every number in the result chapters should be
read.

## A match rate has a ceiling, and it is computable in advance

A blend anchored on `contains` cannot match a grid that carries no `contains`
atom. No amount of search, scoring or compute moves that bound; it is fixed
the moment the encoder runs. So before a sweep, the first measurement is
coverage: how many of the grids to be checked carry the anchor relation at
all.

For the InsideOutside sweep, the seven usable tasks contribute 80 grids, of
which 46 carry containment, 34 of 40 inputs and 12 of 40 outputs. The sweep
makes 15 checks against each grid, 1,200 in total, so the arithmetic gives
hard ceilings before anything runs: at most 510 of 600 input checks and 180
of 600 output checks can ever succeed, 57.5% overall.

Against those ceilings, the sweep results read differently than they do
against 100%:

| | Achieved | Ceiling | Share of ceiling |
|---|---|---|---|
| First-candidate baseline | 377/1200 (31%) | 690 (57.5%) | 55% |
| Diverse-pair selection | 654/1200 (54%) | 690 (57.5%) | 95% |
| Diverse, input grids | 486/600 (81%) | 510 (85%) | 95.3% |
| Diverse, output grids | 168/600 (28%) | 180 (30%) | 93.3% |

"54%" invites a reader to see the missing 46% as failure. "95% of what the
representation makes reachable" says what actually remains: about four points
of headroom on inputs, two on outputs, and nothing further for pair selection
to win. Improvement past this line requires a different anchor relation or a
richer vocabulary, which is a conclusion about where to spend effort that the
raw rate hides. These numbers were re-verified against the D13-corrected
encoder and returned identical counts (decisions.md D13, action item 1).

## Coverage is measured, not assumed

`python/check_group_relation_coverage.py` produces the coverage table for any
group and relation, split by input and output grids, and it runs before any
new group enters the experimental suite. It earns its place twice over.

It sets the sweep's scope. Three of InsideOutside's ten tasks carry no
containment at all, so the sweep is 7 held-out tasks and 105 runs rather than
10 and 360, and the two are not comparable, which matters whenever a re-run
is compared against a recorded baseline.

And it turns intuitions into decisions. Whether the vocabulary can express a
group's concept is an empirical question with a cheap answer, and a group
coming back empty across every anchor relation is the measured form of "this
group needs a predicate we do not have".

## The ceiling and the central caveat are the same fact

Reaching 95% of ceiling requires the maximally general blend, the bare
anchor relation with every property slot generalised, and the pipeline's
best blends are exactly that. So a near-ceiling match rate is not independent
evidence that blending discovers structure; it measures how completely the
pipeline converges back onto a primitive the encoder supplied. The honest
comparison for any future scoring gate follows from this: a gated blend that
scores below 57.5% is not automatically worse, it is trading coverage for
specificity, and the gate should be judged on how much coverage it costs
relative to the ceiling, not on raw match rate, which falls by design once
maximally general blends are excluded.

Next: [Baselines and controlled comparisons](experiments2.md)
