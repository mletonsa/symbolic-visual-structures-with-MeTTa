[Contents](../index.md) · Previous: [Start from the ceiling](experiments1.md) · Next: [Misses are data](experiments3.md)

# Running the experiments, 2: baselines and controlled comparisons

The first result of any experiment here is treated as a baseline to beat, not
as a demonstration to celebrate, and improvements are established by changing
one thing at a time and replicating on a second group before being believed.
This page shows the pattern on the project's main result.

## The first number is the baseline

The first InsideOutside sweep used the laziest possible pair selection, each
task's first candidate, and scored 31% overall (377 of 1,200 held-out
checks). Recorded alongside it was the observation that made the number
useful: per-pair variance was enormous, some source pairs matching 14 of 14
held-out grids and others 0 of 14. A mechanism whose results depend that
heavily on an arbitrary choice is announcing that the choice matters, so the
baseline came with its own hypothesis, that smarter selection should
measurably beat 31%, and a concrete number for the next sprint to aim past.

## One variable at a time

The diversity heuristic was validated by re-running the identical sweep, the
same 7 held-out tasks, the same candidate pools, the same 105 blend-plus-check
runs, with only the selection rule changed: pick the pair with the fewest
coincidentally equal slots instead of the first pair. Everything else held
constant, the overall rate went from 31% to 54% and input grids from 46% to
81%, at zero additional MeTTa cost since the same number of blends is built
either way. Because only one thing changed, the difference can therefore be attributed to the selection rule within this controlled comparison.

The heuristic itself was found on a 4x4 grid of pairs, sixteen data points.
It was not reported from there; it was reported after holding up across the
full sweep. Small controlled experiments are for finding mechanisms cheaply,
full sweeps are for believing them.

## Replicate on a second group before believing

One group can flatter a method that was, after all, developed against it. The
same comparison was rerun on SameDifferent, a different group anchored on a
different relation, `sameShape` rather than `contains`. Baseline 52%, diverse
77%, input grids 97%. A selection rule validated on one relation and
confirmed on a structurally different one supports a much stronger claim than
either result alone, and until that second run, the wording stayed at
"validated on one group".

Scope stays honest too: the SameDifferent runs used 5 of the group's 10
tasks, sized to fit a reasonable runtime, and cross-group comparisons lean on
that sample lightly.

## Two match metrics, both reported

One SameDifferent result looked like a bug until it was understood: the top
three blends by MDL gain matched only 6 of 12 held-out grids, while the
bottom three matched 12 of 12. The two rankings disagree because they count
different things. MDL gain is computed from total match instances, every
matching object pair across all grids summed, while the sweep's headline
counts grids with at least one match. A pattern matching fewer grids but many
pairs within each can out-score one matching every grid once, and with
`sameShape`, where a single grid can hold several same-shaped pairs, it does.

Both numbers answer real questions, how much redundant structure a concept
would compress away versus how widely it generalises, and reporting either
alone would mislead. Every result table since carries both.

Next: [Misses are data](experiments3.md)
