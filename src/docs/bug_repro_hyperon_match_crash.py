"""
bug_repro_hyperon_match_crash.py

Minimal reproduction of a crash found while validating the exported
MeTTa corpus (see docs/decisions.md, D6 - READ THE CORRECTION NOTICE AT
THE TOP OF THAT ENTRY). Not part of the test suite - this script is
EXPECTED to crash the Python process (Rust panic -> abort, not a
catchable exception). Run manually if you want to see it yourself:

    python3 docs/bug_repro_hyperon_match_crash.py

Summary (corrected 2026-07-29 - see docs/decisions.md D6 for the full
account of how the original version of this file was wrong): the crash
is triggered by the TOTAL NUMBER OF DISTINCT SYMBOLS interned across a
MeTTa space (roughly 1000-1050 in this environment) - NOT by `match`
result count, as an earlier version of this file and D6 claimed.
Confirmed directly: a `match` call returning 2000 (duplicate) results
from a space built with only 5 distinct symbols does NOT crash, while a
space with ~1045 distinct symbols crashes even when the match itself
returns very few results. There is no `i // 10`-style grouping in this
version deliberately, since an earlier version had it and a reasonable
question ("why is that there, does it crash without it?") is what
prompted re-testing this claim properly in the first place - every
symbol below is fully unique, and that's what makes the distinct-symbol
count easy to reason about directly (2 new distinct symbols added per
iteration, N iterations -> 2N distinct symbols, ignoring the small fixed
set of predicate names and "red").

No matching issue found in trueagi-io/hyperon-experimental's GitHub
issue tracker as of 2026-07-28 (searched for "TrieKeyStorage", zero
results) - this appears to be undocumented upstream.
"""

from hyperon import MeTTa

N = 341  # crashes (approx. 1100 distinct symbols); try N=450 (approx. 900) to see it NOT crash

m = MeTTa()
for i in range(N):
    m.run(f"(object t{i} g{i} o{i})")   # 2 new distinct symbols per iteration (g{i}, o{i});
    m.run(f"(objColor o{i} red)")       # t{i} is a 3rd, all fully unique - no pooling/grouping

print(f"Loaded {N * 2} atoms ({2*N} distinct t/g/o symbols) without incident.")
res = m.run("!(match &self (object $t $g $o) ($t $g $o))")
print(f"This line should not print at N={N}: matched "
      f"{len(res[0]) if res else 0} results.")
