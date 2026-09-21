[Contents](../index.md) · Previous: [Misses are data](experiments3.md)

# Running the experiments, 4: long runs, and writing them down

The last page of this chapter is about mechanics: how measurements are taken,
how sweeps survive a bounded environment, and how the whole thing gets
recorded so the report can be written from evidence rather than memory.

## Measure steady state, never one call

A performance comparison in this project once reversed itself. A first timing
suggested SameDifferent coherence checks were much slower than InsideOutside
ones, 1.9 s against what looked like 4.4 s, and a full sweep timing out
seemed to confirm it. Both numbers were single calls in fresh processes,
dominated by one-time runtime and stdlib loading. Measured as a loop in one
process, the steady-state figures were 4.1 s and 1.85 s, the opposite
ordering, and the sweep had timed out for the mundane reason that more tasks
have `sameShape` candidates, so there were simply more pairs. The rule since:
no per-call cost is quoted from fewer than five repetitions in one process,
and any relative claim comes from steady-state loops on both sides.

## Sweeps in a bounded environment

A full sweep costs 105 runs at 2 to 4 seconds each, past any single
wall-clock budget in the environments these experiments run in, so
`python/experiment_chunked.py` splits by held-out task and applies two rules
learned the expensive way.

Results are flushed to a JSON-lines file after every pair, never batched at
the end. An early version batched, and a run cut off after finishing all its
work but before the final write lost the whole chunk silently, with the
printed output looking complete; only cross-checking the file's row count
against the printed lines revealed the gap. And chunks are resumable, pairs
already present in the output file are skipped, so a partial chunk continues
rather than restarts. Neither rule is MeTTa-specific; they apply to any long
computation under a wall clock.

## Living with the interpreter

Living with the interpreter

Two upstream issues shaped how the sweeps run, both documented in the log with minimal reproductions. The first was an interpreter crash when querying a sufficiently large trie. The upstream investigation traced this to a TrieKey::value() decoding bug that becomes visible beyond the 1024-key boundary; the original report and reproduction are recorded in Hyperon issue #1076 ([https://github.com/trueagi-io/hyperon-experimental/issues/1076](https://github.com/trueagi-io/hyperon-experimental/issues/1076)), and the proposed fix is in PR #1081 ([https://github.com/trueagi-io/hyperon-experimental/pull/1081](https://github.com/trueagi-io/hyperon-experimental/pull/1081)). The fix includes regression tests and reproduces the original workload successfully, but the pull request remains open, so the workaround remains in place as defensive practice.

Separately, each MeTTa() instantiation leaked several megabytes. Neither “fresh runtime per call” nor “one runtime forever” was safe at sweep scale, which is why the pipeline keeps a persistent runtime for pure blending and a periodically recycled one for coherence checking, and why coherence runs against small per-grid spaces. The interpreter workaround is deliberately conservative: coherence runtimes are recycled every 50 uses, well before the 300–600 uses where the crash was observed.

The episode set a norm: a workaround is labelled as a workaround in the code, the upstream report is part of the fix, and the safety margin is stated rather than hidden.

## The log is the method

Everything cited in these chapters as D-something lives in
`docs/decisions.md`, written under three rules. Entries are append-only, and
a reversed decision gets a new entry rather than an edit, so the record shows
what was believed when. Corrections are entries too: the symbol-count crash
was first recorded with the wrong mechanism, and the correction notice states
what was wrong, how it was caught, and that the practical response survived
unchanged. And entries carry their numbers, so a claim like "the fix is
purely additive" appears with the measurement that established it, a diff of
old against new encoder output over 4,000 grids showing atoms added and none
removed, which is what bounded how much re-running the fix required.

The log exists so the milestone report's methods section is an editing job
over evidence written down at the time. These chapters were drafted the same
way, from the log and from traces, and where they cite a number, the log
entry behind it says how it was measured.

[Contents](../index.md)
