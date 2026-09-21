[Contents](../index.md) · Previous: [Scope and requirements mapping](analysis1.md) · Next: [Diversity-based pair selection](analysis3.md)

# Analysis, 2: Coverage of the relational vocabulary

## 2.1 The coverage ceiling

A blend pattern anchored on relation *r* can only match a grid that
contains at least one atom of *r*. For a leave-one-out sweep over a set of
held-out tasks, this bounds the achievable match rate before any candidate
is extracted or any blend is built. The bound is the fraction of held-out
grids carrying at least one atom of the anchor relation. This quantity is
computed directly from encoder output and requires no MeTTa evaluation.

This section reports that bound, measured across the full ConceptARC
benchmark, for every relation the candidate schema can anchor on. Section 3
reports experimental results against the bounds established here.

## 2.2 Method

`python/coverage_matrix.py` encodes every grid of every task in every
ConceptARC concept group once. From that single encoding pass it records,
for each of the five anchor relations defined in `enumerate.py`
(`contains`, `sameColor`, `sameShape`, `alignedRow`, `alignedCol`), the
number of grids carrying at least one atom of that relation and the number
of tasks carrying the relation in at least one grid. The second count
determines whether a group and relation combination has enough structure to
support a leave-one-out sweep. Five tasks is the minimum used in this
project (Section 3, SameDifferent/`sameShape`). Seven tasks is the number
used for the InsideOutside/`contains` sweep reported in decisions.md D14.

## 2.3 Results

Table 3 reports grid-level coverage for all sixteen ConceptARC groups and
all five anchor relations. A cell reports matched grids over total grids
and the resulting percentage. An asterisk marks a relation with at least
five tasks carrying it in the group.

**Table 3.** Grid-level relational coverage across the ConceptARC benchmark.

| Group | contains | sameColor | sameShape | alignedRow | alignedCol |
|---|---|---|---|---|---|
| AboveBelow | 13/108 (12%) | 78/108 (72%)* | 49/108 (45%)* | 49/108 (45%)* | 75/108 (69%)* |
| Center | 17/120 (14%)* | 66/120 (55%)* | 54/120 (45%)* | 39/120 (32%)* | 44/120 (37%)* |
| CleanUp | 32/106 (30%)* | 79/106 (75%)* | 73/106 (69%)* | 68/106 (64%)* | 63/106 (59%)* |
| CompleteShape | 9/102 (9%) | 61/102 (60%)* | 52/102 (51%)* | 47/102 (46%)* | 53/102 (52%)* |
| Copy | 43/106 (41%)* | 87/106 (82%)* | 87/106 (82%)* | 78/106 (74%)* | 63/106 (59%)* |
| Count | 13/114 (11%) | 32/114 (28%)* | 27/114 (24%)* | 27/114 (24%)* | 19/114 (17%)* |
| ExtendToBoundary | 33/118 (28%)* | 55/118 (47%)* | 44/118 (37%)* | 39/118 (33%)* | 36/118 (31%)* |
| ExtractObjects | 32/106 (30%)* | 48/106 (45%)* | 47/106 (44%)* | 46/106 (43%)* | 40/106 (38%)* |
| FilledNotFilled | 31/118 (26%)* | 52/118 (44%)* | 42/118 (36%)* | 52/118 (44%)* | 50/118 (42%)* |
| HorizontalVertical | 25/110 (23%) | 75/110 (68%)* | 70/110 (64%)* | 71/110 (65%)* | 70/110 (64%)* |
| InsideOutside | 46/118 (39%)* | 84/118 (71%)* | 79/118 (67%)* | 76/118 (64%)* | 65/118 (55%)* |
| MoveToBoundary | 5/110 (5%) | 54/110 (49%)* | 32/110 (29%)* | 50/110 (45%)* | 37/110 (34%)* |
| Order | 14/102 (14%) | 57/102 (56%)* | 56/102 (55%)* | 64/102 (63%)* | 64/102 (63%)* |
| SameDifferent | 33/126 (26%)* | 71/126 (56%)* | 87/126 (69%)* | 68/126 (54%)* | 52/126 (41%)* |
| TopBottom2D | 8/128 (6%) | 25/128 (20%) | 41/128 (32%)* | 22/128 (17%)* | 52/128 (41%)* |
| TopBottom3D | 15/122 (12%) | 72/122 (59%)* | 47/122 (39%)* | 59/122 (48%)* | 54/122 (44%)* |

## 2.4 `contains` is the weakest relation in the vocabulary

`contains` has the lowest coverage of the five relations in all sixteen
groups, without exception. Its coverage ranges from 4.5% (MoveToBoundary)
to 40.6% (Copy). In every group, each of the other four relations has
higher coverage than `contains`.

The consequence for sweep design is direct. `contains` clears the
five-task usable threshold in 8 of 16 groups. Every other relation clears
it in at least 15 of 16 groups. `sameShape`, `alignedRow`, and
`alignedCol` clear it in all sixteen. `sameColor` clears it in fifteen of
sixteen, falling short only in TopBottom2D, where the relation covers 25 of
128 grids (20%) but fewer than five of the group's tasks carry it in any
grid. A leave-one-out sweep anchored on `contains` is
therefore both lower in ceiling and more restricted in which groups can
support one, compared to a sweep on any of the other four relations.

This bears directly on the InsideOutside/`contains` sweep reported in
Section 3 and in decisions.md D9, D11, and D14. That sweep uses 46 of 118
grids across all ten InsideOutside tasks (39.0%), or 46 of 80 grids across
the seven tasks that carry `contains` structure at all (57.5%), the figure
reported in D14 as the sweep's ceiling. The two percentages describe the
same 46 matching grids against different denominators, the full group
against the subset a leave-one-out sweep actually draws on. Both are
correct. The flagship experiment in this project is anchored on the
sparsest relation the vocabulary provides.

## 2.5 Identifying further test groups

Table 4 reports the ten highest-coverage group and relation pairs that
clear the five-task usable threshold, drawn from all 71 pairs meeting that
threshold across the benchmark.

**Table 4.** Highest-coverage sweep-ready group and relation pairs.

| Group | Relation | Coverage | Usable tasks |
|---|---|---|---|
| Copy | sameColor | 87/106 (82.1%) | 10/10 |
| Copy | sameShape | 87/106 (82.1%) | 10/10 |
| CleanUp | sameColor | 79/106 (74.5%) | 10/10 |
| Copy | alignedRow | 78/106 (73.6%) | 10/10 |
| AboveBelow | sameColor | 78/108 (72.2%) | 10/10 |
| InsideOutside | sameColor | 84/118 (71.2%) | 10/10 |
| AboveBelow | alignedCol | 75/108 (69.4%) | 9/10 |
| SameDifferent | sameShape | 87/126 (69.0%) | 10/10 |
| CleanUp | sameShape | 73/106 (68.9%) | 10/10 |
| HorizontalVertical | sameColor | 75/110 (68.2%) | 10/10 |

Copy/`sameColor` and Copy/`sameShape` are tied for the highest coverage
of any pair in the benchmark, both at 82.1% with all ten tasks usable. This
is the basis for selecting Copy/`sameColor` as a third group and relation
for the diversity-selection replication reported in Section 3, alongside
InsideOutside/`contains` (D9, D11, D14) and SameDifferent/`sameShape`
(D10, D12).

Next: [Diversity-based pair selection](analysis3.md)
