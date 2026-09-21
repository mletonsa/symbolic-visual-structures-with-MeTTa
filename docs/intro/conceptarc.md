[Main page](../index.md) | [Back to ARC-AGI](arcagi.md)

# ConceptARC

ConceptARC is a benchmark of new ARC-like tasks designed to isolate specific abstract reasoning skills. Instead of mixing many different puzzle types together, ConceptARC groups tasks by the core concept they require. This makes it easier to study whether an algorithm can learn and apply individual concepts.

## Structure and motivation

ARC-AGI-1 contains 400 diverse tasks, many of which combine multiple concepts in complex ways. ConceptARC takes a different approach: researchers manually created new tasks that clearly demonstrate a single concept and organized them into concept groups.

There are currently 16 concept groups in ConceptARC:

- AboveBelow
- Center
- CleanUp
- CompleteShape
- Copy
- Count
- ExtendToBoundary
- ExtractObjects
- FilledNotFilled
- HorizontalVertical
- InsideOutside 
- MoveToBoundary
- Order
- SameDifferent
- TopBottom2D
- TopBottom3D

Each group contains 10 carefully selected tasks that all require the same core reasoning skill.

In this research, ConceptARC is the primary experimental dataset. The key question we're testing is:

"Can concept blending discover the shared abstract concept within a group?"

For example, if you blend two different "InsideOutside" tasks together, does the resulting pattern capture the essence of what makes them both about containment?

ConceptARC makes this question tractable because:

1. **Clear ground truth** - we know what concept each group represents, so we can evaluate whether blending recovers it
2. **Homogeneous puzzles** - all tasks in a group use the same type of reasoning, reducing noise
3. **Manageable size** - 160 tasks (vs 400 in ARC-AGI-1) is more practical for research
4. **Less noise** - ConceptARC deliberately excludes the scattered, noisy tasks that make ARC-AGI-1 hard

## Examples

https://github.com/victorvikram/ConceptARC/blob/main/corpus/Center/Center1.json

Input 1:

[0,0,0,0,0,0,0],
[0,3,3,3,3,3,0],
[0,3,0,0,0,3,0],
[0,3,0,0,0,3,0],
[0,3,0,0,0,3,0],
[0,3,3,3,3,3,0],
[0,0,0,0,0,0,0]

Output 1:

[0,0,0,0,0,0,0],
[0,3,3,3,3,3,0],
[0,3,0,0,0,3,0],
[0,3,0,3,0,3,0],
[0,3,0,0,0,3,0],
[0,3,3,3,3,3,0],
[0,0,0,0,0,0,0]

https://github.com/victorvikram/ConceptARC/blob/main/corpus/AboveBelow/AboveBelow1.json

Input 1:

[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[2,2,2,2,2,2,2,2,2,2,2,2],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,4,4,4],
[0,0,0,4,4,4,4,0,0,4,4,4],
[0,0,0,4,4,4,4,0,0,4,4,4]

Output 1:

[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,4,4,4,4,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[2,2,2,2,2,2,2,2,2,2,2,2],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0]

Next: [Mini-ARC](miniarc.md)
