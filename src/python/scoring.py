"""
scoring.py

Stage 5 (scoring) of the blending pipeline, per the research plan's MDL
formula: DL(atom) = (arity + 1) * log2(|symbols|), a uniform code over
a fixed symbol vocabulary. This module computes the actual compression
gain from adding a blend to a concept library, rather than relying on
raw match count alone (which the InsideOutside leave-one-out sweep
already showed varies hugely by source pair - see
docs/decisions.md D9 - without telling you WHY one pair is better).

Scope note: this is the MDL objective applied to individual blends
found already (Sprint B's output), not yet the full iterated
library-learning loop (extract -> score -> accept -> re-encode -> repeat)
the plan describes for Milestone 3. That loop needs a real concept
library data structure and a corpus-rewriting step, neither built yet -
this module is the scoring primitive that loop will call.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


def _atom_arity(atom_str: str) -> int:
    """Counts an atom's top-level argument count from its MeTTa string
    form, e.g. "(contains X Y)" -> 2, "(objColor X blue)" -> 2. Depth-1
    tokenization only (doesn't recurse into nested args like shape
    signatures) since arity for the DL formula means the relation's own
    argument count, not the total symbol count of a nested value."""
    inner = atom_str.strip()
    assert inner.startswith("(") and inner.endswith(")")
    inner = inner[1:-1].strip()
    depth = 0
    args = []
    current = ""
    for ch in inner:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
        elif ch == " " and depth == 0:
            if current:
                args.append(current)
                current = ""
        else:
            current += ch
    if current:
        args.append(current)
    return max(len(args) - 1, 0)  # first token is the predicate, not an argument


def dl_of_atom(atom_str: str, symbol_vocab_size: int) -> float:
    """DL(atom) = (arity + 1) * log2(|symbols|) - the plan's formula.
    The "+1" accounts for the predicate symbol itself, in addition to
    its arguments."""
    arity = _atom_arity(atom_str)
    return (arity + 1) * math.log2(max(symbol_vocab_size, 2))


def split_pattern_atoms(pattern_atoms_str: str) -> list:
    """Splits a materialized pattern's atom-list string (e.g.
    "((contains X Y) (objColor X blue) ...)") into individual atom
    strings, depth-aware (so nested atoms like "(shape X (a b))" are
    not split in the middle)."""
    s = pattern_atoms_str.strip()
    assert s.startswith("(") and s.endswith(")")
    inner = s[1:-1]
    atoms, depth, current = [], 0, ""
    for ch in inner:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth -= 1
            current += ch
            if depth == 0:
                atoms.append(current.strip())
                current = ""
        elif depth > 0 or ch != " ":
            current += ch
    return [a for a in atoms if a]


@dataclass
class MDLResult:
    n_matches: int
    dl_definition: float       # one-time cost of the concept's own definition
    dl_raw_per_instance: float  # cost of encoding one instance WITHOUT the concept
    dl_rewritten_per_instance: float  # cost of one concept-instance atom WITH the concept
    dl_gain: float             # total bits saved across all matched instances

    @property
    def worth_it(self) -> bool:
        return self.dl_gain > 0


def mdl_gain(pattern_atoms_str: str, n_matches: int, symbol_vocab_size: int) -> MDLResult:
    """Computes the MDL gain from adding this blend as a library
    concept, given how many held-out instances it matched.

    Without the concept: every matching instance must be encoded as its
    full set of raw atoms (dl_raw_per_instance = sum of DL over all
    atoms in the pattern).

    With the concept: the concept's OWN definition is paid once
    (dl_definition = same sum, since the definition IS the pattern
    itself - the concept's cost is not free, unlike a naive MDL
    implementation might assume), and each matching instance is
    rewritten to a single `(concept <bindings>)` atom whose arity is
    the number of free variables in the pattern (dl_rewritten_per_instance).

    Gain = (n_matches * dl_raw_per_instance) -
           (dl_definition + n_matches * dl_rewritten_per_instance)

    A blend that only matches its own 2 source instances (n_matches<=2,
    i.e. it does not generalize beyond what built it) will essentially
    always have negative gain, since the one-time definition cost isn't
    amortized over enough instances - this is a deliberate, honest
    property of MDL scoring, not a bug to fix: a concept that doesn't
    generalize SHOULD score poorly.
    """
    atoms = split_pattern_atoms(pattern_atoms_str)
    dl_raw = sum(dl_of_atom(a, symbol_vocab_size) for a in atoms)
    free_vars = len(set(re.findall(r"\$[A-Za-z0-9_#]+", pattern_atoms_str)))
    # +2 for the object-role bindings themselves (X, Y), +1 for the
    # concept-instance predicate symbol
    rewritten_arity = free_vars + 2
    dl_rewritten = (rewritten_arity + 1) * math.log2(max(symbol_vocab_size, 2))

    dl_definition = dl_raw  # the definition IS the pattern, paid once
    gain = (n_matches * dl_raw) - (dl_definition + n_matches * dl_rewritten)

    return MDLResult(
        n_matches=n_matches,
        dl_definition=dl_definition,
        dl_raw_per_instance=dl_raw,
        dl_rewritten_per_instance=dl_rewritten,
        dl_gain=gain,
    )
