# Blending two concepts into a third

The previous page ended with a problem. Filling the gap between two 1s needs a
concept about reaching in both directions at once, and counting over the
examples never produces it. Somebody has to propose the idea first.

Inventing a predicate by hand every time a task needs one does not scale, and
it is the thing this project is trying to avoid. So here is the other answer:
build the new concept out of concepts we already have.

Everything on this page is produced by `docs/examples/simple_blend.py`, which
you can run.

## Three tasks

```
task A, fill rightward from a 1        task B, fill leftward from a 1
    1 0 0 0 0  ->  1 1 1 1 1               0 0 0 0 1  ->  1 1 1 1 1
    0 0 1 0 0  ->  0 0 1 1 1               0 0 1 0 0  ->  1 1 1 0 0

task C, fill the gap between two 1s
    1 0 1 0 0  ->  1 1 1 0 0
    0 1 0 1 0  ->  0 1 1 1 0
    0 1 0 0 1  ->  0 1 1 1 1
```

A and B are easy. C is the one that defeated the counting method.

We will learn A and B from their own examples, and we will never learn C at
all. C gets solved by combining what A and B taught us.

## Learning the two easy concepts

The facts available are each cell's colour and which cells reach which, in
both directions, at any distance:

```metta
(colorIn   <cell> one)          ; or zero
(atOrLeft  <cell-a> <cell-b>)   ; a is at or to the left of b
(atOrRight <cell-a> <cell-b>)   ; a is at or to the right of b
```

For every cell that turned into a 1, we ask what could have caused it: some
cell holding a 1 that reaches it. Then we take two such cases from different
rows and anti-unify them, keeping what they agree on and turning what they
disagree on into a variable.

Trying both reach directions on task A:

```
atOrLeft    (atOrLeft $v1 $self) (colorIn $v1 one)      reproduces the task
atOrRight   (atOrRight $v1 $self) (colorIn $v1 one)     does not fit, discarded
```

And on task B, the other way round:

```
atOrLeft    (atOrLeft $v1 $self) (colorIn $v1 one)      does not fit, discarded
atOrRight   (atOrRight $v1 $self) (colorIn $v1 one)     reproduces the task
```

Two concepts, each read straight off two examples. Concept A says a cell
becomes 1 when some cell at or to its left holds a 1. Concept B says the same
thing rightward. Neither needed twenty observations or a tally, because
anti-unification asks a different question than counting does: not how often
something happens, but what two cases have in common.

## What the two concepts share

Anti-unify the concepts themselves and you get what blending calls the generic
space, the structure both of them are variations on:

```
concept A      (atOrLeft $v1 $self) (colorIn $v1 one)
concept B      (atOrRight $v1 $self) (colorIn $v1 one)
generic space  (colorIn $v1 one)
```

The two reach atoms use different predicate names, so there is nothing to
align and they drop out. What survives is "somewhere there is a cell holding a
1", which really is the whole of what A and B agree on. The direction is
exactly where they differ.

## Putting both back together

The blend takes both concepts and projects them into a single structure. Since
a concept here is a list of atoms that must all match, putting two concepts
together means requiring both at once.

There is a decision to make first, and getting it wrong quietly ruins the
result. Both concepts were learned independently and both happen to call their
variable `$v1`, but those name two different cells: the one to the left in A,
the one to the right in B. Combining them as written would force those to be
the same cell. So the variables are renamed apart. `$self` is left shared,
because there the two concepts really do mean the same thing, the cell whose
output we are deciding.

```
roles kept apart   (atOrLeft $av1 $self) (colorIn $av1 one)
                   (atOrRight $bv1 $self) (colorIn $bv1 one)

roles merged       (atOrLeft $w $self) (atOrRight $w $self) (colorIn $w one)
```

## The test

Task C, which none of this has seen:

```
input      A alone    B alone    blend      merged     wanted
1 0 1 0 0  11111      11100      11100      10100      11100
0 1 0 1 0  01111      11110      01110      01010      01110
0 1 0 0 1  01111      11111      01111      01001      01111
```

```
concept A alone            solves task C: False
concept B alone            solves task C: False
blend, roles kept apart    solves task C: True
blend, roles merged        solves task C: False
```

The blend gets all three rows right. Neither parent gets any of them right,
and the failures are in opposite directions: A fills everything rightward from
the first 1, B fills everything leftward from the last one. Only requiring both
at once picks out the interval between them.

No search over candidate concepts was performed for task C. The two parent concepts were learned from their respective tasks and the blend is what is left when
both are projected into one structure. Task C was solved by a concept that was
assembled rather than found.

## Merged blend

The merged blend asks for one cell that is both at or left of me and at or
right of me. Only one cell satisfies that, which is the cell itself, so the
concept reduces to "I am a 1" and copies the input back unchanged. Look at the
merged column above: it is the input, every time.

The same two concepts, combined by the same
mechanism, give either the concept we wanted or a useless one, and the
difference is entirely in how the correspondences were drawn. Blending is not
a machine that turns two ideas into a better one. It is a way of generating
candidates, some of which are worth keeping.

Which is why the real pipeline scores its blends rather than trusting them.
A blend has to still match something, has to pay for itself in description
length, and has to not be a restatement of something already known. The merged
blend above fails that last test loudly, since it is a long way of saying
`(colorIn $self one)`.

## Section summary

This section shows a simplified example how a concept being built rather than searched for. Counting could not
reach the gap-filler, as the previous page established, because counting can
only accumulate evidence one position at a time and this concept needs two
conditions held together. Blending produces conditions held together as a
matter of course, because that is what combining two structures does.

There are also limitations to this example. The two parent concepts were learned over a shape fixed in
advance, a reach relation plus a colour, so the space of things they could
have been was small. Choosing to keep the roles apart rather than merge them
was made here by hand. Three one-dimensional tasks with one rule each is a
long way from a real corpus.

The mechanism is the same one the project uses on ARC grids, and the same
questions come back there in harder forms: which candidates to build, which
correspondences to draw, and how to tell a useful blend from a long-winded
restatement of something already in hand.

This is still a very constrained form of concept learning: the vocabulary, the reach relation, and even the form of the concepts have been given in advance. What we are testing here is a smaller question: whether a system can use concepts it already has to construct a concept that was never explicitly provided.

Next: [Vocabulary](vocabulary.md)
