# Encoding: turning a grid into facts

Before anything can blend two concepts together, it needs concepts to work
with. An ARC task arrives as coloured squares in a JSON file. It is a good
way to store a picture but a poor way to reason about one. The encoder's job
is to read a grid once and write down what it sees as a set of plain
statements. This page explains the thinking behind that translation. 

## Grid format

Here is a small grid, a green ring with a red cell inside it:

```
. . . . .
. 3 3 3 .
. 3 2 3 .
. 3 3 3 .
. . . . .
```

Most people describe this the same way. There is a square made of number 3's. There is a dot made of number 2.
The dot is inside the square. That description is not in the JSON. It is
something a reader adds, and the encoder's job is to add the same kind of
thing, explicitly, so the rest of the system can work with it. It would be something like this:

```metta
(object demo in0 demo_in0_o0)
(objColor demo_in0_o0 green)
(size demo_in0_o0 8)
(bbox demo_in0_o0 (C 1 1) (C 3 3))
(holes demo_in0_o0 1)

(object demo in0 demo_in0_o1)
(objColor demo_in0_o1 red)
(size demo_in0_o1 1)

(contains demo_in0_o0 demo_in0_o1)
```

Here demo is name of the task, in0 means input 0, and o0 is object 0. The long name demo_in0_o0 means object 0 in input 0 in demo task.

That last line is the interesting one. Nothing in the original JSON says
anything is inside anything. The encoder worked it out, and once it is
written down as a fact, blending can treat it like any other fact.

Everything the encoder produces looks like this: a predicate name and some
arguments. There are no images, no arrays, no special cases. A grid becomes a
pile of small true statements, and that pile is what the rest of the project
reasons over.

## The encoder commits to one reading

The grid above could be read other ways. Perhaps the ring and the dot are one
object with two colours. Perhaps colour 0 is not really background here.
Perhaps two cells touching only at a corner should count as connected.

The encoder picks one answer to each of these and applies it everywhere:

- Colour 0 is background.
- An object is a group of same-coloured cells connected up, down, left or
  right.
- Corner-touching cells belong to different objects.

None of these is the truth about ARC grids. They are the conventions the ARC
community mostly uses, they are simple to explain, and applying them
uniformly means a grid always encodes the same way. When one of them turns
out to be wrong for a particular dataset, that becomes a recorded decision
rather than a quiet special case. 

For example, the background rule started out as "the
most common colour in the grid", which sounds sensible until you meet a small
grid that is mostly foreground, at which point it decides the whole grid is
background and finds no objects at all.

## Blending can find only what encoder says

The encoder has a `contains` predicate, so the system can discover concepts
about nesting. It has no "above" predicate, so no amount of clever blending
will discover a concept about one thing being above another. The vocabulary
is a boundary on what is thinkable, not just a convenience.

That boundary is measurable. In ConceptARC's InsideOutside group, only 46 of
the 80 grids used in our experiments carry any containment structure at all.
A pattern built around `contains` cannot possibly match the other 34, so
before running anything we know the experiment's match rate cannot exceed
57.5%. When our best result came in at 54%, that number meant something quite
different than it would have on its own.

So the honest way to report a result here is against what the representation
allows, not against 100%. A page that says "our method matched 54% of grids"
invites the reader to imagine the missing 46% as failure. Much of it was
never available.

## Cells exist, but blending ignores them

The encoder emits a fact for every single cell: where it is, what colour it
is, which cells it touches. For the little 5x5 grid above that is 115 atoms
out of 154. On a full 30x30 grid it is well over 90% of everything produced.

Blending never looks at them.

Cell facts are there so that a human can check the encoder's work, and so
that object-level facts have something to be derived from. The actual
reasoning happens one level up, where a typical grid has ten or twenty
objects rather than nine hundred cells.

The reason for this is arithmetic. Relations between objects are computed for every
pair, so doubling the number of things quadruples the work. One ARC task
turned out to be a field of scattered noise with 441 single-cell objects,
which is 194,000 pairs, and produced about 135,000 atoms from a single grid.
Working at the object level keeps that from being the normal case, and a cap
on object count catches it when it happens anyway.

## Small vocabulary, human readable

Two rules keep the representation from sprawling.

Every predicate has to earn its place. If no experiment uses it, it gets cut.
It is easy to imagine dozens of useful-sounding properties an object might
have, and each one added is another thing that has to be explained,
maintained, and reasoned about. The list stays short deliberately.

Everything can be turned back into something a person can look at. Every
exported corpus file has the grid drawn in ASCII above its facts, and any
object or pattern can be rendered as a small picture. When a result is
surprising, the first move is always to look at what the system actually saw,
and that only works if looking is easy.

## Python encodes, MeTTa reasons

Encoding is done in Python, blending in MeTTa. Reading a grid, finding connected components and checking symmetries is
ordinary computation, and Python does it quickly. Once a grid is a set of
facts, the interesting operations are pattern matching and generalisation,
which is what MeTTa is for. The facts cross the boundary as text or through
MeTTa's Python API, and both sides see the same vocabulary.

There is also a practical reason. Counting how often a pattern occurs across
a whole corpus is heavy work, and doing it inside the MeTTa interpreter is
slow enough to matter at the sizes we care about. Those aggregate operations
stay in Python, over the same atoms.

[Learning vocabulary](1dstats.md)
