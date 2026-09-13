# Frozen v1 cell sets vs Tastekin et al. typing (Phase 1.5, Task A)

Generated 2026-09-12 by `scripts/cross_check_cells.py`. Documentation only: the frozen sets in `data/cells.json` are not changed; Phase 0 gates passed on them as they are.

## Sources

- `Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx` (bioRxiv 10.1101/2025.08.25.671814v2, Supplemental table 2 = Table S1 of the Cell version; CC BY-NC-ND 4.0; gitignored). FlyWire rows only (`Connectome == "FAFB – Flywire"`): 411 GRNs, 66 MNs. The table holds GRNs and MNs only; there are no interneuron rows, so GNG015, GNG016, GNG042 (Quasimodo), GNG087 (Scapula) and GNG510 cannot be resolved from it (OQ-5).
- `data/cells.json` (Shiu et al. 2024 sets: sugar 23, bitter 42, water 18, ir94e 18).
- `2025_Completeness_783.csv`: the FlyWire v783 neuron index the model is built on (138639 neurons); every ID below carries an `in v783` flag from it.
- Modality mapping (docs/phase1_5_plan.md, Amendment 2): sugar = LB3b + LB3c; bitter = LB1a-d; water = LB3a; ir94e = LB1e.

All 411 FlyWire GRN body IDs and all 66 MN body IDs in the table are present in the v783 index.

## Summary

| frozen set | n | Tastekin typing of our IDs | ours without a Tastekin row | Tastekin IDs of the mapped subtypes not in our set |
|---|---:|---|---:|---:|
| sugar | 23 | LB3/LB3c 11; LB3/LB3d 7; LB4/LB4b 4; LB3/LB3b 1 | 0 | 45 of 57 |
| bitter | 42 | LB1/LB1a 16; LB1/LB1c 11; LB1/LB1d 8; LB1/LB1b 7 | 0 | 0 of 42 |
| water | 18 | LB3/LB3a 11; LB3/LB3c 7 | 0 | 19 of 30 |
| ir94e | 18 | LB1/LB1e 11; LB2/LB2c 3; LB2/LB2a 2; LB2/LB2b 2 | 0 | 12 of 23 |

## MN9 side labels

| our name (data/cells.json, Shiu naming) | root_id | Tastekin Root_Side | Tastekin Type | in v783 |
|---|---|---|---|---|
| left MN9 | 720575940660219265 | R | MN9 | yes |
| right MN9 | 720575940618238523 | L | MN9 | yes |

The MNs sheet labels 720575940660219265 as R and 720575940618238523 as L, matching the Schlegel et al. 2024 soma side. Our protocol calls 720575940660219265 "left MN9" following Shiu et al. 2024's contralateral naming (right-hemisphere sugar GRNs are stimulated and the contralateral MN9 is read; docs/cell_ids.md). The two labels describe the same two neurons; nothing is swapped.

## Feeding-MN types available with FlyWire IDs

| Type | n | Target_Muscle |
|---|---:|---|
| CEM | 6 | Crop Entry |
| MN1 | 4 | 1 |
| MN10 | 3 | 10 |
| MN11D | 2 | 11D |
| MN11V | 2 | 11V |
| MN12D | 4 | 12D |
| MN13 | 2 | 13 |
| MN2Da | 2 | 2D |
| MN2Db | 2 | Unknown |
| MN2V | 2 | 2V |
| MN3L | 4 | 3L |
| MN3M | 2 | 3M |
| MN4a | 4 | 4 |
| MN4b | 2 | Unknown |
| MN5 | 2 | 5 |
| MN6 | 2 | 6 |
| MN7 | 4 | 7 |
| MN8 | 2 | 8 |
| MN9 | 2 | 9 |
| MNx01 | 3 | Unknown |
| MNx02 | 2 | Unknown |
| MNx03 | 4 | Unknown |
| MNx04 | 2 | Unknown |
| MNx05 | 2 | Unknown |

Pharyngeal GRN types with FlyWire IDs: PhG1 8, PhG2 5, PhG3 2, PhG4 4, PhG5 2, PhG6 2, PhG7 5, PhG8 4, PhG9 4, PhG10 2, PhG11 2, PhG12 2, PhG13 2, PhG14 2, PhG15 2, PhG16 2 (50 cells).
LB3b (sugar + low salt) 25 and LB3d (high salt / heavy metal, glutamatergic) 29 cells have FlyWire IDs, all in v783: the ID lists Phase 1.5 salt work needs are in the per-set tables below (LB3d appears under the sugar set) and in the table itself.


## sugar (23 IDs; modality subtypes LB3b + LB3c)

### Our IDs by Tastekin type

| root_id | side | Type/Subtype | Class / Subclass | in v783 |
|---|---|---|---|---|
| 720575940610788069 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940611875570 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940612670570 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940613601698 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940616885538 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940617000768 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940621502051 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940621754367 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940623172843 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940624963786 | L | LB4/LB4b | Gustatory / Labellar Bristle | yes |
| 720575940628853239 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940629176663 | L | LB3/LB3b | Gustatory  / Labellar Bristle | yes |
| 720575940630233916 | L | LB4/LB4b | Gustatory / Labellar Bristle | yes |
| 720575940630797113 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940632425919 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940632889389 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940633143833 | L | LB3/LB3d | Gustatory  / Labellar Bristle | yes |
| 720575940637568838 | L | LB4/LB4b | Gustatory / Labellar Bristle | yes |
| 720575940638202345 | L | LB4/LB4b | Gustatory / Labellar Bristle | yes |
| 720575940639198653 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940639259967 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940639332736 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940640649691 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |

### Tastekin LB3b + LB3c IDs not in our sugar set (45 of 57)

| root_id | side | Subtype | in v783 |
|---|---|---|---|
| 720575940621508479 | R | LB3b | yes |
| 720575940622200233 | R | LB3b | yes |
| 720575940629510338 | R | LB3b | yes |
| 720575940629884119 | R | LB3b | yes |
| 720575940610296622 | R | LB3b | yes |
| 720575940641339611 | R | LB3b | yes |
| 720575940616851286 | R | LB3b | yes |
| 720575940631656504 | R | LB3b | yes |
| 720575940617801499 | R | LB3b | yes |
| 720575940632880173 | R | LB3b | yes |
| 720575940614302370 | R | LB3b | yes |
| 720575940634023961 | R | LB3b | yes |
| 720575940607737099 | L | LB3b | yes |
| 720575940609919897 | L | LB3b | yes |
| 720575940617181725 | L | LB3b | yes |
| 720575940617937543 | L | LB3b | yes |
| 720575940622413508 | L | LB3b | yes |
| 720575940622825736 | L | LB3b | yes |
| 720575940627490663 | L | LB3b | yes |
| 720575940629025324 | L | LB3b | yes |
| 720575940639043280 | L | LB3b | yes |
| 720575940607347634 | L | LB3b | yes |
| 720575940631393484 | L | LB3b | yes |
| 720575940632510479 | L | LB3b | yes |
| 720575940612445938 | R | LB3c | yes |
| 720575940612612581 | R | LB3c | yes |
| 720575940616742657 | R | LB3c | yes |
| 720575940612010137 | R | LB3c | yes |
| 720575940622731229 | R | LB3c | yes |
| 720575940632627660 | R | LB3c | yes |
| 720575940608305161 | R | LB3c | yes |
| 720575940620296641 | R | LB3c | yes |
| 720575940620589838 | R | LB3c | yes |
| 720575940629388135 | R | LB3c | yes |
| 720575940631147148 | R | LB3c | yes |
| 720575940627907883 | R | LB3c | yes |
| 720575940606002609 | L | LB3c | yes |
| 720575940625861168 | L | LB3c | yes |
| 720575940612579053 | L | LB3c | yes |
| 720575940612950568 | L | LB3c | yes |
| 720575940622486922 | L | LB3c | yes |
| 720575940629852866 | L | LB3c | yes |
| 720575940635172191 | L | LB3c | yes |
| 720575940645332259 | L | LB3c | yes |
| 720575940623629292 | L | LB3c | yes |

Tastekin LB3b + LB3c in FlyWire: 57 cells (L 33, R 24); our set is Counter({'L': 23}) by Tastekin root side.

## bitter (42 IDs; modality subtypes LB1a + LB1b + LB1c + LB1d)

### Our IDs by Tastekin type

| root_id | side | Type/Subtype | Class / Subclass | in v783 |
|---|---|---|---|---|
| 720575940602353632 | L | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940603266592 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940604027168 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940604714528 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940610259370 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940610481370 | L | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940610483162 | L | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940610773090 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940613061118 | L | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940614281266 | L | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940615641798 | R | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940617094208 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940617239197 | R | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940617433830 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940618025199 | R | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940618682526 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940618887217 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940619028208 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940619072513 | L | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940619197093 | L | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940619659861 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940621008895 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940621778381 | L | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940621864060 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940622298631 | L | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940623183083 | R | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940624310345 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940625750105 | R | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940626287336 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940627578156 | L | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940627692048 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940628962407 | R | LB1/LB1d | Gustatory / Labellar Bristle | yes |
| 720575940629146711 | L | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940629416318 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940629481516 | R | LB1/LB1b | Gustatory / Labellar Bristle | yes |
| 720575940630195909 | L | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940634859188 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940637742911 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940638312262 | R | LB1/LB1a | Gustatory / Labellar Bristle | yes |
| 720575940642088333 | R | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940645743412 | L | LB1/LB1c | Gustatory / Labellar Bristle | yes |
| 720575940646212996 | L | LB1/LB1b | Gustatory / Labellar Bristle | yes |

### Tastekin LB1a + LB1b + LB1c + LB1d IDs not in our bitter set (0 of 42)

none

Tastekin LB1a + LB1b + LB1c + LB1d in FlyWire: 42 cells (L 21, R 21); our set is Counter({'L': 21, 'R': 21}) by Tastekin root side.

## water (18 IDs; modality subtypes LB3a)

### Our IDs by Tastekin type

| root_id | side | Type/Subtype | Class / Subclass | in v783 |
|---|---|---|---|---|
| 720575940606002609 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940612579053 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940612950568 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940613786774 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940613996959 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940616177458 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940617857694 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940622486922 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940622902535 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940625203504 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940625861168 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940629852866 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940630553415 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940631898285 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940634796536 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940635172191 | L | LB3/LB3c | Gustatory  / Labellar Bristle | yes |
| 720575940644965399 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |
| 720575940660292225 | L | LB3/LB3a | Gustatory  / Labellar Bristle | yes |

### Tastekin LB3a IDs not in our water set (19 of 30)

| root_id | side | Subtype | in v783 |
|---|---|---|---|
| 720575940615516319 | R | LB3a | yes |
| 720575940617510720 | R | LB3a | yes |
| 720575940617674909 | R | LB3a | yes |
| 720575940618601782 | R | LB3a | yes |
| 720575940621509759 | R | LB3a | yes |
| 720575940622136022 | R | LB3a | yes |
| 720575940624373483 | R | LB3a | yes |
| 720575940628116476 | R | LB3a | yes |
| 720575940629821500 | R | LB3a | yes |
| 720575940636487598 | R | LB3a | yes |
| 720575940614163367 | R | LB3a | yes |
| 720575940621506943 | R | LB3a | yes |
| 720575940627394376 | R | LB3a | yes |
| 720575940630741701 | R | LB3a | yes |
| 720575940638011994 | R | LB3a | yes |
| 720575940627821896 | L | LB3a | yes |
| 720575940616811265 | L | LB3a | yes |
| 720575940626674182 | L | LB3a | yes |
| 720575940635392910 | L | LB3a | yes |

Tastekin LB3a in FlyWire: 30 cells (L 15, R 15); our set is Counter({'L': 18}) by Tastekin root side.

## ir94e (18 IDs; modality subtypes LB1e)

### Our IDs by Tastekin type

| root_id | side | Type/Subtype | Class / Subclass | in v783 |
|---|---|---|---|---|
| 720575940610683315 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940612920386 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940614211295 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940614273292 | L | LB2/LB2c | Gustatory / Labellar Bristle | yes |
| 720575940615089369 | L | LB2/LB2c | Gustatory / Labellar Bristle | yes |
| 720575940615274425 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940619387814 | L | LB2/LB2b | Gustatory / Labellar Bristle | yes |
| 720575940621375231 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940624079544 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940624604560 | L | LB2/LB2a | Gustatory / Labellar Bristle | yes |
| 720575940626016017 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940626241636 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940627265265 | L | LB2/LB2a | Gustatory / Labellar Bristle | yes |
| 720575940628198503 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940628832256 | L | LB2/LB2b | Gustatory / Labellar Bristle | yes |
| 720575940629211607 | L | LB2/LB2c | Gustatory / Labellar Bristle | yes |
| 720575940631082124 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |
| 720575940638218173 | L | LB1/LB1e | Gustatory / Labellar Bristle | yes |

### Tastekin LB1e IDs not in our ir94e set (12 of 23)

| root_id | side | Subtype | in v783 |
|---|---|---|---|
| 720575940620692833 | R | LB1e | yes |
| 720575940611849178 | R | LB1e | yes |
| 720575940621898665 | R | LB1e | yes |
| 720575940624976572 | R | LB1e | yes |
| 720575940625450498 | R | LB1e | yes |
| 720575940625696601 | R | LB1e | yes |
| 720575940627402568 | R | LB1e | yes |
| 720575940627438906 | R | LB1e | yes |
| 720575940631204163 | R | LB1e | yes |
| 720575940637747519 | R | LB1e | yes |
| 720575940638813016 | R | LB1e | yes |
| 720575940643065032 | R | LB1e | yes |

Tastekin LB1e in FlyWire: 23 cells (L 11, R 12); our set is Counter({'L': 18}) by Tastekin root side.

## Findings (recorded, not acted on)

- 11 of the 23 frozen sugar GRNs are outside LB3b + LB3c in Tastekin's typing: 7 LB3d (high salt / heavy metal; ppk23, Ir7c, Ir47a; glutamatergic; aversive); 4 LB4b (no receptor match). 12 are LB3b + LB3c.
- The 42 frozen bitter GRNs are exactly LB1a + LB1b + LB1c + LB1d in Tastekin's typing.
- 7 of the 18 frozen water GRNs are outside LB3a in Tastekin's typing: 7 LB3c (sugar). 11 are LB3a.
- 7 of the 18 frozen ir94e GRNs are outside LB1e in Tastekin's typing: 3 LB2c (no receptor match, putatively aversive); 2 LB2a (no receptor match, putatively aversive); 2 LB2b (no receptor match, putatively aversive). 11 are LB1e.

These are differences between the Shiu et al. 2024 annotation the sets were frozen from and Tastekin's typing, not errors in our pipeline: the Phase 0 gates passed on the frozen sets as they are. Re-freezing the sets to Tastekin's typing would be a v2 change requiring a full grid rerun (docs/open_questions.md OQ-7). Not done now.
