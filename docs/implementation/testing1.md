[Contents](../index.md) · Next: [Fixtures and properties: the encoder](testing2.md)

# How we know it works, 1: what the tests are for

The pipeline can go wrong in two places, and they need different kinds of
test. The Python side can misread a grid: find the wrong objects, compute a
relation that is not there, miss one that is. The MeTTa side can mishandle a
pattern: generalise a slot that should have stayed fixed, or lose something in
the round trip from result string back to query. The first kind is about
whether the facts are true. The second is about whether true facts survive the
machinery.

## Why the obvious test proves little

The research plan's encoder validation, E0, asks for a round trip: encode a
grid, rebuild it from the atoms, check they match. It sounds decisive, and it
is worth being clear about what it actually establishes. The cell layer is
copied out of the JSON with no interpretation, so a round trip validates
copying. Every encoder bug this project has actually found lived in the layer
that interprets. The background rule picked the wrong colour on small grids.
Containment was tested in only one direction and silently dropped about a
quarter of the containments it should have found. A symmetry check carried a
guard belonging to a different definition of symmetry. A perfect round trip
would have passed while all three were live.

So the suite is built on a different principle: check each derived fact
against an independent statement of what it means, stated before the code
runs, and preferably in a form the code cannot have influenced. The next two
pages show what that looks like on each side of the language boundary.

## The suite at a glance

Ten files under `tests/`, 48 tests, in three dependency tiers.

```
pure Python, runs anywhere
  test_encoder.py           7   hand-checked fixtures for the encoder
  test_encoder_fixes.py    11   regression and property tests for D13
  test_1d_arc.py            3   single-row grids, published 1D-ARC families
  test_scoring.py           6   MDL arithmetic against hand calculations

needs the hyperon package
  test_antiunify.py         5   generic-space construction
  test_blend.py             5   pattern materialisation
  test_metta_integration.py 3   atoms loaded and queried in a live space
  test_export_corpus.py     3   exported files re-parsed by the real parser

needs hyperon and the fetched datasets
  test_blend_insideoutside.py  2   end-to-end on real ConceptARC data
  test_diversity_selection.py  3   pair selection on real data (1 runs without)
```

Data-dependent tests skip rather than fail when the datasets are absent, via
an explicit check that calls `pytest.skip` with instructions, so `make test`
is green on a fresh clone before `make data` has run. A skip is a visible
choice in the output, where a failure would be noise.

The pure-Python tier run against the current code:

```
python3 -m pytest tests/test_encoder.py tests/test_encoder_fixes.py tests/test_1d_arc.py tests/test_scoring.py tests/test_diversity_selection.py -q
..............................                                                                                                                                       
30 passed in 0.71s

```
 
One engineering rule sits on top of the suite: every sprint ends with
`make test` green and at least one committed experiment artifact, so the tests
gate progress rather than trailing it. Several of the tests below exist
because a sprint's work broke them into existence first.

Next: [Fixtures and properties: the encoder](testing2.md)
