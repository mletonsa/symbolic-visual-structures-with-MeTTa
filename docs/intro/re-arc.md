[Main page](../index.md) | [Back to ARC-AGI](arcagi.md)

# Re-ARC

Re-ARC is mentioned here last but it can be one of the most useful tools for building ARC-AGI solvers. An abstract from developer's paper:

"This work presents code to procedurally generate examples for the ARC training tasks. For each of the 400 tasks, an example generator following the transformation logic of the original examples was created. In effect, the assumed underlying distribution of examples for any given task was reverse engineered by implementing a means to sample from it. An attempt was made to cover an as large as reasonable space of possible examples for each task. That is, whenever the original examples of a given task may be limited in their diversity e.g. by having the dimensions of the grids, the set of symbols or number of objects constant or within tight bounds, even though the transformation does not require it, such constraints were lifted. Having access to not just a few examples per task, as the case for ARC, but instead very many, should enable a wide range of experiments that may be important stepping stones towards making leaps on the benchmark."

It therefore provides Procedural Example Generation for the original ARC-AGI 1 tasks. It shows the logic behind the tasks and can generate huge variation of similar tasks.

## Why this matters for this project

A key risk in concept blending is learning superficial patterns instead of genuine abstractions. For example, a blend might learn "whenever you see color 3, do X" rather than "whenever you see an object of type A, do X." These are equivalent on the training data but break on color-swapped variants.

Re-ARC lets us test stability:

- Validate learned concepts - if a blend only works on the original task, it captured spurious correlations, not real concepts
- Measure robustness - how much perturbation can a concept withstand before it fails?
- Ablation testing - compare blends learned on original tasks vs. blends learned on variants

## Structure

Re-ARC is generated procedurally from existing ARC-AGI-1 tasks. For a given source task, the generator creates multiple variants by applying different transformations.

Common perturbation types:

- Color permutations - randomly reorder the color palette
- Rotations - apply 90, 180, or 270-degree rotations
- Reflections - flip horizontally or vertically
- Grid scaling - enlarge or shrink while preserving the pattern
- Translation - shift patterns within the grid

Each variant maintains the solution logic but breaks surface-level memorization.

## Example

For each ARC-AGI 1 task there is a generator such as:

```
def generate_7468f01a(diff_lb: float, diff_ub: float) -> dict:
    cols = interval(0, 10, 1)
    h = unifint(diff_lb, diff_ub, (3, 30))
    w = unifint(diff_lb, diff_ub, (3, 30))
    bgc = choice(cols)
    remcols = remove(bgc, cols)
    sgc, fgc = sample(remcols, 2)
    oh = unifint(diff_lb, diff_ub, (2, max(2, int(h * (2/3)))))
    ow = unifint(diff_lb, diff_ub, (2, max(2, int(w * (2/3)))))
    gi = canvas(bgc, (h, w))
    go = canvas(sgc, (oh, ow))
    bounds = asindices(go)
    shp = {ORIGIN}
    nc = unifint(diff_lb, diff_ub, (0, max(1, (oh * ow) // 2)))
    for j in range(nc):
        shp.add(choice(totuple((bounds - shp) & mapply(dneighbors, shp))))
    go = fill(go, fgc, shp)
    objx = asobject(vmirror(go))
    loci = randint(0, h - oh)
    locj = randint(0, w - ow)
    gi = paint(gi, shift(objx, (loci, locj)))
    return {'input': gi, 'output': go}
```

Next: [MeTTa](metta.md)
