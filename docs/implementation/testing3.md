[Contents](../index.md) · Previous: [Fixtures and properties: the encoder](testing2.md) · Next: [Corpora and held-out data](testing4.md)

# How we know it works, 3: testing the MeTTa side

The MeTTa tests run a real interpreter. Each test builds a fresh `MeTTa()`
with only the file under test loaded, so `test_antiunify.py` loads
`antiunify.metta` and nothing else, and no corpus data is anywhere near the
space. What is being tested is the blending logic, not the vocabulary.

One helper carries more weight than its three lines suggest:

```python
def run_one(m, expr):
    res = m.run(f"!{expr}")
    assert len(res) == 1 and len(res[0]) == 1, ...
    return res[0][0]
```

Every call asserts that exactly one result came back. MeTTa fires every
equation whose head matches, so a function accidentally defined with
overlapping equations returns multiple results rather than erroring. During
development, exactly that happened: a wildcard fallback equation made a
predicate return `[True, False]` for every input. `run_one` turns that class
of bug into an immediate assertion failure in whichever test hits it first.

## Anti-unification, case by case

The five tests in `test_antiunify.py` each pin one clause of the generic
space's meaning, with hand-written candidates small enough to read:

```python
c1 = "(Candidate contains blue  red 10 2 (a) (b) (h v) (h))"
c2 = "(Candidate contains green red 10 2 (a) (b) (h v) (h))"
```

One differing slot, so the result must show `(ColorX (Generalized colX))` and
every other slot `Fixed` with its value, asserted individually. The remaining
cases cover the rest of the definition: partially overlapping symmetry sets
keep exactly their intersection, candidates on different relations produce no
result at all, since same-relation pairing is enforced by the equation head
itself, and the degeneracy check fires for identical candidates and stays
quiet for generalised ones.

## Materialisation, and testing around alpha-renaming

`test_blend.py` checks the step from generic space to usable pattern, and one
of its tests documents an interpreter behaviour as much as the code's. A
generalised slot must materialise as a genuine variable, but MeTTa
alpha-renames variables internally, so `$colX` comes back as something like
`$X#57` and no test can assert an exact name. The assertion is structural
instead:

```python
assert re.search(r"\(objColor X \$\w", pattern)
```

some variable, in the right position. Its companion test closes the other
direction: anti-unifying a candidate with itself makes every slot `Fixed`,
and the materialised pattern must contain no `$` at all. Between them the two
tests would catch a materialiser that emitted variables always, or never.

## Integration: the space behaves like the docs say

`test_metta_integration.py` loads real encoder output into a live space and
checks the derivation story told in the vocabulary chapter. The adjacency
test does it in three steps: the forward edge is present as a ground fact,
the reverse edge is asserted absent as a ground fact, and the reverse is then
derived through `adjSym`. Asserting the middle step matters; without it, a
regression that started emitting both directions would pass silently and the
claim "reverse edges are derived, not stored" would quietly become false. The
third test is a smoke test for `sameColorAdjacent`, the worked example the
documentation leans on.

## Export: the string round trip, made a test

The pipeline repeatedly treats MeTTa output as future MeTTa input, and that
round trip has been this project's most reliable source of bugs, from
reserved `#` characters in variable names to a substitution that ran in the
wrong order. `test_export_corpus.py` guards the corpus-file version of the
trip: an exported task file is fed to a real `MeTTa()` parser, which must
accept it, comments and all, and a `match` against the loaded space must find
the expected object. Not a string comparison against expected file contents,
but the actual consumer consuming it.

Next: [Corpora and held-out data](testing4.md)
