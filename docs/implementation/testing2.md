[Contents](../index.md) · Previous: [What the tests are for](testing1.md) · Next: [Testing the MeTTa side](testing3.md)

# How we know it works, 2: fixtures and properties, the encoder

The encoder's tests come in two kinds. Fixtures are small grids whose correct
encoding was worked out by hand, on paper, before running the code. Property
tests check a derived fact against an independent restatement of its
definition over many random grids. The two catch different failures so the
suite needs both.

## Fixtures, and what makes one worth having

`test_encoder.py` holds seven, each a grid small enough to reason about
completely: a two-cell line, a solid square, an L-tromino, two diagonal cells,
a hollow ring, a nested pair, and a grid built to trip the pairwise cap. The
file states its own standard in the docstring: expected object counts, sizes,
adjacencies and symmetry facts were worked out by hand before running the
code, not derived from the code's own output. A fixture whose expectations
came from the code only pins today's behaviour, bugs included.

The L-tromino shows what a well-chosen fixture looks like. The comment above
it works through the geometry by hand: reflecting this orientation across the
anti-diagonal maps the offset set onto itself, so the shape is symmetric under
`d2` and under nothing else. The expected answer is one axis, not zero and
not all six, which is what gives the fixture its power. A transform function
that always reports no symmetry fails it, and so does one applying the wrong
axis list. The comment is equally plain about a limit: a transform with its
sign flipped would still pass, since the tromino cannot tell `d2` from its
mirror. Knowing what a test cannot catch is part of the test.

The cap fixture is a regression test with a history. Ten isolated cells and
`max_pairwise_objects=5` must produce a `tooManyObjects` flag and no pairwise
relations at all, then the same grid with the cap raised must produce them
normally. It exists because ARC-AGI task `0dfd9992`, a noise field of 441
single-cell objects, once produced roughly 135,000 atoms from one grid.

## Property tests, where fixtures cannot reach

The D13 containment bug motivates the second kind. `contains` was tested in
one direction only, keyed to component scan order, and every hand-built
fixture happened to scan the container first, so all of them passed. The fix
came with `test_encoder_fixes.py`, which pins the failure three ways.

A regression pair: the same nested shapes twice, once with the container
scanned first and once with the contained cell first, both required to emit
the same relation. The second grid is the one the old code failed.

A brute-force cross-check: 300 random grids, and for each, the emitted
`contains` set compared against the definition restated independently in the
test itself, both directions, strict enclosure. The test contains its own
tiny reimplementation precisely so the two cannot share a bug.

A property over 500 random grids: `contains` is never emitted mutually. This
one is a property rather than a fixture out of necessity, since two
4-connected components sharing an identical bounding box appears to be
geometrically unreachable, and no concrete example exists to write down.

The same file pins decisions as well as fixes. Pattern-frame symmetry is
deliberate, so a test asserts that an off-centre symmetric shape fires and a
d1-symmetric foreground in a non-square grid fires too. If someone later
switches `gridSymmetric` to grid-frame, two tests fail and say why.

## The 1D tests

`test_1d_arc.py` holds three hand-built single-row grids in the style of
published 1D task families, checking the one thing the research plan uses
1D-ARC for: the same vocabulary works with one row and no special-casing in
`encoder.py`. The fill-between fixture doubles as a structural case the corpus
code must tolerate, two endpoint objects in the input becoming one object in
the output, so object counts need not match across an input/output pair.

These fixtures were written under a mistaken belief about the dataset, and the
file's own docstring still records it: that 1D-ARC was a procedural generator
with no corpus to download. The actual 1D-ARC is a dataset, published with
Xu et al.'s TMLR 2024 paper and available at `khalil-research/1D-ARC` under
`dataset/`, organised by task type with 50 tasks each. The generator the tests
refer to is a separate third-party project. The correction is recorded in the
decisions log (D15).

The fixtures remain useful, since they are small enough to check by hand and
they pin the one-row path directly. What changes is that they are no longer a
substitute for the corpus. With the real dataset fetched, the 1D path gets the
same whole-corpus validation the other datasets get, and 1D-ARC can serve as
the low-complexity debugging domain the plan intended rather than as three
examples.

Next: [Testing the MeTTa side](testing3.md)
