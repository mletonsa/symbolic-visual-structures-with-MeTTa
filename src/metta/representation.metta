; ---------------------------------------------------------------------------
; representation.metta
;
; Vocabulary and derivation rules for encoding ARC-style grids as hypergraphs
; in the Atomspace. Ground facts (cell, coord, color, adj, object, ...) are
; produced by python/encoder.py and added to the space directly; this file
; only defines TYPES for those predicates and a small number of DERIVED
; rules that are cheap enough to compute inside MeTTa itself.
;
; Design rule (see docs/decisions.md): cell-level atoms exist for inspection
; and as the substrate object-level facts are derived from, but blending
; (representation.metta's sibling, blend.metta) operates on object-level
; atoms and above. This keeps individual task hypergraphs small (roughly
; 10-20 objects for a typical ARC grid, vs. hundreds of cells).
; ---------------------------------------------------------------------------

; --- Types -------------------------------------------------------------

(: Cell Type)
(: Object Type)
(: Coord Type)
(: Color Type)
(: Task Type)
(: Grid Type)
(: Dir Type)
(: Axis Type)

(: C (-> Number Number Coord))

; Cell-level ground predicates (emitted by the encoder)
(: cell (-> Task Grid Cell Type))          ; used as (cell t g c) : membership fact
(: coord (-> Cell Coord Type))
(: color (-> Cell Color Type))
(: adj (-> Cell Cell Dir Type))

; Object-level ground predicates (emitted by the encoder)
(: object (-> Task Grid Object Type))
(: member (-> Object Cell Type))
(: objColor (-> Object Color Type))
(: size (-> Object Number Type))
(: bbox (-> Object Coord Coord Type))
(: shape (-> Object Atom Type))            ; Atom = normalized offset-signature
(: holes (-> Object Number Type))

; Object-relation predicates (emitted by the encoder; some may also be
; derivable, kept as ground facts for performance since they are used
; heavily as blending anchors)
(: sameShape (-> Object Object Type))
(: sameColor (-> Object Object Type))
(: contains (-> Object Object Type))
(: alignedRow (-> Object Object Type))
(: alignedCol (-> Object Object Type))
(: symmetric (-> Object Axis Type))
(: gridSymmetric (-> Task Grid Axis Type))

; Emitted instead of the pairwise object-relation set when a grid's
; object count exceeds the encoder's max_pairwise_objects cap (see
; encoder.py; motivated by an empirically observed O(n^2) blowup on
; scattered-noise ARC grids). Downstream stages should treat a task
; carrying this flag as needing a coarser representation, not as a bug.
(: tooManyObjects (-> Task Grid Number Type))

; --- Directions and axes (closed vocabularies) --------------------------

(: up Dir) (: down Dir) (: left Dir) (: right Dir)
(: h Axis) (: v Axis) (: d1 Axis) (: d2 Axis) (: rot90 Axis) (: rot180 Axis)

; --- Derived rules -------------------------------------------------------
; These are cheap, purely relational derivations left inside MeTTa so that
; downstream blend patterns can rely on them without the encoder having to
; precompute every closure. Anything expensive (bbox containment search,
; shape signature comparison across the whole corpus) stays in Python.

; Symmetric relation: adjacency is not inherently symmetric in the encoder
; output (only the canonical direction is emitted per pair), so derive the
; reverse here rather than doubling the fact count on disk.
(= (opposite up) down)
(= (opposite down) up)
(= (opposite left) right)
(= (opposite right) left)

; (adjSym $a $b $d) derives the direction from $a to $b when only the
; reverse edge ($b -> $a) was stored as a ground fact. Note the query
; inside deliberately looks up (adj $b $a $d0) - the STORED direction -
; and returns (opposite $d0), the direction as seen from $a; looking up
; (adj $a $b ...) here would just re-find the case where the forward
; edge already exists, which is not the case this rule is for.
(= (adjSym $a $b $d)
   (match &self (adj $b $a $d0) (opposite $d0)))

; Same-color adjacency: the canonical "toy" blend target used in
; tests/test_blend_smoke.py, kept here as a worked example of a
; single-scope blend of (adj) and (color).
(= (sameColorAdjacent $x $y)
   (match &self
     (, (adj $x $y $d) (color $x $c) (color $y $c))
     (SameColorAdjacency $x $y $c)))

; Utility: list all objects belonging to a given task/grid.
(= (objectsOf $t $g)
   (match &self (object $t $g $o) $o))

; Utility: retrieve an object's full ground-fact bundle (used by pretty.py
; via the Python API's `run` to sanity-check what a subgraph query pulled).
(= (bundleOf $o)
   (match &self
     (, (objColor $o $c) (size $o $n) (bbox $o $p1 $p2))
     (Bundle $o $c $n $p1 $p2)))
