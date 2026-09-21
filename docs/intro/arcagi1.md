[Main page](index.md) | [Back to ARC-AGI](arcagi.md)

# ARC-AGI-1

ARC-AGI-1 is the original benchmark dataset released in 2019. It contains 400 training tasks and 100 test tasks, each one a visual reasoning puzzle.

## File format

Each task is stored as a JSON file with this structure:

```json
{
  "train": [
    {"input": [[0, 1, 2], [3, 4, 5]], "output": [[5, 4, 3], [2, 1, 0]]},
    {"input": [[1, 1, 1], [2, 2, 2]], "output": [[1, 2], [1, 2], [1, 2]]}
  ],
  "test": [
    {"input": [[0, 0, 1], [2, 3, 4]]}
  ]
}
```

Each task has a `train` section with input-output pairs (examples you learn from) and a `test` section with only inputs (puzzles you solve). Grids are represented as 2D arrays of integers. Colors are numbered 0-9:

- 0 = black (usually background)
- 1-9 = other colors

Grid sizes vary widely: from 3x3 to 30x30 or larger. Some tasks have multiple grids of different sizes.

## A simple example

Task ID: `6150a2bd` - rotation transformation

**Example 1 Input:**

```
3 3 8
3 7 0
5 0 0
```

**Example 1 Output:**

```
0 0 5
0 7 3
8 3 3
```

**Example 2 Input:**

```
5 5 2
1 0 0
0 0 0
```

**Example 2 Output:**

```
0 0 0
0 0 1
2 5 5
```

The rule: rotate the 3x3 grid 180 degrees (flip it both horizontally and vertically).

There are community sites such as [https://arc.markbarney.net/puzzle/6150a2bd](https://arc.markbarney.net/puzzle/6150a2bd) to explain these puzzles. 

## A more complex example

Task ID: `00d62c1b` - fill rectangular interiors

This task is harder. The rule detects rectangular boundaries and fills their interiors.

**Example 1 Input (6x6 grid):**

```
0 0 0 0 0 0
0 0 3 0 0 0
0 3 0 3 0 0
0 0 3 0 3 0
0 0 0 3 0 0
0 0 0 0 0 0
```

**Example 1 Output:**

```
0 0 0 0 0 0
0 0 3 0 0 0
0 3 4 3 0 0
0 0 3 4 3 0
0 0 0 3 0 0
0 0 0 0 0 0
```

**Example 2 Input (10x10 grid):**

```
0 0 0 0 0 0 0 0 0 0
0 0 3 0 3 0 0 0 0 0
0 0 0 3 0 3 0 0 0 0
0 0 3 0 0 0 3 0 0 0
0 0 0 0 0 3 0 3 0 0
0 0 0 3 0 3 3 0 0 0
0 0 3 3 3 0 0 0 0 0
0 0 0 3 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
```

It has total 5 training examples and the last is 20x20 grid! You can see them at [https://arc.markbarney.net/puzzle/00d62c1b](https://arc.markbarney.net/puzzle/00d62c1b).

This requires understanding geometry, detecting connected structures, and determining if they form closed rectangular shapes.

## What makes ARC-AGI-1 challenging

Some properties that make them hard for traditional algorithms:

- **Variable input/output sizes.** The output grid is not always the same size as the input.
- **Abstract rules.** The transformation might involve geometry, color, counting, symmetry, or relationships between shapes—or combinations of all of them.
- **Minimal examples.** Usually only 2-3 training examples. You can't afford to fit a big model.
- **No side information.** The only data is the grids themselves. No text descriptions, no hints.

## Next steps

ARC-AGI-1 is the reference dataset we use in this project. However, it's also quite large and contains many difficult, noise-heavy tasks. Researchers have created simpler versions to isolate specific reasoning skills. Let's look at those:

Next: [ConceptARC](conceptarc.md)
