[Contents](../index.md) · Previous: [Baselines and controlled comparisons](experiments2.md) · Next: [Long runs and the log](experiments4.md)

# Running the experiments, 3: misses are data

The research plan commits to reporting negative results, every gated-out
blend and every experiment where blending yields no gain, on the view that
"structural blending cannot reach this" is a finding about ARC concepts, not
an embarrassment. In practice the commitment has paid for itself: the
project's most useful result so far started as a pattern in the misses.

## The asymmetry that became a finding

The very first real blend attempted missed 4 of 12 held-out grids, and the
misses concentrated on output grids. That could have been noise. Instead it
was recorded with a candidate explanation, several InsideOutside puzzles
remove the containment structure as their transformation, and left as an
observation.

The full sweep turned the observation into numbers: 46% of input checks
matched against 17% of outputs. The second group echoed it, 67% against 37%,
close enough that the log promoted it to a stated hypothesis, that ConceptARC
transformations generally disrupt whatever static relational invariant a
task's inputs share, explicitly marked as needing more groups before being
treated as established.

The coverage measurement then closed it from a different direction. The
asymmetry is in the raw atoms before any blending runs: 85% of the group's
input grids carry containment against 30% of outputs. Outputs are not harder
to match; the structure is mostly absent from them, and blends run at about
93% of the output ceiling, nearly the same efficiency as on inputs. What
began as a miss pattern ended as a property of the benchmark, with a
three-step provenance, observed, replicated, explained at the level of the
data.

The per-task detail refined it further and produced targets. Of the seven
usable tasks, four destroy containment entirely in their outputs, one
preserves it in every grid, one reduces it, and one creates containment that
was not in the input. The preserve and create cases are the natural first
targets for transformational blending, and the destroy cases mark exactly
what the current vocabulary cannot express, absence.

## Zero-structure tasks are findings too

Three of InsideOutside's ten tasks contain no `contains` atoms at all. That
is a fact about the benchmark worth knowing before assuming a group's name
describes its structure: "InsideOutside" does not mean containment uniformly,
and a human-labelled concept group realises its concept in structurally
unrelated ways. The claim was originally derived from buggy encoder output,
so it was rechecked after the D13 containment fix; the same three tasks are
still empty, which is what let the recorded sweep baselines stand.

## A miss explained beats a hit unexplained

The diversity heuristic itself came from inspecting failures rather than
successes. In the 4x4 pair grid where it was found, three candidates scored
zero with every partner, and comparing their materialised blends against the
one good candidate's showed why: both source objects happened to be single
cells, every single-cell object normalises to the identical shape signature,
anti-unification treated the coincidence as an invariant, and the blend
over-narrowed to require an exact single-cell inner object. The mechanism
generalised into a selection rule; the failing blends were the evidence.

Two standing rules follow. Misses are recorded at the same granularity as
hits, per grid and per pair, because the pattern in them is where mechanisms
show up. And a proposed explanation for a miss is labelled as hypothesis
until it survives a second group and, where possible, a measurement that does
not involve the mechanism at all.

Next: [Long runs and the log](experiments4.md)
