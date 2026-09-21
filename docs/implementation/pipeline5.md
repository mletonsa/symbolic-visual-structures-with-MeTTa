[Contents](../index.md) · Previous: [The generic space](pipeline4.md) · Next: [Checking the blend holds](pipeline6.md)

# How the pipeline works, 5: building the blend

Stage 4 turns the generic space into something usable: a pattern that can be
matched against grids. `buildBlend` in `metta/blend.metta` runs
anti-unification on its two inputs and materialises the result. For this
run's pair it returns:

```metta
(Blend
  ((contains X Y)
   (objColor X $X#7738) (objColor Y $X#7777)
   (size X $X#7816) (size Y $X#7855)
   (shape X $X#7894) (shape Y $X#7933))
  (SymmetryUnion X (d1 d2 h rot180 rot90 v) Y (d1 d2 h rot180 rot90 v))
  False)
```

We consider this in three parts: the pattern, an enrichment, and a degeneracy flag.

## The pattern

`materializePattern` emits exactly seven atoms in a fixed order: the anchor
relation on the roles X and Y, then colour, size and shape for each role. A
`Fixed` slot from the generic space becomes its ground value; a `Generalized`
slot becomes a variable. Here every slot generalised, so every property atom
carries a variable, and the pattern's only real constraint is
`(contains X Y)` plus the requirement that both objects have some colour,
size and shape, which every object does.

This is worth pausing on, because it is the run demonstrating something the
sweeps established statistically. The best pairs are the most diverse ones,
diverse pairs generalise every slot, and a fully generalised pattern is the
anchor relation with nothing else left. The blend that performs best is the
one that has converged back onto the encoder's own primitive. The
implications for what blending can claim to discover are taken up in the
experiment chapters; here the point is that the trace makes the phenomenon
visible in a single run.

The odd-looking variable names are MeTTa's doing: the interpreter
alpha-renames pattern variables internally, so the slot variable `$colX`
comes back as something like `$X#7738`. This matters for the next step.

## From pattern to query

A blend is only useful if it can be asked about other grids, which means
feeding its pattern back into `match`. Two obstacles sit in the way, both
consequences of round-tripping MeTTa results as text. The `#` character in
the alpha-renamed variables is reserved in MeTTa source syntax, so the
pattern string cannot be re-parsed as written. And the role symbols X and Y
are literals that need to become query variables.

`pattern_to_query` in `python/blend_pipeline.py` handles both, replacing each
`$...#N` token with a clean `$genN` placeholder first, and only then
substituting the roles, an ordering that matters because the alpha-renamed
tokens themselves contain a bare `X`. The result for this run:

```metta
(, (contains $qx $qy)
   (objColor $qx $gen0) (objColor $qy $gen1)
   (size $qx $gen2) (size $qy $gen3)
   (shape $qx $gen4) (shape $qy $gen5))
```

A conjunctive query with eight free variables, ready for Stage 5.

## The enrichment and the degeneracy flag

The `SymmetryUnion` element records the union of the two source instances'
symmetry axes for each role. It is a modest annotation carried along with the
blend, and it is deliberately not called emergent structure. Genuine
emergence, in the blending literature's sense, would be running the
representation's derivation rules over the blend's projected atoms and
surfacing a fact entailed by the combination that neither input contained.
The current derivation rules are too thin for that to produce anything
interesting, and the honest status, recorded in the decisions log (D8), is
that emergent completion is designed but not attempted.

The final `False` is the degeneracy flag from the previous stage: this blend
is not a relabeling of its inputs.

Next: [Checking the blend holds](pipeline6.md)
