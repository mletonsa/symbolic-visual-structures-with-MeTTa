[Contents](../index.md) · Previous: [The shape of the system](pipeline1.md) · Next: [Choosing pairs](pipeline3.md)

# How the pipeline works, 2: from grid to candidates

The run starts with the first training input of InsideOutside1, a 10x10 grid
with a red frame and four scattered blue cells, one of them inside the frame:

```
. . . . . . . . . .
. . . . . . . . . .
. . 2 2 2 2 2 2 . 1
. . 2 . . . . 2 . .
. . 2 . . 1 . 2 . .
. . 2 . . . . 2 . .
. . 2 . . . . 2 . .
. . 2 2 2 2 2 2 . .
1 . . . . . . . . .
. . . . . 1 . . . .
```

The encoder turns it into 575 atoms, 504 of them cell-level, describing 5
objects: the red frame (`o0`, 20 cells, one hole, symmetric on all six axes)
and four single blue cells (`o1` to `o4`). Fifteen relation atoms tie the
objects together, and one of them is the fact this group is about:

```metta
(contains o0 o2)
```

The blue cell at row 4, column 5 sits inside the frame. The other three blue
cells are outside it, so no other `contains` exists. (Object ids are
shortened throughout this chapter; the full form is
`conceptarc__InsideOutside1_train0_input_o0`.)

The vocabulary these atoms come from has [its own chapter](../encoding/vocabulary.md).

## Stage 1: one candidate per relation atom

A candidate is a small pattern built around one relation atom: the relation,
plus everything the encoder knows about its two endpoint objects. Extraction
(`extract_candidates` in `python/enumerate.py`) walks the grid's relation
atoms and produces one candidate for each. This grid yields 15, of which one
anchors on `contains`:

```
alignedRow  x=red/20  y=blue/1     (frame and the blue cell level with its top)
contains    x=red/20  y=blue/1     (frame and the blue cell inside it)
sameShape   x=blue/1  y=blue/1     (blue cells pairwise)
sameColor   x=blue/1  y=blue/1
...
```

Two things happen at extraction that shape everything downstream.

**Object identity is discarded immediately.** The candidate does not remember
that its objects were `o0` and `o2`. They become the roles X and Y, so the
candidate is already a pattern with two open slots, not a fact about two
particular objects. The original ids are kept only as provenance for tracing a
result back to its source.

**The candidate's shape is fixed.** Every candidate has exactly the same
slots: the anchor relation, then each role's colour, size, shape signature,
and symmetry-axis set. Here is the `contains` candidate as MeTTa, which is
exactly what the anti-unifier will receive:

```metta
(Candidate contains red blue 20 1
  ((SC 0 0) (SC 0 1) (SC 0 2) (SC 0 3) (SC 0 4) (SC 0 5)
   (SC 1 0) (SC 1 5) (SC 2 0) (SC 2 5) (SC 3 0) (SC 3 5)
   (SC 4 0) (SC 4 5) (SC 5 0) (SC 5 1) (SC 5 2) (SC 5 3)
   (SC 5 4) (SC 5 5))
  ((SC 0 0))
  (d1 d2 h rot180 rot90 v)
  (d1 d2 h rot180 rot90 v))
```

Reading it: X contains Y, X is red with 20 cells and the listed frame shape,
Y is blue with 1 cell and the single-cell shape, and both are symmetric on all
six axes. The two long lists are the shape signatures, passed through as
opaque values; downstream stages only ever compare them for equality.

## What the fixed shape buys, and what it costs

Because every candidate has the same slots in the same order, comparing two of
them reduces to comparing slot by slot. That is what makes the MeTTa
anti-unifier in the next stages a page of code rather than a search procedure.

The cost is expressiveness. The research plan's general Stage 1 enumerates
relational subgraphs with up to k relation atoms, which would allow chains of
three or more objects and patterns mixing several relations. The fixed schema
cannot say "X contains Y and Y contains Z", and it is the reason cross-group
blending, where two patterns need not share a shape at all, remains future
work. The scoping decision and its rationale are recorded in the decisions
log (D7).

Across all twelve grids of InsideOutside1, extraction finds 9 candidates
anchored on `contains`. The other task in this run, InsideOutside4, is much
denser: 60. What to do with two pools of candidates is the next stage.

Next: [Choosing pairs](pipeline3.md)
