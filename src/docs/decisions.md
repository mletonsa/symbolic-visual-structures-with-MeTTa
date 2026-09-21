# Design Decisions and Findings Log

This file records design decisions and empirical findings as they happen,
in the order encountered, so they can be turned into the report's methods
narrative later without reconstructing history from memory. Entries are
append-only; if a decision is later reversed, add a new entry rather than
editing the old one.

---

## Sprint A

### D1. Background color defaults to 0, not "most frequent color"

**Decision:** `GridEncoder` defaults to treating color 0 (black) as
background, matching ARC community convention. `background_rule="frequent"`
is available as an opt-in for datasets where it's known to hold.

**Why:** The initial implementation defaulted to the statistical mode of
the grid. This broke immediately on the encoder's own unit-test fixtures
(a solid 2x2 non-zero square encoded as "all background, zero objects",
since the non-zero color was the majority in a 4-cell grid). The failure
mode generalizes beyond small fixtures: any grid where the foreground
covers more area than the background defeats the frequency heuristic,
and there is no principled way to distinguish "foreground is large" from
"background is uncommon" using frequency alone. Fixed by making 0 the
default and frequency an explicit opt-in.

### D2. Pairwise object relations are capped at 60 objects per grid

**Decision:** `GridEncoder(max_pairwise_objects=60)` (default). Above the
cap, the O(n^2) pairwise relation computation (`sameShape`, `sameColor`,
`contains`, `alignedRow`, `alignedCol`) is skipped and a single
`(tooManyObjects <task> <grid> <n>)` flag atom is emitted instead.
Cell-level atoms, per-object atoms (color, size, bbox, shape, holes,
symmetry), and whole-grid symmetry are all still computed regardless.

**Why:** Found empirically, not anticipated in the abstract. Running the
uncapped encoder against the first 30 ARC-AGI training tasks produced
934,309 atoms; profiling identified ARC-AGI task `0dfd9992` (a
scattered-noise grid with 441 single-cell objects, no meaningful
adjacency structure) as responsible for ~135,000 atoms from ONE grid,
almost entirely from the pairwise relation step (441^2 ~ 194k candidate
pairs). This is exactly the bottleneck flagged in the plan's risk
section ("complexity of symbolic representations... large or unwieldy
hypergraphs") materializing on real data rather than staying
hypothetical.

**Effect of the fix**, full ARC-AGI-1 training set (400 tasks, 3,436
grids):
| Metric | Before cap | After cap |
|---|---|---|
| Max per-grid encode time | 0.71 s | 0.04 s |
| Full training set encode time | not measured (too slow to run in full) | 6.9 s |
| Errors | 0 | 0 |
| Grids hitting the cap | n/a | 117 / 3436 (3.4%) |

The 3.4% figure is itself worth reporting: it is a rough measure of how
much of ARC-AGI-1 is "scattered/noisy" enough that object-level
relational blending needs a fallback rather than a naive pairwise scan.

**Open question for Sprint C:** should capped grids be excluded from
candidate extraction entirely, or should a coarser relation set (e.g.
only spatially-local pairs, via a grid partition) be computed for them
instead of dropping relations altogether? Decision deferred; flagged
here so it isn't silently forgotten.

### D3. Footnote [^5] in the Milestone 1 plan pointed to the wrong Mini-ARC

**Finding:** The Milestone 1 research plan cites `pfletcherhill/mini-arc`
for Mini-ARC. That repository does not contain the Mini-ARC dataset - it
bundles a full copy of the standard ARC-AGI-1 training set (400 tasks,
grids up to 30x30, identical task IDs to the reference ARC-AGI corpus)
alongside the author's own tooling (an `arc-editor`, Kaggle notebooks,
RL experiments). Verified directly: max grid dimension in that repo's
`data/arc/training_challenges.json` is 30x30, and 1403/1718 grids exceed
5x5.

The actual Mini-ARC (Kim et al., 2022, "Playgrounds for Abstraction and
Reasoning," KAIST NMSL lab) is at `KSB21ST/MINI-ARC`, under
`data/MiniARC/*.json`. Verified: 149 task files (matches the count
reported in the literature, e.g. Ferré 2023's "collection of 149
miniature ARC-AGI-like tasks"), all grids confirmed 5x5 by direct
inspection of every grid in every task.

**Action:** the project's dataset fetch script (see Makefile) points to
`KSB21ST/MINI-ARC`. The Milestone 1 document's footnote should be
corrected in the next revision or in an erratum note; not fixed
retroactively here since Milestone 1 was already submitted.

### D4. Encoding time and full-corpus validation summary

All three real datasets used by this project encode cleanly with the
current implementation:

| Dataset | Tasks | Grids | Errors | Max encode time/grid | Cap hits |
|---|---|---|---|---|---|
| ARC-AGI-1 training | 400 | 3,436 | 0 | 0.042 s | 117 (3.4%) |
| ConceptARC (16 groups) | 160 | 1,814 | 0 | 0.012 s | 2 (0.1%) |
| Mini-ARC (Kim et al. 2022) | 149 | 1,354 | 0 | 0.003 s | 0 |

ConceptARC - the primary experimental dataset for E1/E2 - has a
negligible cap-hit rate, meaning the O(n^2) relation cap is very unlikely
to interfere with the concept-recovery experiments it's used for. The
cap mostly matters for the broader ARC-AGI-1 reference set, which
includes noise-heavy tasks ConceptARC was explicitly designed to avoid.

### D5. 1D-ARC has no data to download

`optozorax/arc_1d` is a Rust procedural generator (`src/main.rs`), not a
JSON corpus. Rather than compiling it in Sprint A, the encoder's 1D path
was validated with three hand-built fixtures in the style of published
1D-ARC task families (single-object move, recolor, fill-between-
endpoints; see `tests/test_1d_arc.py`). This is sufficient to confirm
what 1D-ARC is actually needed for per the plan (a lower-complexity
debugging domain using the same vocabulary, not a distinct code path) -
`n_rows == 1` requires no special-casing in `encoder.py`.

One property worth flagging for Sprint C: a 1-row object is trivially
`symmetric h` (row-flip is a no-op with one row), which carries no
information on 1D data and should be down-weighted or excluded from
candidate extraction when working on 1D-ARC fixtures specifically.

If the actual generator's task diversity becomes valuable later (e.g.
to stress-test candidate extraction on a larger 1D corpus than three
hand fixtures), compiling `optozorax/arc_1d` with `cargo build` and
dumping its output to JSON is a same-day task, not attempted here since
it wasn't necessary to validate E0.


D6. hyperon 0.2.10 crashes once a space's total distinct symbol count crosses ~1000-1050 (CORRECTED - originally mischaracterized as a match-result-count threshold; FIXED UPSTREAM)

Severity: high. Read this before writing any Stage 5 coherence/scoring code in Sprint C.

Correction notice (2026-07-29): this entry originally claimed the trigger was "match result count above ~450-500." That was wrong, and the error was caught by a good question about an incidental detail in the repro script (i // 10 grouping of the t symbol) that prompted re-testing more carefully. The corrected finding is below; the design implications for Sprint C (small, per-task spaces, not a shared corpus space) are UNCHANGED, since the practical mitigation already keeps total symbol counts small too - only the stated MECHANISM needed fixing, not the response to it.

Upstream fix status (2026-08-23): This bug has been fixed in the hyperon-experimental main branch (GitHub issue #1076). The root cause was a 2-bit packing bug in TrieKey::value() in hyperon-space/src/index/trie.rs (operator precedence: (self.0 & TK_VALUE_MASK) - TK_MAX_EXPRESSION_SIZE was being parsed as self.0 & (TK_VALUE_MASK - TK_MAX_EXPRESSION_SIZE)). The real limit is expression arity (1024 direct children per expression during result collapsing), not raw atom/symbol count. The fix is available in source; a patched pip wheel is not yet released as of this date. Workaround code in blend_pipeline.py (_blend_runtime reuse, periodic _coherence_runtime recycling) is no longer necessary for crash prevention but remains as defensive practice to bound state accumulation.

Finding: While validating that exported .metta corpus files load correctly together into one shared MeTTa space (a natural way to run cross-task candidate extraction, per the plan's Stage 1-2), loading ~20 real task files and querying !(match &self (object $t $g $o) ($t $g $o)) crashed the Python process entirely - not a catchable Python exception, a Rust panic that aborts the whole interpreter:

thread '<unnamed>' panicked at hyperon-space/src/index/trie.rs:179:71:
called `Option::unwrap()` on a `None` value
...
thread caused non-unwinding panic. aborting.

Isolated to a minimal repro (docs/bug_repro_hyperon_match_crash.py): the crash has nothing to do with this project's representation - the most trivial possible ground atoms - (object t g o) / (objColor o red), no nested structures, no domain content - reproduce it.

What the trigger actually is, established by controlled tests that vary one dimension at a time:

A match call returning up to 2000 DUPLICATE results (from a space built by cycling through only 5 distinct (t, g, o) triples 2000 times) does NOT crash. This alone refutes "match result count" as the driver - 2000 results, no crash, when the underlying symbol vocabulary is tiny.
A space with 500 iterations where t is drawn from a pool of only 5 values but g/o are unique each time (total distinct symbols ≈ 1005) does NOT crash. Reversing which argument is pooled (t unique, g/o pooled) also does NOT crash at the same scale. So it isn't tied to diversity in any ONE specific argument position either.
Pushing the SAME "t pooled at 5, g/o unique" scenario from 500 to 600 iterations (total distinct symbols ≈1005 -> ≈1205) DOES start crashing, and bisection narrowed it to between 500 and 520 iterations (≈1005 to ≈1045 distinct symbols).
The original "everything fully unique" scenario crashes between 300 and 350 iterations (≈900 to ≈1050 distinct symbols across t, g, o combined) - consistent with the same ~1000-1050 threshold measured a different way.

Conclusion: the crash is triggered by the TOTAL NUMBER OF DISTINCT SYMBOLS interned across the whole space (roughly 1000-1050 in this environment), not by match result count, not by which argument position carries the diversity, and not by whether results contain duplicates. This is consistent with the crash's own stack trace (TrieKeyStorage::get_atom_unchecked, hyperon-space/src/index/trie.rs)

a symbol-table/trie-indexing structure, which is exactly what would be sized by distinct symbol count, not match volume.

Searched trueagi-io/hyperon-experimental's GitHub issues for "TrieKeyStorage" - zero results as of 2026-07-28. This appears to be undocumented upstream. Action item: file an issue upstream with the minimal repro before Sprint C, both as due diligence and because a fix would materially de-risk Milestone 3's larger-scale experiments (E3/E4). The draft issue text (docs/DRAFT_upstream_issue.md) has been updated to reflect the corrected mechanism.

Design implication - unchanged despite the correction: any MeTTa space accumulating more than roughly 1000 distinct symbols (not "more than a few hundred match results," which was the original, wrong, framing) is unsafe to query with match. Concretely, for Sprint C:

Stage 5's coherence gate ("the blend pattern matches at least one instance in a held-out slice") is safe when scoped to one small per-grid space (tens to low hundreds of distinct symbols, nowhere near 1000) - which is exactly what blend_pipeline.check_coherence already does, for reasons that turned out to still be correct even though the original stated reason (result count) wasn't quite right.
MDL rewriting (Stage 5) and reuse counting (Stage 5), which need corpus-wide occurrence counts, should NOT be implemented as MeTTa match calls against a fully-loaded corpus space - a real corpus easily exceeds 1000 distinct symbols. This reinforces the hybrid architecture already chosen in the research plan (Section 2: "Python: candidate subgraph enumeration, MDL / novelty / reuse scoring").
Practical scoping for now: keep per-task or per-small-group MeTTa spaces (comfortably under ~1000 distinct symbols - a single ARC grid is typically tens to low hundreds) for anti-unification and blend construction (Sprint B); do corpus-wide aggregate operations (candidate frequency filtering, MDL, reuse counts) over the Python-side Atom lists that encoder.py already produces.

### D7. Sprint B scoping: 2-object fixed-relation candidates, and three MeTTa language gotchas found building it

**Scoping decision.** The research plan's general Stage 1 enumerates
arbitrary relational subgraphs (1-2 object variables, up to k relation
atoms). For Sprint B's validation pass, this was narrowed to exactly
one anchor binary relation (contains/sameColor/sameShape/alignedRow/
alignedCol) plus each endpoint's own unary properties (color, size,
shape, symmetry axes) - see `python/enumerate.py`. This is a real
scoping choice: anti-unification over this fixed schema reduces to
per-slot comparison, which is what made a working MeTTa implementation
tractable in the time available. Generalizing to variable-length
relation chains and a real graph-alignment search (needed for E2's
cross-group blending, where two patterns won't share a common schema by
construction) is real, un-started future work.

**Group choice.** ConceptARC's InsideOutside was chosen over e.g.
AboveBelow or Center because its defining concept (nesting) maps
directly onto the encoder's existing `contains` predicate - confirmed
empirically before committing to it (`contains` atoms fire on 3 of the
first 5 InsideOutside tasks inspected, with clear nested-rectangle
structure). AboveBelow and Center would need predicates the vocabulary
doesn't have yet (a directional "above" ordering, a "near-center"
predicate) - worth building when a group actually requires it.

**Result on real data.** Anti-unifying a `contains` candidate from
InsideOutside1 with one from InsideOutside4 generalized every scalar
slot (their colors, sizes, and shapes all differ) but kept the anchor
relation `(contains X Y)` and the full symmetry-axis set as invariant.
Checked for coherence against a third, completely unused task
(InsideOutside5, 12 grids) by loading each grid into its own small
space and matching: the blend matched in 8 of 12 grids. The 4 misses
were concentrated in *output* grids - a sensible negative result, since
several InsideOutside puzzles remove the containment structure as their
transformation (keep only the inner object, or only the outer one), so
a container/contained relation genuinely shouldn't be expected to
survive into every output. This is exactly the kind of registered,
explicable negative result the plan's "report negative results too"
principle asks for, found on the very first real blend attempted.

**Three MeTTa-specific gotchas found while implementing
`antiunify.metta`/`blend.metta`, each cost real debugging time:**

1. **Grounded stdlib functions (`union-atom`, `intersection-atom`, etc.)
   do not auto-reduce when nested directly inside another grounded
   function call.** `(unique-atom (union-atom $a $b))` returns the
   literal unevaluated expression `(union-atom $a $b)`, not the unioned
   list - confirmed by direct testing before relying on it. `let*`
   (which evaluates each binding in sequence before the next) fixes
   this reliably. User-defined equations (introduced via `=`), by
   contrast, DO auto-reduce when nested - this asymmetry isn't obvious
   from the outside and is worth knowing before chaining stdlib set
   operations.

2. **Bare `=` equations have no "most specific match wins" priority -
   unlike Prolog.** A wildcard catch-all equation
   `(= (isDegenerate $anythingElse) False)` alongside a specific pattern
   for the true case does not act as a fallback; MeTTa fires BOTH
   equations unconditionally for any input matching the wildcard (which
   is everything), so `!(isDegenerate ...)` returned `[True, False]`
   simultaneously for every input during development. Fixed by using
   genuinely mutually-exclusive constructors (`Fixed` vs `Generalized`
   share no overlap) instead of a wildcard fallback. Where a real
   fallback is unavoidable, `case` is the correct tool (confirmed to
   give proper priority-ordered matching) - a second bare `=` equation
   is not a substitute for it.

3. **No gensym: variables can't be constructed from a symbol at
   runtime, and MeTTa alpha-renames variables internally in a way that
   breaks round-tripping through strings.** There is no "build a fresh
   pattern variable named after this data value" primitive. Worked
   around by hardcoding the (small, fixed, known-in-advance) set of
   slot names as literal `$variable`s directly in each equation body -
   correct precisely because the schema only has 6 possible generalized
   slots, all known ahead of time; this would not scale to a schema
   with a dynamic/unbounded set of slot names. Separately: the variable
   MeTTa produces for a generalized slot gets alpha-renamed internally
   (e.g. `$colX` becomes something like `$X#4246`), and this renamed
   form contains a `#` character that MeTTa's own source-level parser
   refuses to accept (`'#' char is reserved for internal usage`) - so a
   materialized pattern's string representation cannot be fed directly
   back into a new `m.run(...)` call without first sanitizing any
   `#`-containing variable token into a clean placeholder name (see
   `blend_pipeline.pattern_to_query`). This is a real trap for any
   pipeline that treats MeTTa result strings as re-usable source text,
   which is exactly what a corpus-scale blending system needs to do
   routinely (materialize a blend, then use it as a query).

### D8. Emergent-structure detection is not yet attempted

The blend's "SymmetryUnion" enrichment (Stage 4) is a plain set union of
two instances' symmetry axes - a modest, honestly-described enrichment,
not a claim of emergent structure. Genuine emergent completion (running
`representation.metta`'s derivation rules, e.g. `adjSym`, over a
blend's projected atoms to surface a NEW fact entailed by combining them
but present in neither input alone) is real future work, not attempted
in Sprint B. The representation's current derivation rules are thin
(mainly `adjSym` and the `sameColorAdjacent` worked example), so
meaningful emergent-structure demonstrations will likely need richer
derivation rules added to `representation.metta` first.

### D9. hyperon MeTTa() instantiation leaks memory; fixed via runtime reuse + recycling; first E1-style cross-validated result

**The leak.** Separately from D6's match-crash bug, `hyperon.MeTTa()`
instantiation leaks memory: each Python-level `MeTTa()` object leaks
roughly 4-5MB that is never reclaimed, confirmed with explicit `del` +
`gc.collect()` and checking real-time (not peak) RSS via
`/proc/self/status` - `ru_maxrss` alone wouldn't distinguish a genuine
leak from ordinary peak-then-freed allocation, so this was checked the
right way before concluding it was real. Found while trying to run a
100+ check sweep across the InsideOutside group with the Sprint B
pipeline's original "fresh `MeTTa()` per call" design: the process was
OOM-killed partway through.

**Why the obvious fix doesn't fully work.** Reusing one persistent
runtime and creating isolated sub-spaces within it via
`(bind! &name (new-space))` avoids the memory leak entirely (confirmed
flat over 150 iterations) - but repeating that same pattern at larger
scale (300-600+ calls) triggers D6's crash again. With D6's corrected
mechanism (total distinct symbols, not match result count) this now has
a clean explanation rather than a shrug: each `(bind! &check{i} ...)`
call interns a NEW distinct symbol name (`&check1`, `&check2`, ...)
into the runtime, so after enough calls the runtime's own accumulated
symbol table crosses the same ~1000-1050 threshold D6 identified,
independent of what this project's code explicitly queries. So neither
"always fresh" (leaks -> OOM) nor "one runtime, never recreated"
(eventually crosses the symbol threshold and crashes) is safe on its
own at the scale a real experiment sweep needs.

**The fix actually used** (`python/blend_pipeline.py`): two runtimes
with different lifetimes, matching what each workload actually needs:
- A single persistent runtime for `antiunifyPair`/`buildBlend`, which
  never call `add-atom` or `new-space` - pure computation, confirmed
  safe (flat memory) over 2000 repeated calls with no recycling needed.
- A periodically-recycled runtime for coherence checking (which does
  add atoms and match), torn down and recreated every 50 uses -
  conservative given the crash was observed between 300 and 600 calls
  in manual testing, leaving roughly a 6-12x margin.

This is a workaround for two separate, apparently-unfixed upstream
issues, not a real fix to either - flagged as such in-code, and both
issues are candidates for the upstream report alongside D6's.

**First genuinely cross-validated result.** With the pipeline fixed,
ran a leave-one-task-out sweep over all 7 InsideOutside tasks that have
`contains` structure (3 of the group's 10 tasks - InsideOutside2, 3, 9 -
have zero `contains` atoms at all, presumably using a different
sub-concept such as scattered dot patterns rather than nesting; this
itself is worth knowing about the group before assuming "InsideOutside"
means "containment" uniformly). For each held-out task, built blends
from every pair of the OTHER 6 tasks' first `contains`-candidate (15
pairs), then checked coherence against all of the held-out task's
grids: 105 blend+check runs total (see
`docs/insideoutside_leave_one_out_sweep.txt` for the
full table, `python/experiment_insideoutside.py` to reproduce).

Results: 0% degenerate blends (different tasks' colors/sizes/shapes
essentially never coincide, so scalar generalization always engages).
Overall held-out match rate 31% (377/1200 grid checks). Splitting by
grid type confirms, with real numbers rather than a single anecdote,
the pattern noticed earlier: **input grids matched 46% (277/600),
output grids only 17% (100/600).** This is an explicable, registered
negative result, not a failure of the mechanism: many InsideOutside
puzzles remove the containment structure as their transformation (keep
only the inner object, or only the outer one), so a blend built purely
from a static `contains` relation has no reason to survive into those
outputs, and the numbers say it mostly doesn't. Per-source-pair
variance was also large (some pairs matched 14/14 held-out grids,
others 0/14), suggesting the specific pair chosen matters a lot - a
signal that Sprint C's frequency-filtered candidate pool (rather than
"first candidate per task") should measurably improve on this baseline,
which gives Sprint C a concrete number to beat rather than a vague goal.

### D10. MDL scoring implemented and applied; cross-group validation on SameDifferent; a performance red herring worth recording honestly

**MDL scoring (`python/scoring.py`).** Implements the plan's stated
formula, `DL(atom) = (arity + 1) * log2(|symbols|)`, and computes gain
from adding a blend to a library: `n_matches * dl_raw - (dl_definition
+ n_matches * dl_rewritten)`. Applied to the 105 InsideOutside blends
from D9's sweep: MDL ranking exactly tracked raw match count (top 5
blends by MDL gain were the same as top 5 by match count). This is
expected, not a bug: every candidate in this validation shares the
same 7-atom schema, so `dl_gain` is a linear function of `n_matches`
for a fixed pattern shape - MDL scoring only adds ranking information
beyond raw match count when comparing STRUCTURALLY DIFFERENT patterns
(different atom counts / arities), which this single-schema sweep
doesn't exercise. Worth stating plainly rather than overselling MDL as
already doing more than it currently can in this codebase.

A genuine formula limitation, found the same way D7's gotchas were
(write a test with an expectation, let it fail, learn something real):
the plan's simple uniform-code formula does not distinguish a ground
constant from a variable at the same argument position - arity is
identical either way. So this formula's only lever against a
non-generalizing blend is LOW MATCH COUNT, not narrowness of the
pattern itself. Measured directly: for a typical 7-atom InsideOutside
pattern, break-even is between 1 and 2 matches - a genuinely low bar.
This is exactly the "MDL sensitivity on small corpora... trivial
conjunctions dominate early rankings" risk the research plan's own risk
section anticipated, now confirmed with an actual number rather than
left as a general worry. Kept faithful to the plan's literal formula
rather than quietly adding a ground-vs-variable distinction the plan
didn't specify - worth revisiting explicitly in Sprint C if MDL is
meant to gate library acceptance on its own.

**A performance false lead, corrected before being reported as fact.**
While trying to run a full leave-one-out sweep on ConceptARC's
SameDifferent group (using `sameShape` as the anchor relation - a
different relation than InsideOutside's `contains`, to test whether the
pipeline generalizes at all beyond the one relation/group it was built
against), a first attempt timed out. An isolated single-call timing
test suggested SameDifferent was much slower per check than
InsideOutside (1.9s vs an InsideOutside baseline that looked like
~4.4s in one earlier ad-hoc measurement) - but that comparison was
wrong, and caught before being written up as a finding: both numbers
were each a SINGLE isolated call in a fresh process, dominated by
one-time runtime/stdlib loading cost, not steady-state per-check cost.
Repeating each measurement 5 times in one process gave the real
picture: InsideOutside checks steady out around **4.1s/call**,
SameDifferent checks around **1.85s/call** - SameDifferent is actually
FASTER per check, the opposite of the first (wrong) impression. The
actual reason the full 10-task SameDifferent sweep timed out is
mundane: more tasks have `sameShape` candidates than have `contains`
candidates, so the leave-one-out sweep simply has more pairs to check
(up to 360 vs InsideOutside's 105), not a per-check slowdown. Recorded
here as a caution about trusting single-call timing measurements at
all in an environment with meaningful one-time setup cost - always
measure a steady-state loop, not one call, before concluding anything
about relative performance.

**Cross-group validation result (scoped to 5 of SameDifferent's 10
tasks, to fit a reasonable runtime given the per-check cost above; see
`docs/samedifferent_sweep_5tasks.txt` and
`python/experiment_group_sweep.py --group SameDifferent --relation
sameShape --n-tasks 5`):** 30 blend+check runs, 0% degenerate, overall
held-out match rate 52% (187/360) - notably HIGHER than InsideOutside's
31%, suggesting `sameShape` may be a more robust invariant within its
group than `contains` was within InsideOutside, though 5 tasks is a
small sample for that comparison to lean on heavily. The input/output
asymmetry recurred here too: 67% on input grids vs 37% on output grids,
echoing InsideOutside's 46%/17% split closely enough to be worth a real
hypothesis rather than a coincidence - **ConceptARC transformations may
generally disrupt whatever static relational invariant a task's input
grids share, as a general property of the benchmark's puzzle design,
not something specific to containment or shape-sameness.** This is
exactly the kind of finding that's easy to only notice with a second
group to compare against, and is worth checking against a third and
fourth group in Sprint C before treating it as established rather than
suggestive.

### D11. Diversity-based pair selection (free, no MeTTa) nearly doubles held-out match rate

**The question.** All of Sprint B/C's validation so far used "each
task's first matching candidate" for pairing, arbitrarily. The large
pair-to-pair variance already observed (some pairs matched 14/14
held-out grids, others 0/14) suggested smarter selection should help -
but exhaustive pair search is expensive (~2-4s per MeTTa blend+coherence
check), so the right first move was a small, cheap controlled
experiment before building general search infrastructure.

**The mechanism, found by inspecting actual materialized patterns.** A
4x4 grid of InsideOutside1 x InsideOutside6 candidate pairs, checked
against held-out InsideOutside5, showed a striking pattern: one
candidate (`c6[0]`) scored well paired with anything (7/12, 3/12, 3/12),
while three others (`c6[2,4,6]`) scored 0/12 regardless of partner.
Comparing the actual materialized blend patterns explained it exactly:
the good pair generalized EVERY scalar slot (all six became variables -
the maximally general `(contains X Y)` pattern with no color/size/shape
constraint at all), while the bad pairs shared a coincidental exact
match on `size Y` and `shape Y` (both had a single-cell inner object -
and every single-cell object normalizes to the IDENTICAL shape
signature `((0,0))`, regardless of task, color, or position, since
there's only one way to represent one cell). Anti-unification correctly
treated that coincidence as an invariant, but it was never a meaningful
one - it over-narrowed the blend to require an exact single-cell inner
object, which most containment instances aren't. This is the same
"trivial conjunctions dominate early rankings" risk the plan's own risk
section anticipated for MDL, showing up here in coherence matching.

**A cheap, validated fix.** `enumerate.n_coincidental_fixed_slots(c1, c2)`
counts how many of the 6 scalar slots happen to be exactly equal between
two candidates - computable in pure Python from already-extracted
candidate data, zero MeTTa calls. In the 16-pair grid this was checked
against, it correlated almost perfectly with held-out match count: 0
coincidental matches -> 7/12; 1 -> 3/12; 2 or 3 -> always 0/12,
monotonic with no exceptions. `select_most_diverse_pair` picks the pair
minimizing this score.

**Validated at full scale, not just the one 4x4 grid it was discovered
in.** Re-ran the complete 105-check InsideOutside leave-one-out sweep
(same 7 held-out tasks, same candidate pools, only the pair SELECTED
from each pool changed) using `select_most_diverse_pair` instead of
"first candidate." Results, compared directly to the established
baseline (`docs/insideoutside_leave_one_out_sweep.txt` vs
`docs/insideoutside_diverse_strategy_sweep.txt`):

| | first-candidate (baseline) | diverse-pair |
|---|---|---|
| Overall match rate | 31% (377/1200) | **54% (654/1200)** |
| Input grids | 46% (277/600) | **81% (486/600)** |
| Output grids | 17% (100/600) | **28% (168/600)** |
| Complete-failure pairs (0 matches) | not tracked at this granularity | 5/105 |
| Degenerate blends | 0 | 0 |

Input-grid match rate nearly doubled (46% -> 81%), and this cost
NOTHING extra in MeTTa calls - it's the identical 105 blend+coherence
checks, just smarter (free) candidate selection feeding into them. This
is a genuine, validated Sprint C improvement, not a single-example
anecdote: it held up across the full leave-one-out sweep, not just the
4x4 grid where the mechanism was first noticed.

**Practical note on running large sweeps in this environment.** The
full 105-check sweep exceeds a single tool-call's wall-clock budget
(~100-120s here, vs ~2-4s/check * 105 ≈ 300-400s needed). Chunked it by
held-out task (`python/experiment_chunked.py`, 15 checks per chunk,
~60-90s each) with results written and flushed to a JSON-lines file
incrementally after EVERY pair, not batched at the end - an earlier
version of this script batched writes at the end and silently lost an
entire chunk's results when a run got cut off by the wall-clock limit
after finishing all its work but before the final write. Also added
resumability (skip pairs already present in the output file) so a
partially-completed chunk can continue rather than restart. Neither of
these is specific to MeTTa or this project - they're generic lessons
for running any long computation in bounded-wall-clock chunks - but
worth having written down since it cost real debugging time to notice
the silent data loss (the chunk's own printed output looked complete;
only cross-checking the file's actual row count against the printed
line count revealed the gap).

**Not yet done:** this validates the heuristic on ONE group
(InsideOutside). Whether it generalizes as cleanly to SameDifferent or
other groups, and whether a more principled version (e.g. weighting
which slots matter more, or accounting for how RARE a coincidental
match actually is across the corpus - size=1 is common, a specific
large shape being shared would be a much stronger and more meaningful
signal) improves further, is real next-step work, not yet attempted.

### D12. Diversity heuristic confirmed on a second group; a real MDL-ranking subtlety worth understanding

**Cross-group validation.** Reran the same diverse-pair-selection
strategy on ConceptARC's SameDifferent group (`sameShape` relation, a
genuinely different relation than InsideOutside's `contains`), same
5-task scope as the existing `docs/samedifferent_sweep_5tasks.txt`
baseline for a fair comparison:

| | first-candidate (baseline) | diverse-pair |
|---|---|---|
| Overall match rate | 52% (187/360) | **77% (276/360)** |
| Input grids | 67% | **97%** |
| Output grids | 37% | **57%** |

Input-grid match rate reached 97% - essentially every input grid's
same-shape structure was recovered. This is not a one-group fluke: D11
was found on `contains`/InsideOutside and holds up cleanly on a
different relation and group, which is a meaningfully stronger claim
than either result alone. See
`docs/samedifferent_diverse_strategy_sweep.txt`.

**A subtlety in the MDL ranking output, worth understanding rather than
mistaking for a bug.** In this SameDifferent run, the "top 3 blends by
MDL gain" all matched only 6/12 held-out grids, while the "bottom 3 by
MDL gain" matched 12/12 - MDL gain and grid-match-rate are NOT ranking
the same thing, and that's by design once noticed, not a contradiction.
`mdl_gain` is computed from `total_match_instances` (every individual
matching object-pair found across all grids, summed), not from
`n_matched` (how many grids had AT LEAST ONE match). A pattern that
matches fewer GRIDS but finds MANY matching pairs WITHIN each of those
grids (plausible for `sameShape`, where a single grid can contain
several same-shaped object pairs at once) can rack up a higher total
instance count than a pattern matching every grid but only one pair
each. Both metrics are legitimate and answer different questions -
"how many grids does this generalize to" vs "how much redundant
structure would this concept compress away" - but reporting only one of
them without the other would be misleading. Worth surfacing both
explicitly in any future scoring/ranking output rather than picking one
as "the" quality score.
