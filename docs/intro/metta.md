# Introduction to MeTTa

This project uses MeTTa (Meta Type Talk), the native language of the OpenCog Hyperon framework.

## Why MeTTa?

Unlike standard programming languages (like Python) that separate data from code, MeTTa treats everything as an Atom. This allows us to represent visual grids, logical rules, and concept blending operations in a single, unified Atomspace.

For "Pattern Discovery," MeTTa provides three critical features out of the box:
1.  Pattern Matching: You can search for complex structural patterns without writing custom loops.
2.  Unification: The system can automatically fill in variables (like `?x` or `?color`) to find solutions.
3.  Homoiconicity: Code can rewrite itself. This is useful for concept blending, where the system invents new rules on the fly.

## Data Representation

In this project, we do not store grids as 2D arrays (like `grid[0][1]`). Instead, we explode them into a Hypergraph of symbolic facts. For example, a simple red pixel at coordinates (1, 2) is represented as a set of linked atoms:

    ; Primitive entities (Symbols)
    (IsA c1 Cell)
    (HasColor c1 Red)
    (HasCoord c1 (1 2))

    ; Relations between entities
    (Adjacent c1 c2)
    (Direction c1 c2 Right)

More information about MeTTa language can be found at [MeTTa language homepage](https://metta-lang.dev/).

Next: [Resources](resources.md)