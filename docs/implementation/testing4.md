[Contents](../index.md) · Previous: [Testing the MeTTa side](testing3.md)

# How we know it works, 4: corpora and held-out data

Fixtures prove the code right on grids somebody thought of. The remaining
question is what happens on the grids nobody thought of, and the suite
answers it at two scales: every grid of every dataset, and tasks deliberately
kept out of a concept's construction.

## Running the whole corpus

Corpus validation is not a pytest test. It is the encoder run over every grid
of every dataset, with errors, timings and cap hits recorded:

| Dataset | Tasks | Grids | Errors | Max encode time/grid | Cap hits |
|---|---|---|---|---|---|
| ARC-AGI-1 training | 400 | 3,436 | 0 | 0.042 s | 117 (3.4%) |
| ConceptARC | 160 | 1,814 | 0 | 0.012 s | 2 (0.1%) |
| Mini-ARC | 149 | 1,354 | 0 | 0.003 s | 0 |

Zero errors is the headline, and the more useful content is in the other
columns. The cap-hit rate is a measurement no fixture could produce: 3.4% of
ARC-AGI-1 grids are noisy enough that object-level pairwise relations need a
fallback, against 0.1% of ConceptARC, which quantifies how much cleaner the
primary experimental dataset is. The pairwise blowup itself was found this
way, by a corpus run that got slow, not by a failing test, and the fixture
guarding it was written afterwards. Fixtures catch regressions; corpus runs
find the surprises that become fixtures.

The exported corpus adds a second whole-corpus check, since every task file
is regenerated from source data and the manifest's totals move whenever the
encoder's output changes, which makes an unintended change visible as a diff.

## Held-out tasks: where testing becomes evaluation

`test_blend_insideoutside.py` runs the entire pipeline on real data: extract
candidates from InsideOutside1 and InsideOutside4, blend, then check the
result against a task that contributed nothing to it. The assertion is a
threshold, the blend must match some held-out grids, plus a structural check
that the blend is not degenerate.

That threshold marks a boundary worth being explicit about. Everywhere else
in the suite, a test asserts an exact answer, and a failure means the code is
wrong. Here the code can be entirely correct while the blend matches nothing,
because whether a concept generalises is a fact about the concept and the
data, not about the implementation. The test pins the weakest claim the
project depends on, that the pipeline can produce at least one generalising
blend on the group it was built against, and leaves every stronger claim to
the experiments, where match rates are results to be reported rather than
assertions to pass. The leave-one-out sweeps, their baselines and their
ceilings live there, in the experiment chapters and the decisions log.

The same file demonstrates the suite's data policy. ConceptARC is fetched by
`make data`, not committed, so both tests begin with a guard that calls
`pytest.skip` naming the command to run. A fresh clone is green offline, and
the skip line in the output says what was not exercised, where a failure
would say nothing useful.

## Executable documentation

One more artifact belongs to the testing story without being a test.
`python/trace_pipeline.py` runs one real task through every stage and prints
what each produced, and the implementation chapter is built from its output.
Whenever the pipeline changes, rerunning the trace and diffing it against the
chapter's quoted output is a review of both at once: either the docs are
stale or the change did something unintended, and the diff says which.

[Contents](../index.md)
