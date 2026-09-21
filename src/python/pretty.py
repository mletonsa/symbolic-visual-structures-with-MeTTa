"""
pretty.py

Renders grids and encoder output back to human-readable ASCII, so that
every object, concept, and blend can be inspected visually rather than
trusted as opaque atom soup. Used in tests, in experiment logs, and as
the source of the paper's figures.
"""

from __future__ import annotations

from encoder import ObjectInfo, COLOR_NAMES

# Single-character glyphs per ARC color index, for compact terminal/log
# rendering. '.' is used for background regardless of its actual color.
GLYPHS = {0: ".", 1: "1", 2: "2", 3: "3", 4: "4",
          5: "5", 6: "6", 7: "7", 8: "8", 9: "9"}


def render_grid(grid, background=0) -> str:
    # Default matches GridEncoder's default background rule (ARC
    # convention: color 0 is background). Pass background=... to override.
    lines = []
    for row in grid:
        lines.append("".join("." if v == background else GLYPHS.get(v, "?") for v in row))
    return "\n".join(lines)


def render_object(obj: ObjectInfo) -> str:
    """Renders just the object's own cells, cropped to its bounding box."""
    (r0, c0), (r1, c1) = obj.bbox
    h, w = r1 - r0 + 1, c1 - c0 + 1
    grid = [["." for _ in range(w)] for _ in range(h)]
    glyph = GLYPHS.get(obj.color, "?")
    for (r, c) in obj.cells:
        grid[r - r0][c - c0] = glyph
    return "\n".join("".join(row) for row in grid)


def summarize_object(obj: ObjectInfo) -> str:
    color_name = COLOR_NAMES.get(obj.color, f"c{obj.color}")
    (r0, c0), (r1, c1) = obj.bbox
    n_holes = obj.holes()
    return (f"{obj.oid}: color={color_name} size={obj.size} "
            f"bbox=({r0},{c0})-({r1},{c1}) holes={n_holes}\n"
            f"{render_object(obj)}")


def summarize_encoding(atoms, objects) -> str:
    lines = [f"{len(atoms)} atoms, {len(objects)} objects"]
    for obj in objects:
        lines.append("")
        lines.append(summarize_object(obj))
    return "\n".join(lines)
