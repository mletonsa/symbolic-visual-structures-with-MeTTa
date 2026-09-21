"""
encoder.py

Converts an ARC-style grid (a list of lists of small ints, 0-9) into the
ground-fact vocabulary defined in metta/representation.metta.

Design notes (see docs/decisions.md for the full rationale):
  - Every cell becomes a `cell`/`coord`/`color` atom, for inspectability.
  - Adjacency is emitted only in the canonical (right, down) directions;
    the reverse is derived inside MeTTa (`adjSym` in representation.metta)
    to avoid doubling the fact count on disk.
  - Objects are connected components of same-colored, non-background cells
    under 4-connectivity. This is the level blending actually operates on.
  - Background color defaults to 0 (black), the ARC-community convention.
    "Most frequent color" is available as an opt-in
    (`background_rule="frequent"`) but is NOT the default: it fails on
    small or foreground-dominant grids (decisions.md D1).
  - `contains` is bbox enclosure and is tested in BOTH directions. It is
    emitted only for strict enclosure, so two objects whose bboxes are
    identical produce no `contains` atom in either direction.
  - `gridSymmetric` is PATTERN-FRAME, not grid-frame: it reports whether
    the set of non-background cells is symmetric as a free-floating shape,
    normalized to its own bounding box, with position inside the grid
    quotiented out. A symmetric shape parked off-centre still counts. It
    is also colour-blind, since all non-background colours collapse into
    one offset set. Grid-frame symmetry (mirroring about the grid's own
    edges, which is what most ARC symmetry-completion tasks are about) is
    a strictly narrower relation and is deliberately NOT what this
    predicate reports.

This module has two outputs for every grid:
  1. A list of Atom objects (see `Atom` below) - a lightweight, dependency-
     free representation used by enumerate.py and scoring.py.
  2. A `.metta` text rendering (via `atoms_to_metta`) for loading into a
     MeTTa space, and a direct-to-space loader (`load_into_space`) using
     the `hyperon` Python API for encoder.py, harness.py, and tests to
     use without going through a file at all.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Iterable, Optional


COLOR_NAMES = {
    0: "black", 1: "blue", 2: "red", 3: "green", 4: "yellow",
    5: "grey", 6: "magenta", 7: "orange", 8: "cyan", 9: "maroon",
}


@dataclass(frozen=True)
class Atom:
    """A ground fact, e.g. Atom('adj', ('c0_0', 'c0_1', 'right'))."""
    predicate: str
    args: tuple

    def to_metta(self) -> str:
        def fmt(a):
            if isinstance(a, tuple):
                return "(" + " ".join(fmt(x) for x in a) + ")"
            return str(a)
        return "(" + " ".join([self.predicate] + [fmt(a) for a in self.args]) + ")"

    def __repr__(self):
        return self.to_metta()


@dataclass
class ObjectInfo:
    """Python-side bookkeeping for a connected component; not itself an
    atom, but the source ObjectInfo the encoder derives object-level atoms
    from. Exposed so enumerate.py / pretty.py can work with objects
    directly instead of re-parsing atoms."""
    oid: str
    color: int
    cells: list           # list of (row, col)
    grid_shape: tuple      # (n_rows, n_cols) of the parent grid

    @property
    def bbox(self):
        rows = [r for r, c in self.cells]
        cols = [c for r, c in self.cells]
        return (min(rows), min(cols)), (max(rows), max(cols))

    @property
    def size(self):
        return len(self.cells)

    @property
    def shape_signature(self):
        (r0, c0), _ = self.bbox
        return tuple(sorted((r - r0, c - c0) for r, c in self.cells))

    def holes(self) -> int:
        """Count background regions enclosed by (i.e. not touching the
        border of) this object's bounding box, via flood fill within the
        bbox treating this object's own cells as walls."""
        (r0, c0), (r1, c1) = self.bbox
        occupied = set(self.cells)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        visited = [[False] * w for _ in range(h)]
        holes = 0
        for sr in range(h):
            for sc in range(w):
                gr, gc = r0 + sr, c0 + sc
                if (gr, gc) in occupied or visited[sr][sc]:
                    continue
                # flood fill this background component within the bbox
                q = deque([(sr, sc)])
                visited[sr][sc] = True
                touches_border = False
                region = []
                while q:
                    cr, cc = q.popleft()
                    region.append((cr, cc))
                    if cr == 0 or cc == 0 or cr == h - 1 or cc == w - 1:
                        touches_border = True
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc]:
                            if (r0 + nr, c0 + nc) not in occupied:
                                visited[nr][nc] = True
                                q.append((nr, nc))
                if not touches_border:
                    holes += 1
        return holes


def _most_frequent_color(grid) -> int:
    """Fallback heuristic only, used when the caller explicitly asks for
    it. NOT the default background rule (see GridEncoder docstring) -
    "most frequent color" fails on small or foreground-dominant grids,
    which is common in unit-test fixtures and not unheard of in real ARC
    grids either."""
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def _connected_components(grid, background: int) -> list:
    """4-connected, same-color components over non-background cells."""
    n_rows, n_cols = len(grid), len(grid[0])
    seen = [[False] * n_cols for _ in range(n_rows)]
    comps = []
    for r in range(n_rows):
        for c in range(n_cols):
            if seen[r][c] or grid[r][c] == background:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < n_rows and 0 <= nc < n_cols
                            and not seen[nr][nc] and grid[nr][nc] == color):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append((color, cells))
    return comps


def _transform_offsets(offsets, kind):
    if kind == "h":       # flip over horizontal axis (reflect rows)
        return {(-r, c) for r, c in offsets}
    if kind == "v":       # flip over vertical axis (reflect cols)
        return {(r, -c) for r, c in offsets}
    if kind == "d1":      # transpose (main diagonal)
        return {(c, r) for r, c in offsets}
    if kind == "d2":      # anti-transpose
        return {(-c, -r) for r, c in offsets}
    if kind == "rot90":
        return {(c, -r) for r, c in offsets}
    if kind == "rot180":
        return {(-r, -c) for r, c in offsets}
    raise ValueError(kind)


def _normalize(offsets):
    r0 = min(r for r, c in offsets)
    c0 = min(c for r, c in offsets)
    return frozenset((r - r0, c - c0) for r, c in offsets)


class GridEncoder:
    """Encodes a single grid into Atom objects, given a task/grid label.

    Background rule: defaults to color 0 (black), the ARC-community
    convention, NOT "most frequent color" - frequency is unreliable on
    small or foreground-dominant grids (e.g. a grid that is entirely one
    non-zero color has no well-defined "most frequent minority"). Pass
    `background=...` to override per call, or `background_rule="frequent"`
    to opt into the frequency heuristic for corpora where it is known to
    hold (e.g. after inspecting a specific dataset's conventions).
    """

    def __init__(self, background: Optional[int] = None,
                 background_rule: str = "zero", diagonal_adj: bool = False,
                 max_pairwise_objects: int = 60):
        if background_rule not in ("zero", "frequent"):
            raise ValueError(
                f"background_rule must be 'zero' or 'frequent', got "
                f"{background_rule!r}. Previously any unrecognised value fell "
                f"through to 'zero' silently, so a typo looked like it worked."
            )
        self.background_override = background
        self.background_rule = background_rule
        self.diagonal_adj = diagonal_adj
        # Pairwise object relations (sameShape, sameColor, contains,
        # alignedRow/Col) are O(n^2) in object count. Confirmed empirically
        # on ARC-AGI training task 0dfd9992 (a scattered-noise grid with
        # 441 single-cell objects): computing them uncapped produced
        # ~135,000 atoms for ONE grid, almost entirely pairwise relations
        # among noise pixels that carry no useful blending signal. Above
        # this threshold, pairwise relations are skipped and a
        # `tooManyObjects` flag atom is emitted instead, so the encoder
        # degrades to cell/object-only output rather than stalling or
        # flooding downstream candidate enumeration with noise. Sprint C's
        # candidate-extraction step should also independently size-filter
        # tasks before enumeration; this cap is the encoder-level backstop.
        self.max_pairwise_objects = max_pairwise_objects

    def encode(self, task: str, grid_label: str, grid) -> tuple:
        """Returns (atoms: list[Atom], objects: list[ObjectInfo])."""
        atoms: list = []
        if not grid or not grid[0]:
            raise ValueError(
                f"empty grid for {task}/{grid_label}: expected a non-empty "
                f"list of non-empty rows, got {grid!r}"
            )
        n_rows, n_cols = len(grid), len(grid[0])
        if self.background_override is not None:
            background = self.background_override
        elif self.background_rule == "frequent":
            background = _most_frequent_color(grid)
        else:
            background = 0

        def cid(r, c):
            return f"{task}_{grid_label}_c{r}_{c}"

        # --- cell-level atoms (all cells, including background) ---
        for r in range(n_rows):
            for c in range(n_cols):
                cell = cid(r, c)
                atoms.append(Atom("cell", (task, grid_label, cell)))
                atoms.append(Atom("coord", (cell, ("C", r, c))))
                atoms.append(Atom("color", (cell, COLOR_NAMES.get(grid[r][c], f"c{grid[r][c]}"))))

        # --- adjacency (canonical directions only: right, down) ---
        dirs = [(0, 1, "right"), (1, 0, "down")]
        if self.diagonal_adj:
            dirs += [(1, 1, "downright"), (1, -1, "downleft")]
        for r in range(n_rows):
            for c in range(n_cols):
                for dr, dc, name in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n_rows and 0 <= nc < n_cols:
                        atoms.append(Atom("adj", (cid(r, c), cid(nr, nc), name)))

        # --- objects: connected components of non-background cells ---
        comps = _connected_components(grid, background)
        objects: list = []
        for i, (color, cells) in enumerate(comps):
            oid = f"{task}_{grid_label}_o{i}"
            obj = ObjectInfo(oid=oid, color=color, cells=cells, grid_shape=(n_rows, n_cols))
            objects.append(obj)

            atoms.append(Atom("object", (task, grid_label, oid)))
            for (r, c) in cells:
                atoms.append(Atom("member", (oid, cid(r, c))))
            atoms.append(Atom("objColor", (oid, COLOR_NAMES.get(color, f"c{color}"))))
            atoms.append(Atom("size", (oid, obj.size)))
            (r0, c0), (r1, c1) = obj.bbox
            atoms.append(Atom("bbox", (oid, ("C", r0, c0), ("C", r1, c1))))
            # shape_signature already returns a sorted tuple; do not re-sort.
            atoms.append(Atom("shape", (oid, ("Shape", obj.shape_signature))))
            n_holes = obj.holes()
            if n_holes:
                atoms.append(Atom("holes", (oid, n_holes)))

            # symmetry of the object's own cell pattern
            norm = _normalize(obj.shape_signature)
            for axis in ("h", "v", "d1", "d2", "rot90", "rot180"):
                if _normalize(_transform_offsets(set(obj.shape_signature), axis)) == norm:
                    atoms.append(Atom("symmetric", (oid, axis)))

        # --- pairwise object relations (capped, see __init__ comment) ---
        # Above the cap, a `tooManyObjects` flag atom is emitted instead
        # of the O(n^2) relation set; whole-grid symmetry (below) is still
        # computed either way since it is O(grid size), not O(n^2).
        if len(objects) > self.max_pairwise_objects:
            atoms.append(Atom("tooManyObjects", (task, grid_label, len(objects))))
        else:
            # `bbox` and `shape_signature` are recomputed properties, so
            # reading them inside the pair loop recomputes them O(n) times
            # each. Hoist once into a parallel list.
            meta = [(o.bbox, o.shape_signature, o.color) for o in objects]
            for i, a in enumerate(objects):
                (ar0, ac0), (ar1, ac1) = meta[i][0]
                for j in range(i + 1, len(objects)):
                    b = objects[j]
                    (br0, bc0), (br1, bc1) = meta[j][0]
                    if meta[i][1] == meta[j][1]:
                        atoms.append(Atom("sameShape", (a.oid, b.oid)))
                    if meta[i][2] == meta[j][2]:
                        atoms.append(Atom("sameColor", (a.oid, b.oid)))

                    # Containment is asymmetric, so BOTH orderings must be
                    # tested. The loop visits each unordered pair once, in
                    # connected-component scan order, and scan order does not
                    # track nesting: an object whose topmost row starts
                    # further left is found first even when a later object's
                    # bbox encloses it. Testing only (a encloses b) therefore
                    # dropped real containments (measured at ~23% of true
                    # bbox-containment pairs on random grids). See D13.
                    a_encloses = (ar0 <= br0 and ac0 <= bc0
                                  and ar1 >= br1 and ac1 >= bc1)
                    b_encloses = (br0 <= ar0 and bc0 <= ac0
                                  and br1 >= ar1 and bc1 >= ac1)
                    if a_encloses and not b_encloses:
                        atoms.append(Atom("contains", (a.oid, b.oid)))
                    elif b_encloses and not a_encloses:
                        atoms.append(Atom("contains", (b.oid, a.oid)))
                    # Both true means the bboxes are identical (two
                    # interlocking objects spanning the same box). Neither
                    # is nested in the other in any useful sense, so emit
                    # nothing rather than a mutual pair that would let a
                    # `contains`-anchored blend match non-nested structure.

                    if ar0 == br0 or ar1 == br1:
                        atoms.append(Atom("alignedRow", (a.oid, b.oid)))
                    if ac0 == bc0 or ac1 == bc1:
                        atoms.append(Atom("alignedCol", (a.oid, b.oid)))

        # --- whole-grid symmetry (PATTERN-FRAME; see module docstring) ---
        # This asks whether the foreground, taken as a free-floating shape
        # normalized to its own bounding box, is invariant under each axis.
        # Position inside the grid is quotiented out, so an off-centre but
        # internally symmetric pattern still fires.
        #
        # There is deliberately NO square-grid guard on d1/d2/rot90 here.
        # Such a guard would be correct for grid-frame symmetry, where those
        # transforms have to map the grid onto itself. Under pattern-frame
        # normalization the grid's own dimensions are irrelevant, and the
        # guard was silently dropping true positives: a d1-symmetric
        # foreground in a 3x5 grid reported no symmetry at all.
        grid_offsets = {(r, c) for r in range(n_rows) for c in range(n_cols)
                        if grid[r][c] != background}
        if grid_offsets:
            base = _normalize(grid_offsets)   # hoisted; was recomputed per axis
            for axis in ("h", "v", "d1", "d2", "rot90", "rot180"):
                if _normalize(_transform_offsets(grid_offsets, axis)) == base:
                    atoms.append(Atom("gridSymmetric", (task, grid_label, axis)))

        return atoms, objects


def atoms_to_metta(atoms: Iterable[Atom]) -> str:
    return "\n".join(a.to_metta() for a in atoms)


def load_into_space(metta, atoms: Iterable[Atom]) -> None:
    """Adds atoms directly into a running hyperon.MeTTa instance's space,
    via its Python API (`metta.run('!(add-atom ...)')`), rather than
    round-tripping through a file. Used by tests and by harness.py for
    small/medium runs; for very large corpora, writing a .metta file and
    loading it with `!(import! &self "file.metta")` is faster and is the
    path documented in the README for full-corpus experiments.

    Cost note: this issues one `run()` per atom, so each atom is parsed
    separately and each new identifier is interned separately. Both the
    per-call overhead and the accumulating symbol table matter at scale
    (decisions.md D6, D9). Treat this as a convenience for tens to low
    hundreds of atoms, not as a bulk loader.
    """
    for a in atoms:
        metta.run(f"!(add-atom &self {a.to_metta()})")
