; ---------------------------------------------------------------------
; antiunify.metta
;
; Stage 3 (anti-unification / generic space computation) of the
; blending pipeline, specialized to the Candidate schema produced by
; python/enumerate.py: a 2-object relational pattern (relation, color,
; size, shape per object, plus each object's symmetry-axis set).
;
; This is NOT a general graph-alignment anti-unifier - see
; docs/decisions.md D7 for the scoping rationale. Because a Candidate
; has exactly one atom per (predicate, object-slot), except `symmetric`
; (a set), anti-unification reduces to a fixed per-slot comparison
; rather than a general subgraph-alignment search over arbitrary
; relational patterns. Generalizing this to variable-length relation
; lists and a real alignment search is future work (needed for E2's
; cross-group blending, which this Sprint does not attempt).
;
; IMPORTANT MeTTa-specific gotcha, confirmed by direct testing before
; writing this file (see decisions.md D7): grounded stdlib functions
; like union-atom/intersection-atom do NOT auto-reduce when nested
; directly inside another grounded function call - e.g.
; `(unique-atom (union-atom $a $b))` returns the literal unevaluated
; expression `(union-atom $a $b)`, not the unioned-and-deduped list.
; `let*` (which evaluates each binding before the next) is required
; throughout to force intermediate reduction. This cost real debugging
; time and is exactly the kind of MeTTa-tooling-maturity finding this
; grant is meant to surface.
; ---------------------------------------------------------------------

; genOrDrop: anti-unification step for a single scalar slot (color,
; size, or a whole shape signature compared as one opaque value). If two
; instances agree, the value is an invariant of the generic space,
; kept as a ground constant (Fixed <value>). If they disagree, the slot
; generalizes - tagged (Generalized <name>) rather than bound to a
; fresh gensym, since each Candidate has exactly one atom per slot, so a
; fixed per-slot name (colX, colY, szX, szY, shX, shY) is unambiguous
; within a single antiunifyPair call.
(= (genOrDrop $a $b $name)
   (if (== $a $b) (Fixed $a) (Generalized $name)))

; antiunifyPair: the Stage 3 entry point. Two candidates anti-unify by
; virtue of sharing the same $rel - this is enforced by the head
; pattern itself (both input Candidates must bind the SAME $rel for
; this equation to fire at all), matching Stage 2's same-relation pair
; selection for this Sprint's scope.
;
; Symmetric axes are handled by intersection (the subset of axes present
; in BOTH instances) rather than genOrDrop, since they are sets, not
; scalars: "both instances are h-symmetric" is a meaningful invariant
; even when the full symmetry groups differ.
(= (antiunifyPair (Candidate $rel $c1x $c1y $s1x $s1y $sh1x $sh1y $sym1x $sym1y)
                   (Candidate $rel $c2x $c2y $s2x $s2y $sh2x $sh2y $sym2x $sym2y))
   (let* (($symX (intersection-atom $sym1x $sym2x))
          ($symY (intersection-atom $sym1y $sym2y)))
     (GenericSpace $rel
       (ColorX (genOrDrop $c1x $c2x colX))
       (ColorY (genOrDrop $c1y $c2y colY))
       (SizeX  (genOrDrop $s1x $s2x szX))
       (SizeY  (genOrDrop $s1y $s2y szY))
       (ShapeX (genOrDrop $sh1x $sh2x shX))
       (ShapeY (genOrDrop $sh1y $sh2y shY))
       (SymX $symX)
       (SymY $symY))))

; Convenience accessor used by blend.metta and by tests to check
; whether a generic space has any generalized (non-invariant) slots at
; all - a generic space that is ALL Fixed slots means the two instances
; were identical up to relabeling, which is worth flagging as a
; degenerate/uninteresting blend rather than silently accepting it.
;
; IMPORTANT MeTTa-specific gotcha #2 (see decisions.md D7): a first
; draft of this used a wildcard catch-all equation
; `(= (isDegenerate $anythingElse) False)` alongside the specific
; pattern below, expecting Prolog-style "most specific match wins."
; MeTTa's bare `=` equations have no such priority - a wildcard matches
; EVERYTHING unconditionally, so both equations fired simultaneously
; and `!(isDegenerate ...)` returned `[True, False]` for every input.
; Fixed by using mutually-exclusive constructors (Fixed vs Generalized
; genuinely don't overlap) instead of a wildcard fallback. Where a real
; wildcard fallback is unavoidable, `case` (which IS priority-ordered)
; is the correct tool, not a second bare `=` equation.
(= (slotIsFixed (Fixed $v)) True)
(= (slotIsFixed (Generalized $v)) False)

(= (isDegenerate (GenericSpace $rel
                    (ColorX $cx) (ColorY $cy)
                    (SizeX $sx) (SizeY $sy)
                    (ShapeX $shx) (ShapeY $shy)
                    (SymX $symx) (SymY $symy)))
   (let* (($a (slotIsFixed $cx)) ($b (slotIsFixed $cy))
          ($c (slotIsFixed $sx)) ($d (slotIsFixed $sy))
          ($e (slotIsFixed $shx)) ($f (slotIsFixed $shy))
          ($ab (and $a $b)) ($cd (and $c $d)) ($ef (and $e $f))
          ($abcd (and $ab $cd)))
     (and $abcd $ef)))
