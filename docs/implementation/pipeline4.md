[Contents](../index.md) · Previous: [Choosing pairs](pipeline3.md) · Next: [Building the blend](pipeline5.md)

# How the pipeline works, 4: the generic space

Stage 3 answers one question: what do the two chosen candidates have in
common? In blending terms the answer is called the generic space, and it is
computed by anti-unification, the operation the 1D pages introduced on small
examples. Values that agree survive; values that disagree generalise.

The entry point is `antiunifyPair` in `metta/antiunify.metta`. Its equation
head does the first piece of work by itself:

```metta
(= (antiunifyPair (Candidate $rel ...) (Candidate $rel ...)) ...)
```

Both inputs must bind the same `$rel` for the equation to fire at all, so
same-relation pairing is enforced by pattern matching rather than by a check.

Each scalar slot then goes through `genOrDrop`: if the two values are equal
the slot stays a ground invariant, tagged `(Fixed <value>)`; if they differ it
generalises, tagged `(Generalized <name>)` with a fixed per-slot name. Fixed
names are enough because the schema has exactly one atom per slot, which is
one of the simplifications the fixed candidate shape bought.

Symmetry sets are handled differently, by intersection rather than
comparison. "Both instances are h-symmetric" is a meaningful shared fact even
when the full symmetry groups differ, so the generic space keeps the axes
present in both.

## The generic space of this run's pair

Candidate A was a red 20-cell frame containing a blue single cell. Candidate B
was a blue 38-cell frame containing a green 20-cell frame. `antiunifyPair`
returns:

```metta
(GenericSpace contains
  (ColorX (Generalized colX)) (ColorY (Generalized colY))
  (SizeX  (Generalized szX))  (SizeY  (Generalized szY))
  (ShapeX (Generalized shX))  (ShapeY (Generalized shY))
  (SymX (h rot180 v))
  (SymY (d1 d2 h rot180 rot90 v)))
```

Every scalar slot generalised, which is what a zero-coincidence pair
guarantees, since no slot agreed. What survives as shared structure is the
anchor relation itself, the fact that both outer objects are symmetric under
`h`, `v` and `rot180` (A's frame had all six axes, B's had those three, and
the intersection keeps what both have), and the inner objects' full shared
symmetry.

Read as a concept, the generic space says: something contains something, and
the container has at least mirror and half-turn symmetry. That is recognisably
a first draft of "a symmetric container", and it fell out of comparing two
examples.

A degeneracy check (`isDegenerate`) flags the opposite outcome, a generic
space with no generalised slots at all, which means the two inputs were
identical up to relabeling and the blend would just restate one of them.

## Two language notes

Implementing this surfaced two MeTTa behaviours that cost real debugging time
and are worth knowing before reading the source. Grounded standard-library
functions such as `union-atom` do not reduce when nested directly inside
another grounded call, so the code threads intermediate results through
`let*`. And bare `=` equations have no most-specific-match priority, so a
wildcard fallback equation fires alongside the specific case rather than
instead of it; the code uses mutually exclusive constructors instead. Both are
documented with tests in the decisions log (D7).

Next: [Building the blend](pipeline5.md)
