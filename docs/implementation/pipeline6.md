[Contents](../index.md) · Previous: [Building the blend](pipeline5.md) · Next: [Scoring, and the map of the code](pipeline7.md)

# How the pipeline works, 6: checking the blend holds

A blend built from InsideOutside1 and InsideOutside4 has, so far, only ever
seen those two tasks. Stage 5's first question is whether it describes
anything beyond them. The run checks it against InsideOutside5, a task
neither source has touched, by matching the query from the previous page
against each of its twelve grids.

## One grid, one space

`check_coherence` loads a single grid's atoms into a fresh, uniquely named
sub-space and runs the query there. Grids are never concatenated into one
big space, for two reasons that happen to point the same way.

The semantic reason: the question being asked is "does the blend match in
this grid", per grid, so that hits and misses can be attributed. A match
found somewhere in a blob of unrelated grids answers a vaguer question, and
could even span grids, binding X from one and Y from another.

The practical reason: small spaces keep the interpreter comfortable. A single
grid is tens to low hundreds of distinct symbols, and the pipeline's history
with large shared spaces (decisions log, D6) argues for keeping it that way
even now that the underlying interpreter bug is fixed upstream.

The same history explains the two-runtime arrangement mentioned in the first
page. Coherence checking mutates spaces, so its runtime is recycled every 50
uses (`RECYCLE_EVERY` in `python/blend_pipeline.py`), bounding both memory
and accumulated state. Blending itself mutates nothing and keeps one
persistent runtime.

## The result on the held-out task

```
InsideOutside5: matched 7 of 12 grids

train0_input    1        train0_output   0
train1_input    1        train1_output   0
train2_input    4        train2_output   1
test0_input     2        test0_output    0
test1_input     0        test1_output    0
test2_input     7        test2_output    3

input grids matched: 5 of 6     output grids matched: 2 of 6
```

The counts are match instances, distinct ways the query's variables can be
bound in that grid, so `test2_input` containing 7 means seven object pairs
there stand in the containment relation.

Two readings of this table, both of which recur throughout the experiments:

The blend generalises. Seven of twelve grids of an unseen task contain its
structure, which for a pattern built from two examples of two other tasks is
the outcome the coherence gate exists to detect. Blends that fail it are
logged as negative results rather than discarded, per the plan's reporting
policy.

The misses are not noise. They concentrate on output grids, five of six
inputs matched against two of six outputs, and the reason is a property of
the benchmark rather than of the blend: several InsideOutside puzzles remove
the containment structure as their transformation, keeping only the inner or
outer object, so a pattern anchored on static containment has nothing to
match in their outputs. The raw atom counts confirm it, with 85% of the
group's input grids carrying containment against 30% of outputs. An
explicable miss is a finding, and this asymmetry became one of the project's
more useful ones (D9, D14).

Next: [Scoring, and the map of the code](pipeline7.md)
