# Learning the Language of Concepts

On the previous page we wrote a grid down as pixels, then imagined more useful
facts we could add on top: which cells touch, which cells group into objects,
which object sits inside which. Every one of those was chosen by a person
looking at a picture and deciding what mattered.

That is the part we want the program to do for itself. So the question becomes:
where does a vocabulary come from, if nobody hands it over?

Grids are a lot to think about at once, so this page works in one dimension.
Five cells in a row, two colours. Small enough to write the whole thing out,
and it turns out to be enough to run into the real problem.

## A first example

Four input rows and their outputs:

```
in0  0 0 1 0 0        out0  0 0 1 1 0
in1  0 1 0 0 0        out1  0 1 1 0 0
in2  0 0 0 1 0        out2  0 0 0 1 1
in3  1 0 0 0 0        out3  1 1 0 0 0
```

Most people see this quickly. The 1 stays where it is, and it also spreads one
step to the right. Or, said from each cell's point of view: a cell is 1 if it
was already 1, or if the cell to its left was 1.

Suppose we know nothing except that a cell's output might depend on the input
row. For binary cells there are 32 possible input rows. If we saw all 32 and
their outputs, we would have solved this task in a brute way, assuming it is
fully causal with no randomness. But that is not something we can generalise.
It works for no grid size other than five cells, and size makes the number of
possibilities huge. A 5x5 grid with 10 colours has 10^(5*5) = 10^25 possible
inputs, which is 10000000000000000000000000.

Let's make a design decision instead: centre the input row on the output cell
we are checking, so that corresponding cells line up. I write `e` for
positions that fall outside the row:

```
in0        out0

eeee00100  0
eee00100e  0
ee00100ee  1
e00100eee  1
00100eeee  0

in1        out1

eeee01000  0
eee01000e  1
ee01000ee  1
e01000eee  0
01000eeee  0

in2        out2

eeee00010  0
eee00010e  0
ee00010ee  0
e00010eee  1
00010eeee  1

in3        out3

eeee10000  1
eee10000e  1
ee10000ee  0
e10000eee  0
10000eeee  0
```

Now count, for each of the nine window positions, how often a 1 appears there,
split by what the output cell became:

```
ones per position when output is 0:   1 2 3 0 0 3 2 1 0
ones per position when output is 1:   0 0 0 4 4 0 0 0 0
```

The two rows never overlap. Whenever the output is 1, the input's 1 sits
either in the centre position or one step to its left, and it never sits in
those positions when the output is 0. That gives us the mask `000110000`: a
cell becomes 1 exactly when a 1 appears at one of the marked positions.

Applying it means sliding the same window along and looking only at the two
marked positions, the centre and one step to its left. For `in0`:

```
                window                   marked     output

cell 0     e e e e 0 0 1 0 0              e 0         0
cell 1     e e e 0 0 1 0 0 e              0 0         0
cell 2     e e 0 0 1 0 0 e e              0 1         1
cell 3     e 0 0 1 0 0 e e e              1 0         1
cell 4     0 0 1 0 0 e e e e              0 0         0
```

Reading down the last column gives `0 0 1 1 0`, which is `out0`.

This is a much stronger result than the brute-force table. It works for a 1D
input of any size, even line by line on a 2D grid. It has compressed the
operation from a big lookup table into a single convolution mask. But notice
who made it possible. Lining up corresponding cells is a geometric idea that
humans bring to grids without thinking about it. For the computer, five bits
were just data. A program can be made to find this alignment, but nothing
about the data makes it as natural as it is for us.

## A second example

Now a different task, same shape of problem:

```
in0  1 0 1 0 0        out0  1 1 1 0 0
in1  0 1 0 1 0        out1  0 1 1 1 0
in2  0 1 0 0 1        out2  0 1 1 1 1
```

Again most people see it at once. There are two 1s, and the space between them
fills in. From a cell's point of view: a cell is 1 if there is a 1 somewhere at
or to its left, and also a 1 somewhere at or to its right.

We run exactly the same procedure. Centre the windows, count the ones, split by
what the output cell became:

```
ones per position when output is 0:   1 2 1 2 0 2 0 1 1
ones per position when output is 1:   0 1 3 3 6 3 3 1 0
```

Two positions still look clean. Position 4, the centre, and position 6, two
cells to the right, hold a 1 only when the output is 1. So the method proposes
the mask `000010100`.

Apply it to the training rows it was derived from:

```
input 1 0 1 0 0    want 1 1 1 0 0    mask gives 1 0 1 0 0
input 0 1 0 1 0    want 0 1 1 1 0    mask gives 0 1 0 1 0
input 0 1 0 0 1    want 0 1 1 1 1    mask gives 0 1 1 0 1
```

Wrong on every row, and wrong in a different place each time. This is not a
poor choice of positions. We checked all 511 possible masks over the nine
window positions, and none of them reproduces these three examples.

## Why no mask can work

The counting method asks one question per position: does a 1 appear here more
often when the answer is yes? Then it collects the positions that pass and
fires whenever any of them holds. The evidence adds up disjunctively, and a
mask is an OR over its marked positions.

This task needs an AND. The cell at position 1 in `1 0 1 0 0` becomes 1 because
there is a 1 to its left and a 1 to its right. Either one on its own must do
nothing, otherwise a row with a single 1 would start filling in every
direction. A requirement that two things hold together is invisible to a method
that only ever measures one position at a time, because neither position looks
decisive on its own.

Notice what is not the problem here: Five-cell rows put every cell within four
steps of every other, so our nine-wide window already reaches the whole row.
There is nothing the window failed to see. The information was all present and
the shape of the rule was wrong.

On longer rows a second problem joins it. The gap between the two 1s can be as
wide as the row, so even a rule that could express AND would need to look
arbitrarily far in both directions. A mask that grows with its input is no
longer a mask.

So the idea we need is not in the space being searched, and no amount of
counting will find it. Somebody, or something, has to propose it first.

That is the real difficulty, and it is not about running out of computing
power. Both problems here are tiny. The difficulty is that the second task
needs a kind of rule the first one gave no reason to invent.

There is an uncomfortable ladder in view here. When a simple OR over a window
fails, allow any combination of positions, including ANDs. When a fixed window
fails, allow reach of any distance. When that fails, allow state carried along
a sweep, and past that lie arbitrary programs. Each step buys expressiveness
and pays for it in search space, and the top of the ladder, the space many
believe ARC tasks are really drawn from, is all computable algorithms. Nothing
searches that space unaided. Something has to narrow it first, and whatever
does the narrowing is doing the job a vocabulary does.

## What this means for our vocabulary

Our encoder records which cells touch each other, and that is a neighbourhood
fact. It has nothing that says one cell is somewhere to the left of another at
any distance. Written out, this task needs something like:

```metta
(leftOf  <cell-a> <cell-b>)    ; a is somewhere to the left of b, any distance
(rightOf <cell-a> <cell-b>)    ; and its mirror
```

which is `adj` followed as many times as it takes. With those, the rule is
sayable: a cell is 1 when some 1 is at or left of it and some 1 is at or right
of it. In the first example these predicates would have been pointless. Here
nothing works without them, and they have to be used together rather than
separately.

The same idea covers a whole family of ARC tasks: filling the space between
two marks, extending a line until it reaches an edge, letting shapes fall to
the bottom, casting a ray until it hits something. All of them are about
reaching, not about touching.

It is not free. Recording which cells touch is one fact per neighbouring pair.
Recording which cells are anywhere to the left of which is a fact for every
pair in the row, so a row twice as long costs four times as much. On five
cells that is nothing. On a thirty by thirty grid it needs more care.

## Where this leaves us

Two five-cell examples, and already the shape of the problem is visible. The first was solved by counting, once we chose what to count. The second could not be solved by counting at all, whatever we counted, because the rule it needs has a shape the counting method cannot represent.

This is why the vocabulary is the thing worth being careful about. A concept the encoder cannot express is not merely expensive to find. It is not there to be found.

Humans are remarkably good at inventing and applying useful vocabularies. We can introduce a concept such as between, inside, or left of when a problem calls for it, and then use that concept to reason about the problem. An artificial general intelligence would ideally need to do something similar. This project does not attempt to go so far. Instead, we take a smaller and more controlled step: we start with a limited vocabulary and ask whether new concepts can be built from concepts that are already available.

The next question is therefore where a concept like that comes from, if we do not want to keep inventing predicates by hand every time a task needs one. One answer is to build new concepts out of the ones already learned, which is what concept blending is for.

[Blending two concepts into a third](simpleblend.md)
