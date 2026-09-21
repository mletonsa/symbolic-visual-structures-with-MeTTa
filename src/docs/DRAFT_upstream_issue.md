# Draft issue for trueagi-io/hyperon-experimental

Not filed automatically - I don't have write/auth access to GitHub.
Copy the content below into a new issue at
https://github.com/trueagi-io/hyperon-experimental/issues/new if you'd
like to report it. Searched existing issues for "TrieKeyStorage" first
(zero results, 2026-07-28), so this looks unreported.

-------------------------------------------------------------------------

**Title:** `match` against a grounding space panics/aborts the process
once the space's total distinct symbol count crosses ~1000-1050

**Body:**

`hyperon` 0.2.10 (Python package, installed via `pip install hyperon`).

Calling `!(match &self <pattern> <template>)` against a space whose
TOTAL DISTINCT SYMBOL COUNT (not match result count - see below) has
crossed roughly 1000-1050 crashes the process with an unrecoverable
Rust panic (not a catchable Python exception - the process aborts):

```
thread '<unnamed>' panicked at hyperon-space/src/index/trie.rs:179:71:
called `Option::unwrap()` on a `None` value
...
thread 'main' panicked at library/core/src/panicking.rs:225:5:
panic in a function that cannot unwind
...
thread caused non-unwinding panic. aborting.
```

Minimal reproduction (no domain-specific content - trivial ground atoms
only, every symbol fully unique so distinct-symbol count is easy to
reason about: 2 new symbols per iteration, N iterations -> 2N distinct
symbols):

```python
from hyperon import MeTTa

N = 550  # crashes reliably (~1100 distinct symbols); N=450 (~900) does not

m = MeTTa()
for i in range(N):
    m.run(f"(object t{i} g{i} o{i})")
    m.run(f"(objColor o{i} red)")

print(f"Loaded {N * 2} atoms without incident.")
res = m.run("!(match &self (object $t $g $o) ($t $g $o))")
print(f"Does not reach here at N={N}.")
```

Findings from controlled testing (single environment, Ubuntu, Python
3.12, pip package) - **the trigger is total distinct symbol count, not
match result count**, established by varying one dimension at a time:

- A `match` call returning 2000 results, ALL DUPLICATES (built by
  cycling through only 5 distinct `(t, g, o)` triples 2000 times, so
  the underlying symbol vocabulary stays tiny) does **not** crash. This
  alone rules out "match result count" as the trigger.
- A space of 500 iterations with `t` drawn from a pool of only 5 values
  but `g`/`o` unique each time (total distinct symbols ≈1005) does
  **not** crash. Reversing which argument is pooled (t unique, g/o
  pooled) also does not crash at the same scale - so it isn't tied to
  diversity in any one specific argument position either.
- Scaling that same "t pooled, g/o unique" scenario from 500 to 600
  iterations (≈1005 -> ≈1205 distinct symbols) DOES start crashing;
  bisection narrows it to between 500 and 520 iterations (≈1005 to
  ≈1045 distinct symbols).
- A fully-unique scenario (every t/g/o distinct) crashes between 300
  and 350 iterations (≈900 to ≈1050 distinct symbols total) -
  consistent with the same threshold measured a different way.
- Pure insertion with **no** `match` call does **not** crash at any
  scale tested up to 3000 iterations (6000 atoms, 6000 distinct
  symbols) - the crash is specifically triggered by the `match` query
  path itself, only once the SPACE being queried has already
  accumulated enough distinct symbols.
- Not obviously related to atom structure: reproduces with the most
  trivial possible ground atoms, and separately reproduces when loading
  real, more complex atom data (a hypergraph encoding of ARC-AGI puzzle
  grids from an unrelated project), so it does not appear specific to
  any particular atom shape - only to distinct symbol count.

This is consistent with the panic's own stack trace
(`TrieKeyStorage::get_atom_unchecked`, in
`hyperon-space/src/index/trie.rs`) - a symbol-table/trie-indexing
structure, which is exactly what would be sized by distinct symbol
count rather than match result volume.


Would appreciate a pointer to whether this is a known limitation (e.g.
a fixed-capacity buffer somewhere in the trie index) or worth a proper
bug report with more detail / a fix. Happy to provide more repro
variants if useful.

-------------------------------------------------------------------------

See docs/decisions.md (D6) and docs/bug_repro_hyperon_match_crash.py in
this repo for the fuller writeup and the exact script used to find this.

-------------------------------------------------------------------------

## Second issue: MeTTa() instantiation leaks memory

**Title:** Python `MeTTa()` instantiation leaks ~4-5MB per instance,
never reclaimed

**Body:**

Also `hyperon` 0.2.10, Python package. Repeated instantiation of
`hyperon.MeTTa()` leaks memory - confirmed with explicit `del` +
`gc.collect()` and checking real-time RSS (`/proc/self/status`,
`VmRSS`), not just peak RSS (`ru_maxrss`), which wouldn't distinguish a
genuine leak from normal allocate-then-free behavior.

```python
from hyperon import MeTTa
import gc

def current_rss_kb():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1])

for i in range(30):
    m = MeTTa()
    m.run("(foo bar)")
    del m
    gc.collect()
    if i % 5 == 0:
        print(i, "RSS KB:", current_rss_kb())
```

Output: RSS grows by ~4-5MB per iteration, linearly, with no plateau
observed up to 30 iterations, despite explicit deletion and garbage
collection each time.

Practical impact: any workload that creates many short-lived `MeTTa()`
instances (which is also the natural workaround for the `match`-crash
issue reported separately, since keeping each space small and
short-lived avoids that crash) will eventually OOM instead. Worked
around in our case by reusing one runtime for pure-computation calls
and periodically recycling (not per-call) a second runtime for calls
that mutate a space - see docs/decisions.md D9 in the same repo for the
fuller writeup.

-------------------------------------------------------------------------
