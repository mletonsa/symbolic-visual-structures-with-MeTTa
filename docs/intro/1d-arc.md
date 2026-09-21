[Main page](../index.md) | [Back to ARC-AGI](arcagi.md)

# 1D-ARC

1D-ARC extends the ARC reasoning framework to one-dimensional grids—single rows of colored cells instead of 2D grids. By reducing spatial dimensionality, 1D-ARC isolates the reasoning challenge while eliminating complexity from 2D geometry and spatial relations.

## Basic idea

Instead of a 2D grid like this:

```
1 1 0 2 2
1 0 0 2 0
0 0 1 2 2
```

A 1D task is just a single row:

```
1 1 0 2 2 1 0 2 2
```

The puzzle still asks: given input rows and output rows, infer the transformation rule. But without the complexity of 2D space—no rotation, no bounding boxes, no directional adjacency beyond "left" and "right."

## Why 1D is useful for development

1D-ARC is even simpler than Mini-ARC:

- Minimal spatial complexity - only linear sequence, no geometric relations
- Faster to encode and process - a 1D row has far fewer atoms to represent than a 2D grid
- Easier to visualize patterns - you can see sequences and repetitions at a glance
- Targeted testing - test pattern matching, color transformations, and sequence logic without the noise of 2D geometry


## Structure

1D-ARC is procedurally generated rather than hand-crafted. There is no fixed dataset to download; instead, tasks are created on-the-fly using a generator (optozorax/arc_1d).

For validation and testing in this project, we use hand-built fixture tasks that represent common 1D patterns:

- **Simple recoloring** - change all cells of color X to color Y
- **Repetition detection** - identify and extend repeating sequences
- **Symmetry** - mirror patterns or create symmetric transformations
- **Counting and filling** - count occurrences of a color or fill based on counts

## Example

Here is a mirror task 1 (https://github.com/khalil-research/1D-ARC/blob/main/dataset/1d_mirror/1d_mirror_1.json) data, three training examples and one test with correct output:

train:

"input":  [[0, 0, 0, 0, 2, 2, 2, 2, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0]], 
"output": [[0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 2, 2, 2, 2, 0, 0, 0]]}, {

"input":  [[0, 0, 0, 5, 5, 5, 5, 5, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0]], 
"output": [[0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 5, 5, 5, 5, 5, 0, 0]]}, {

"input":  [[0, 6, 6, 6, 6, 6, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 
"output": [[0, 0, 0, 0, 0, 0, 0, 9, 0, 6, 6, 6, 6, 6, 0, 0, 0, 0]]}],

test: 

"input":  [[0, 0, 2, 2, 2, 2, 2, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 
"output": [[0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 2, 2, 2, 2, 2, 0, 0, 0]]

In this task cell valued 9 is the center point and other cells are mirrored around that.

More visual examples can be found from [https://github.com/khalil-research/1D-ARC](https://github.com/khalil-research/1D-ARC)

## Representation in MeTTa

Since 1D grids are just single rows, the MeTTa representation simplifies: there are only maximum 2 neighbours and y-coordinates are fixed to 0. 

## Generation

There exists also [generator](https://github.com/optozorax/arc_1d) for these 1D tasks with excellent [visualization tools](https://optozorax.github.io/arc_1d/). 


Next: [Re-ARC](re-arc.md)
