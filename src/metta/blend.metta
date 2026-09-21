; ---------------------------------------------------------------------
; blend.metta
;
; Stage 4 (blend construction) of the pipeline. Takes a GenericSpace
; (from antiunify.metta) and the two source Candidates it came from,
; and produces:
;
;   1. A materialized PATTERN - a real, executable MeTTa pattern with
;      genuine fresh variables for generalized slots and ground
;      constants for invariant slots. This is what Stage 5's coherence
;      check would match against held-out data (see
;      docs/decisions.md D6 for why that matching must stay scoped to
;      small per-task spaces, not the shared corpus space).
;
;   2. A selective-projection enrichment of the symmetry slots: the
;      GENERIC space kept only the INTERSECTION of each object's
;      symmetry axes (the invariant core); the BLEND additionally
;      offers the UNION (axes seen in EITHER instance) as optional
;      enriched structure. This is a modest, honest reading of the
;      plan's "selective projection of non-corresponding atoms into the
;      blend" - not a claim of emergent structure beyond a set union.
;      Genuine emergent completion (new facts entailed by combining
;      projected atoms via representation.metta's derivation rules,
;      e.g. adjSym) is not attempted here; see docs/decisions.md D8.
; ---------------------------------------------------------------------

; materialize: turns a single Fixed/Generalized-tagged slot into either
; the ground constant or a genuine fresh MeTTa pattern variable.
;
; IMPORTANT MeTTa-specific gotcha #3 (see decisions.md D7): there is no
; "construct a variable from a symbol at runtime" primitive in MeTTa
; (no gensym-from-string). A first draft tried `(materializeSlot
; (Generalized $name)) -> (var $name)`, hoping to build a variable
; dynamically from whatever symbol name arrived - `var` is not a real
; MeTTa construct and this just produces a useless literal `(var colX)`
; term, not a usable pattern variable. Fixed by exploiting that there
; are only 6 known, FIXED slot names (colX, colY, szX, szY, shX, shY):
; one small equation per slot, each writing the real $variable directly
; in the equation body (e.g. `$colX`), which IS a genuine fresh pattern
; variable for that equation's own scope. Not general, but correct -
; and there is nothing to generalize to without a gensym primitive this
; package doesn't have.
(= (matColorX (Fixed $v)) $v)
(= (matColorX (Generalized colX)) $colX)
(= (matColorY (Fixed $v)) $v)
(= (matColorY (Generalized colY)) $colY)
(= (matSizeX (Fixed $v)) $v)
(= (matSizeX (Generalized szX)) $szX)
(= (matSizeY (Fixed $v)) $v)
(= (matSizeY (Generalized szY)) $szY)
(= (matShapeX (Fixed $v)) $v)
(= (matShapeX (Generalized shX)) $shX)
(= (matShapeY (Fixed $v)) $v)
(= (matShapeY (Generalized shY)) $shY)

; materializePattern: the Stage 4 entry point. Produces a list of atoms
; usable as a MeTTa pattern (each element already in the representation
; vocabulary's shape - object-role placeholders X and Y are left as the
; literal symbols X/Y, matching representation.metta's convention of
; using object identifiers as plain symbols; a caller wanting to MATCH
; this pattern against a populated space substitutes X/Y for real $
; variables at that point, e.g. via blendToQueryPattern in enumerate
; harness code, kept in Python since it is pure string substitution).
;
; Note: user-defined equations (matColorX etc.) DO auto-reduce when
; nested directly inside a literal tuple constructor - unlike grounded
; stdlib functions (union-atom etc., see the module-level note above),
; which is why this uses direct nesting rather than a let* wrapper. Also
; note: the resulting variable for a generalized slot is a genuine,
; freely-matchable MeTTa variable, but MeTTa alpha-renames it internally
; (e.g. to something like `$X#57`, not literally `$colX`) - do not rely
; on the exact variable name surviving through evaluation, only on it
; being a variable at all.
(= (materializePattern (GenericSpace $rel
                          (ColorX $cx) (ColorY $cy)
                          (SizeX $sx) (SizeY $sy)
                          (ShapeX $shx) (ShapeY $shy)
                          (SymX $symx) (SymY $symy)))
   ( ($rel X Y)
     (objColor X (matColorX $cx)) (objColor Y (matColorY $cy))
     (size X (matSizeX $sx)) (size Y (matSizeY $sy))
     (shape X (matShapeX $shx)) (shape Y (matShapeY $shy)) ))

; blendSymmetryEnrichment: the union of both instances' symmetry axes
; per object-slot, deduplicated. This is the "extra, non-invariant
; structure" the blend offers beyond the generic space's intersection -
; it is NOT asserted as always-true (unlike the intersection, which
; genuinely is invariant across both instances) but reported as
; "axes seen across this concept's instances so far," useful as a
; hypothesis for further instances to confirm or refute.
(= (blendSymmetryEnrichment (Candidate $r1 $c1x $c1y $s1x $s1y $sh1x $sh1y $sym1x $sym1y)
                             (Candidate $r2 $c2x $c2y $s2x $s2y $sh2x $sh2y $sym2x $sym2y))
   (let* (($ux (union-atom $sym1x $sym2x))
          ($uy (union-atom $sym1y $sym2y))
          ($uux (unique-atom $ux))
          ($uuy (unique-atom $uy)))
     (SymmetryUnion X $uux Y $uuy)))

; A full Blend bundles the materialized pattern with the enrichment and
; the provenance of which relation it came from, for inspection/logging.
(= (buildBlend $c1 $c2)
   (let* (($generic (antiunifyPair $c1 $c2))
          ($pattern (materializePattern $generic))
          ($enrichment (blendSymmetryEnrichment $c1 $c2))
          ($degenerate (isDegenerate $generic)))
     (Blend $pattern $enrichment $degenerate)))
