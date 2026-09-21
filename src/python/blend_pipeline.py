"""
blend_pipeline.py

Ties Stage 1 (enumerate.py candidates) to Stage 3-4 (antiunify.metta,
blend.metta) to a lightweight Stage 5 coherence check, scoped for
Sprint B's single-group validation pass.

Design choices:
- Runtime reuse + periodic recycling: defensive practice to avoid
  long-term state accumulation and keep memory footprint bounded.
- Per-grid coherence checking (not concatenated): each grid's atoms
  are loaded into a separate space, keeping distinct symbol counts
  predictably low and maintaining semantic separation ("does it match
  THIS grid?" vs. "does it match somewhere in a blob of unrelated grids").
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from encoder import load_into_space  # noqa: E402
from hyperon import MeTTa  # noqa: E402

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
METTA_FILES = ["antiunify.metta", "blend.metta"]


def blending_metta() -> MeTTa:
    """A fresh MeTTa instance with antiunify.metta + blend.metta loaded
    (NOT representation.metta or any corpus data - this is deliberately
    a small, separate space for the blending logic itself)."""
    m = MeTTa()
    for fname in METTA_FILES:
        with open(os.path.join(REPO_ROOT, "metta", fname)) as f:
            m.run(f.read())
    return m


# ---------------------------------------------------------------
# Runtime reuse / recycling strategy
#
# Two distinct runtimes with different lifecycles:
#
# 1. _blend_runtime: persistent, never recycled.
#    Safe because buildBlend/antiunifyPair are pure computation with
#    no space mutation (no add-atom, no new-space calls).
#    Reuse avoids repeated MeTTa() instantiation overhead.
#
# 2. _coherence_runtime: recycled every RECYCLE_EVERY uses.
#    Coherence checking mutates spaces (bind!, new-space, add-atom),
#    so repeated mutations can accumulate state. Recycling periodically
#    is defensive: it bounds memory footprint and ensures clean slate,
#    even though the original Hyperon crash (expression arity limit on
#    result collapsing, not symbol count) is now fixed in the upstream
#    codebase.
#
# RECYCLE_EVERY=50 is conservative and safe for typical workloads.
RECYCLE_EVERY = 50

_blend_runtime = None       # persistent; pure computation, never recycled
_coherence_runtime = None   # recycled periodically
_coherence_use_count = 0
_coherence_space_counter = 0


def _get_blend_runtime() -> MeTTa:
    global _blend_runtime
    if _blend_runtime is None:
        _blend_runtime = blending_metta()
    return _blend_runtime


def _get_coherence_runtime() -> MeTTa:
    """Returns a MeTTa runtime for coherence checking, recycling it
    (creating a fresh one) every RECYCLE_EVERY uses - see the module
    note above for why periodic recycling is good defensive practice."""
    global _coherence_runtime, _coherence_use_count
    if _coherence_runtime is None or _coherence_use_count >= RECYCLE_EVERY:
        _coherence_runtime = MeTTa()
        _coherence_use_count = 0
    _coherence_use_count += 1
    return _coherence_runtime


def build_blend(candidate_a, candidate_b):
    """Runs Stage 3+4 on two Candidate objects (see enumerate.py).
    Returns (blend_result_str, is_degenerate: bool). Reuses one shared
    persistent runtime (see _get_blend_runtime) rather than creating a
    fresh MeTTa() per call - safe because this is pure computation with
    no space mutation (see module note above)."""
    m = _get_blend_runtime()
    expr = f"(buildBlend {candidate_a.to_metta()} {candidate_b.to_metta()})"
    res = m.run(f"!{expr}")
    if not res or not res[0]:
        return None, None
    blend_str = str(res[0][0])
    is_degenerate = blend_str.rstrip(")").endswith("True")
    return blend_str, is_degenerate


def _extract_pattern_atoms(blend_str: str) -> list:
    """Pulls the materialized-pattern atom list out of a `Blend(...)`
    result string. The pattern is the first element after `Blend `,
    itself a parenthesized list of atoms - this is a small, deliberately
    simple parser for OUR OWN known output shape, not a general s-expr
    parser, so it leans on the fact that `materializePattern` always
    emits exactly 7 atoms in a fixed order (see blend.metta)."""
    # Find the substring between the first '((' after 'Blend' and its
    # matching ')' that closes the whole 7-atom list - depth-counting
    # since atoms are themselves nested (e.g. "(shape X (a))").
    start = blend_str.index("((", blend_str.index("Blend"))
    depth = 0
    for i in range(start, len(blend_str)):
        if blend_str[i] == "(":
            depth += 1
        elif blend_str[i] == ")":
            depth -= 1
            if depth == 0:
                return blend_str[start:i + 1]
    raise ValueError(f"could not parse pattern atoms out of: {blend_str}")


def pattern_to_query(pattern_atoms_str: str) -> str:
    """Converts a materialized pattern's atom-list string (using the
    literal symbols X/Y for object roles) into a conjunctive MeTTa query
    usable with `match`, substituting X/Y for fresh query variables
    $qx/$qy.

    Order matters. MeTTa alpha-renames generalized-slot variables into
    tokens like `$X#7738` (see blend.metta's materializePattern
    docstring), and the '#' character is reserved in MeTTa source
    syntax, so these tokens cannot be fed back in as query text. They
    are also exactly the "longer token containing a bare X" that a
    word-boundary substitution will clobber: in `$X#7738` the X sits
    between '$' and '#', both non-word characters, so \\bX\\b matches
    it. Running the role substitution first therefore produced
    `$$qx#7738` and, after sanitising, a malformed `$$gen0`. So the
    alpha-renamed variables are replaced with clean `$genN` placeholders
    FIRST, consistently per unique token, and only then are the bare
    role symbols substituted.

    Sanitising replaces longest tokens first, so that a hash variable
    that happens to be a prefix of another (e.g. `$X#77` and `$X#778`)
    is not partially rewritten by the shorter one's replacement.
    """
    hash_vars = sorted(set(re.findall(r"\$[A-Za-z0-9_]*#[0-9]+", pattern_atoms_str)),
                       key=lambda v: (-len(v), v))
    q = pattern_atoms_str
    for i, v in enumerate(hash_vars):
        q = q.replace(v, f"$gen{i}")

    q = re.sub(r"\bX\b", "$qx", q)
    q = re.sub(r"\bY\b", "$qy", q)

    inner = q.strip()
    assert inner.startswith("(") and inner.endswith(")")
    inner = inner[1:-1].strip()
    return f"(, {inner})"


def check_coherence(pattern_atoms_str: str, held_out_atoms: list) -> list:
    """Stage 5 preview: does this blend's pattern match anything in a
    held-out grid's atoms? Uses a uniquely-named sub-space within a
    periodically-recycled shared runtime (see module note above).

    Each sub-space is kept small: a single grid's atoms, not concatenated
    across multiple grids. This maintains semantic clarity ("does it match
    in THIS grid?") and keeps distinct symbol counts predictably small."""
    global _coherence_space_counter
    query = pattern_to_query(pattern_atoms_str)
    m = _get_coherence_runtime()
    _coherence_space_counter += 1
    space_name = f"&chk{_coherence_space_counter}"
    m.run(f"!(bind! {space_name} (new-space))")
    for a in held_out_atoms:
        m.run(f"!(add-atom {space_name} {a.to_metta()})")
    free_vars = sorted(set(re.findall(r"\$[A-Za-z0-9_]+", query)))
    template = "(" + " ".join(free_vars) + ")"
    res = m.run(f"!(match {space_name} {query} {template})")
    if not res or not res[0]:
        return []
    return res[0]


def check_coherence_per_grid(pattern_atoms_str: str, grids_atoms: list) -> dict:
    """Runs check_coherence separately against each grid in
    `grids_atoms` (a list of (label, atoms) pairs). Returns a dict of
    label -> match list, so callers can see exactly which held-out
    grids the blend generalizes to and which it doesn't - the plan's
    "report negative results too" principle applies at this granularity
    as much as at the level of whole blends."""
    return {label: check_coherence(pattern_atoms_str, atoms)
            for label, atoms in grids_atoms}


def blend_and_check(candidate_a, candidate_b, held_out_grids_atoms: list):
    """Convenience wrapper: build the blend, then check it against each
    held-out grid (a list of (label, atoms) pairs - see
    check_coherence_per_grid). Returns (blend_str, is_degenerate,
    {label: matches})."""
    blend_str, is_degenerate = build_blend(candidate_a, candidate_b)
    if blend_str is None:
        return None, None, {}
    pattern_atoms = _extract_pattern_atoms(blend_str)
    matches = check_coherence_per_grid(pattern_atoms, held_out_grids_atoms)
    return blend_str, is_degenerate, matches
