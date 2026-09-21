# ConceptARC coverage matrix

Grid-level coverage per group and anchor relation - the D14 ceiling, computed for every group at once. A cell is `grids_with/grids_total (pct%)`; `*` marks a relation with at least 5 usable tasks (tasks carrying that relation in at least one grid), the threshold a leave-one-out sweep needs.

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

## Sweep-ready pairs (>=5 usable tasks)

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
| InsideOutside | sameShape | 79/118 (66.9%) | 10/10 |
| HorizontalVertical | alignedRow | 71/110 (64.5%) | 10/10 |
| InsideOutside | alignedRow | 76/118 (64.4%) | 10/10 |
| CleanUp | alignedRow | 68/106 (64.2%) | 10/10 |
| HorizontalVertical | sameShape | 70/110 (63.6%) | 10/10 |
| HorizontalVertical | alignedCol | 70/110 (63.6%) | 10/10 |
| Order | alignedRow | 64/102 (62.7%) | 9/10 |
| Order | alignedCol | 64/102 (62.7%) | 9/10 |
| CompleteShape | sameColor | 61/102 (59.8%) | 9/10 |
| CleanUp | alignedCol | 63/106 (59.4%) | 10/10 |
| Copy | alignedCol | 63/106 (59.4%) | 10/10 |
| TopBottom3D | sameColor | 72/122 (59.0%) | 10/10 |
| SameDifferent | sameColor | 71/126 (56.3%) | 10/10 |
| Order | sameColor | 57/102 (55.9%) | 9/10 |
| InsideOutside | alignedCol | 65/118 (55.1%) | 10/10 |
| Center | sameColor | 66/120 (55.0%) | 9/10 |
| Order | sameShape | 56/102 (54.9%) | 8/10 |
| SameDifferent | alignedRow | 68/126 (54.0%) | 10/10 |
| CompleteShape | alignedCol | 53/102 (52.0%) | 8/10 |
| CompleteShape | sameShape | 52/102 (51.0%) | 7/10 |
| MoveToBoundary | sameColor | 54/110 (49.1%) | 9/10 |
| TopBottom3D | alignedRow | 59/122 (48.4%) | 10/10 |
| ExtendToBoundary | sameColor | 55/118 (46.6%) | 9/10 |
| CompleteShape | alignedRow | 47/102 (46.1%) | 8/10 |
| MoveToBoundary | alignedRow | 50/110 (45.5%) | 8/10 |
| AboveBelow | sameShape | 49/108 (45.4%) | 9/10 |
| AboveBelow | alignedRow | 49/108 (45.4%) | 7/10 |
| ExtractObjects | sameColor | 48/106 (45.3%) | 10/10 |
| Center | sameShape | 54/120 (45.0%) | 8/10 |
| ExtractObjects | sameShape | 47/106 (44.3%) | 9/10 |
| TopBottom3D | alignedCol | 54/122 (44.3%) | 9/10 |
| FilledNotFilled | sameColor | 52/118 (44.1%) | 9/10 |
| FilledNotFilled | alignedRow | 52/118 (44.1%) | 8/10 |
| ExtractObjects | alignedRow | 46/106 (43.4%) | 9/10 |
| FilledNotFilled | alignedCol | 50/118 (42.4%) | 9/10 |
| SameDifferent | alignedCol | 52/126 (41.3%) | 9/10 |
| TopBottom2D | alignedCol | 52/128 (40.6%) | 9/10 |
| Copy | contains | 43/106 (40.6%) | 10/10 |
| InsideOutside | contains | 46/118 (39.0%) | 7/10 |
| TopBottom3D | sameShape | 47/122 (38.5%) | 9/10 |
| ExtractObjects | alignedCol | 40/106 (37.7%) | 8/10 |
| ExtendToBoundary | sameShape | 44/118 (37.3%) | 8/10 |
| Center | alignedCol | 44/120 (36.7%) | 9/10 |
| FilledNotFilled | sameShape | 42/118 (35.6%) | 8/10 |
| MoveToBoundary | alignedCol | 37/110 (33.6%) | 9/10 |
| ExtendToBoundary | alignedRow | 39/118 (33.1%) | 8/10 |
| Center | alignedRow | 39/120 (32.5%) | 9/10 |
| TopBottom2D | sameShape | 41/128 (32.0%) | 8/10 |
| ExtendToBoundary | alignedCol | 36/118 (30.5%) | 8/10 |
| CleanUp | contains | 32/106 (30.2%) | 7/10 |
| ExtractObjects | contains | 32/106 (30.2%) | 7/10 |
| MoveToBoundary | sameShape | 32/110 (29.1%) | 7/10 |
| Count | sameColor | 32/114 (28.1%) | 9/10 |
| ExtendToBoundary | contains | 33/118 (28.0%) | 5/10 |
| FilledNotFilled | contains | 31/118 (26.3%) | 5/10 |
| SameDifferent | contains | 33/126 (26.2%) | 7/10 |
| Count | sameShape | 27/114 (23.7%) | 8/10 |
| Count | alignedRow | 27/114 (23.7%) | 8/10 |
| TopBottom2D | alignedRow | 22/128 (17.2%) | 5/10 |
| Count | alignedCol | 19/114 (16.7%) | 8/10 |
| Center | contains | 17/120 (14.2%) | 5/10 |
