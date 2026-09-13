# Phase P: pharyngeal input screen

## P0 — what Tastekin reports for PhG1–PhG16

The PhG typing is **Tastekin's**, and the FlyWire IDs are from their **Table S1**:
the locally supplied bioRxiv v2 workbook is named
`Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx` (the Cell version calls
this Table S1), sheet `GRNs`, `Connectome = FAFB – Flywire`, pharyngeal rows.
It contains 50 FlyWire cells, all present in v783. PhG1 combines subtypes
PhG1a/b/c (2/2/4 cells); the five-cell PhG2 and PhG7 sets are preserved as supplied.

This section uses only Tastekin et al., *The complete gustatory connectome of
adult Drosophila reveals how taste guides feeding, foraging, and social behavior*,
Cell 189 (2026), 5527–5551.e5,
[doi:10.1016/j.cell.2026.08.016](https://doi.org/10.1016/j.cell.2026.08.016).
The inspected local file is `docs/papers/PIIS0092867426009438.pdf` (31 PDF pages).
No other paper supplies receptor, tastant, valence, or target assignments here.

Receptor entries are the paper's **putative morphology/driver matches**, not
confirmed receptor expression in these individual FlyWire cells. Valence is the
paper's **prediction in Figure 7F**, not a measured type-specific behavioural
response. Unknown fields are written as **not characterised**. In particular,
PhG3/4 are water-associated but drawn as putatively aversive; tastant and valence
must not be inferred from one another. Figure 7F's appetitive PhG1 assignment
also does not erase the paper's observation that some sugar-like pharyngeal GRNs
share a putative-aversive connectivity cluster (p. 5538).

All sixteen types project into the subesophageal zone (SEZ). Accessory pharyngeal
nerve (aPhN) and pharyngeal nerve (PhN) below specify **entry routes**, not named
postsynaptic neurons. Direct partners and multi-hop relationships are distinguished;
the latter are not direct GRN-to-MN contacts or predictions of LIF firing.

| Type (FlyWire cells) | Receptor / tastant association | Predicted valence | Projection / stated downstream targets | Figure or table; printed page |
|---|---|---|---|---|
| PhG1 (8) | Gr64e-GAL4 match; sweet/sugar | Appetitive | SEZ via aPhN; PhG1a–c reach insulin-producing cells (IPCs) in 3 hops; PhG1c is an exception to the generally weak effective connectivity to the MN4/6/8/9 group | Fig. 3D/E; Fig. 7F; pp. 5541, 5544 discussing S14/S15 and S18B |
| PhG2 (5) | not characterised | Aversive | SEZ via aPhN; direct GNG055 input, with a predicted indirect inhibitory route to Fdg (GNG588); high multi-hop MN connectivity, including the highest MN11V score among pharyngeal types | Fig. 3D; Fig. 5D/E; Fig. 7F; p. 5542 discussing S14D |
| PhG3 (2) | ppk28-GAL4 match jointly with PhG4; water | Aversive | SEZ via aPhN; high effective connectivity to CEM in 4 hops (MaleCNS) | Fig. 3D/E; Fig. 7F; p. 5542 discussing S14D |
| PhG4 (4) | ppk28-GAL4 match jointly with PhG3; water | Aversive | SEZ via aPhN; high effective connectivity to CEM in 4 hops (MaleCNS) | Fig. 3D/E; Fig. 7F; p. 5542 discussing S14D |
| PhG5 (2) | not characterised | Aversive | SEZ via aPhN; further type-specific named targets not characterised | Fig. 3D; Fig. 7F |
| PhG6 (2) | not characterised | Aversive | SEZ via aPhN; high effective connectivity to CEM in 4 hops (MaleCNS) | Fig. 3D; Fig. 7F; p. 5542 discussing S14D |
| PhG7 (5) | not characterised | Aversive | SEZ via PhN; high effective connectivity to CEM in 4 hops (MaleCNS) | Fig. 3D; Fig. 7F; p. 5542 discussing S14D |
| PhG8 (4) | not characterised | not characterised | SEZ via PhN; further type-specific named targets not characterised | Fig. 3D; Fig. 7F |
| PhG9 (4) | Ir10a-/Ir100a-GAL4 matches; tastant not characterised | Aversive | SEZ via PhN; its putative-aversive-I cluster shares routes converging on GNG016/GNG510/GNG056 (group-level relationship, not an assertion of each direct edge) | Fig. 3D/E and p. 5534; Fig. 5A/C and p. 5538; Fig. 7F |
| PhG10 (2) | not characterised | Appetitive | SEZ via aPhN; further type-specific named targets not characterised | Fig. 3D; Fig. 7F |
| PhG11 (2) | Likely Ir10a-/Ir100a-GAL4 morphology match; tastant not characterised | Aversive | SEZ via aPhN; further type-specific named targets not characterised | Fig. 3D/E and p. 5534; Fig. 7F |
| PhG12 (2) | not characterised | Aversive | SEZ via aPhN; comparatively weak effective connectivity to the feeding-MN groups (MaleCNS) | Fig. 3D; Fig. 7F; p. 5542 discussing S14/S15 |
| PhG13 (2) | Ir67c-GAL4 match; tastant not characterised | Aversive | SEZ via aPhN; direct GNG016 input; AN05B035 is a top partner specifically in MaleCNS; comparatively weak effective MN connectivity (MaleCNS) | Fig. 3D/E and p. 5534 discussing S6F; Fig. 5B/C; Fig. 7F; p. 5542 discussing S14/S15 |
| PhG14 (2) | not characterised | Aversive | SEZ via aPhN; direct GNG016 input; comparatively weak effective MN connectivity (MaleCNS) | Fig. 3D; Fig. 5B/C; Fig. 7F; p. 5542 discussing S14/S15 |
| PhG15 (2) | Gr77a-GAL4 match; bitter | Aversive | SEZ via aPhN; weak effective MN-connectivity cluster in FlyWire, but strong effective connectivity to MN13/MNx03 in MaleCNS | Fig. 3D/E; Fig. 7F; p. 5542 discussing S14C |
| PhG16 (2) | Ir60d-GAL4 match; tastant not characterised | Aversive | SEZ via aPhN; direct GNG016 input; comparatively weak effective MN connectivity (MaleCNS) | Fig. 3D/E; Fig. 5B/C; Fig. 7F; p. 5542 discussing S14/S15 |

Figure 3 is on printed pp. 5533–5534 (PDF pp. 8–9), Figure 5 on pp. 5537–5538
(PDF pp. 12–13; PhG2 prose continues on p. 5540), and Figure 7F on p. 5543
(PDF p. 18). The fewest-hop MN ranking is explicitly a **MaleCNS** analysis
(p. 5541); exceptions specifying FlyWire are marked above. The main text describes
PhG1a–c to IPCs through feed-forward relays including CB0041 and Sustain (p. 5544).
Its broader effective-connectivity cluster of *most* pharyngeal types also reaches
DMS and DH44 cells (p. 5542); that group statement does not assign these targets
to every one of PhG1–16. Supplementary figures S6/S14/S15/S18 were not supplied
locally: references to them above identify explicit statements in the main PDF,
not independently inspected supplementary panels.

MN target labels come only from the same workbook's FlyWire `MNs` sheet,
`Target_Muscle` column, preserved in [the MN inventory](../data/mn_readout_ids.json):
MN9 = `9`, MN11D = `11D`, MN11V = `11V`, CEM = `Crop Entry`, MN13 = `13`,
MNx03 = `Unknown`, MN6 = `6`, MN8 = `8`. The paper's aggregate MN4 label is not
an XLSX type: the workbook instead has MN4a = `4` and MN4b = `Unknown`.
Its broader MN4/6/8/9 grouping is a connectivity grouping, not a new functional
annotation supplied by this project or an assertion that PhG1c influences each
member equally.

Source SHA-256:

- Tastekin Cell PDF: `32cb56aff1f689e7968566190c8a246b842e86be06dfb4ca5b2557b24d1ef45f`.
- Table S1 workbook: `7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9`.

## P1 — ten-trial single-type screen

P1 is an experimental input design on the unchanged FlyWire v783 LIF model,
not the paper's MaleCNS effective-connectivity calculation and not a product change.
The [new protocol](../data/stim_protocol_pharyngeal.json) references the frozen
`data/stim_protocol.json`; [the runner](../sim/run_pharyngeal.py) adds stimulation
channels in memory without changing any frozen GRN set, network parameter, or score.

The authorised 18-condition screen comprises baseline, PhG1–16 separately, and
all fifty PhGs together. The additional PhG1 + sugar-high condition makes
**19 conditions × 10 trials = 190 runs**. Each PhG stimulus drives every source
cell of that type, both sides, at 100 Hz for the frozen 1-second trial; all
labellar inputs are zero except sugar at its frozen high level, **120 Hz**, in
the combined condition. PhG1 combines its three subtypes; types have unequal cell
counts (2–8), so equal per-cell drive is not equal total input across types.

Twenty channels remain present in every condition, ordered sugar, bitter, water,
ir94e, PhG1, …, PhG16, with **151 distinct Poisson units** (101 frozen labellar
cells + 50 pharyngeal cells). All-PhG activates the same sixteen channels rather
than adding duplicate stimulation units. Baseline drives none. The 100 Hz input,
choice of complete types, trial count and combined condition are our design,
not calibrated tastant concentrations or receptor-selective experimental stimuli.

Conditions have new, explicit indices: 0 baseline; 1–16 PhG1–16; 17 all-PhG;
18 PhG1 + sugar high. They use the published grid seed formula
`20260910 + 1000 * (condition_index % 40) + trial_index`, with trials 0–9.
These are new condition identities, not four-axis grid cells. The fixed 151-unit
stimulation layout differs from the grid/C2 layout of 101 units, so equal integer
seeds do **not** imply matching stochastic trajectories across those experiments.

Recorded MNs are the same twelve source neurons as C2: six CEMs individually,
MN9 L/R, both MN11D and both MN11V cells. MN9 L/R follows the frozen protocol,
which reverses the Table S1 `Root_Side` labels for those two IDs (see
[C2 conventions](feeding_mn_readouts.md#c2-thirteen-cell-30-trial-rerun)).
MN11D/V rates are the per-trial mean of their two neurons, including silent cells.
All driven pharyngeal cells' individual spike trains and rates are retained;
the combined condition also retains all 23 driven sugar cells, summarised separately.

Rates below are mean ± population SD (`ddof=0`) across ten trials, in Hz.
Latency is the median first-spike time in ms **conditional on an active trial**;
each entry carries active/10. For a two-cell MN11 type it is the earliest member's
first spike in that trial, not an average over only the firing neurons. `none`
means no spike, not a zero-millisecond latency. An empty driven-cell set is `not driven`.
Driven-cell group latency follows the same earliest-member rule; for example,
all-PhG latency is not the median of fifty individual neurons' first-spike times.

The CEM column aliases retain the workbook's sides and target `Crop Entry`:

| Alias | Table S1 Body_ID | Root_Side |
|---|---|---|
| CEM_L1 | 720575940620008112 | L |
| CEM_L2 | 720575940625799513 | L |
| CEM_L3 | 720575940640681680 | L |
| CEM_R1 | 720575940621126384 | R |
| CEM_R2 | 720575940621169690 | R |
| CEM_R3 | 720575940628781333 | R |

<!-- BEGIN COMPUTED PHARYNGEAL TABLES -->
### MN rates (mean ± population SD, Hz; n = 10)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P_baseline | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG1 | 53.200 ± 2.400 | 46.900 ± 3.390 | 140.700 ± 7.804 | 70.750 ± 3.970 |
| P_PhG2 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG3 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG4 | 37.500 ± 6.087 | 32.000 ± 2.933 | 110.600 ± 11.933 | 58.000 ± 5.527 |
| P_PhG5 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG6 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG7 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG8 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG9 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3.650 ± 2.550 | 0.050 ± 0.150 |
| P_PhG10 | 11.100 ± 5.009 | 10.900 ± 3.885 | 17.650 ± 10.267 | 8.600 ± 4.898 |
| P_PhG11 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG12 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG13 | 0.000 ± 0.000 | 0.100 ± 0.300 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG14 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG15 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG16 | 1.000 ± 1.414 | 0.700 ± 1.187 | 0.900 ± 1.221 | 0.250 ± 0.461 |
| P_all_pharyngeal | 23.000 ± 8.390 | 18.600 ± 7.158 | 127.550 ± 9.427 | 67.700 ± 4.112 |
| P_PhG1_sugar_high | 82.800 ± 4.812 | 57.100 ± 2.982 | 151.000 ± 6.546 | 74.150 ± 3.795 |

### Individual CEM rates (mean ± population SD, Hz; n = 10)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P_baseline | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG1 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG2 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG3 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG4 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG5 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG6 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG7 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG8 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG9 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG10 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG11 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG12 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG13 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG14 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG15 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG16 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_all_pharyngeal | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P_PhG1_sugar_high | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### Driven-cell rate sanity (mean ± population SD, Hz; n = 10)

| Condition | driven_pharyngeal | driven_sugar |
|---|---:|---:|
| P_baseline | not driven | not driven |
| P_PhG1 | 98.763 ± 3.738 | not driven |
| P_PhG2 | 97.740 ± 4.108 | not driven |
| P_PhG3 | 100.050 ± 6.424 | not driven |
| P_PhG4 | 98.275 ± 3.342 | not driven |
| P_PhG5 | 98.550 ± 8.816 | not driven |
| P_PhG6 | 94.300 ± 4.828 | not driven |
| P_PhG7 | 99.520 ± 2.461 | not driven |
| P_PhG8 | 99.625 ± 3.865 | not driven |
| P_PhG9 | 98.000 ± 4.271 | not driven |
| P_PhG10 | 97.900 ± 8.049 | not driven |
| P_PhG11 | 98.700 ± 3.187 | not driven |
| P_PhG12 | 98.750 ± 6.524 | not driven |
| P_PhG13 | 96.700 ± 4.308 | not driven |
| P_PhG14 | 96.550 ± 4.917 | not driven |
| P_PhG15 | 99.350 ± 4.478 | not driven |
| P_PhG16 | 96.350 ± 8.268 | not driven |
| P_all_pharyngeal | 98.702 ± 1.281 | not driven |
| P_PhG1_sugar_high | 99.825 ± 1.834 | 118.648 ± 1.939 |

### MN latency medians (ms; active trials / 10)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P_baseline | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG1 | 31.05 (10/10) | 37.60 (10/10) | 25.95 (10/10) | 27.05 (10/10) |
| P_PhG2 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG3 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG4 | 47.55 (10/10) | 49.30 (10/10) | 35.85 (10/10) | 38.05 (10/10) |
| P_PhG5 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG6 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG7 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG8 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG9 | none (0/10) | none (0/10) | 369.60 (7/10) | 549.40 (1/10) |
| P_PhG10 | 225.50 (10/10) | 227.40 (10/10) | 202.40 (10/10) | 213.70 (10/10) |
| P_PhG11 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG12 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG13 | none (0/10) | 971.00 (1/10) | none (0/10) | none (0/10) |
| P_PhG14 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG15 | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG16 | 456.80 (4/10) | 692.10 (3/10) | 741.50 (4/10) | 876.30 (3/10) |
| P_all_pharyngeal | 33.70 (10/10) | 43.55 (10/10) | 30.75 (10/10) | 31.15 (10/10) |
| P_PhG1_sugar_high | 26.25 (10/10) | 32.00 (10/10) | 24.60 (10/10) | 26.40 (10/10) |

### Individual CEM latency medians (ms; active trials / 10)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P_baseline | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG1 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG2 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG3 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG4 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG5 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG6 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG7 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG8 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG9 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG10 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG11 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG12 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG13 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG14 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG15 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG16 | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_all_pharyngeal | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| P_PhG1_sugar_high | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) | none (0/10) |

### Driven-cell latency sanity (ms; active trials / 10)

| Condition | driven_pharyngeal | driven_sugar |
|---|---:|---:|
| P_baseline | not driven | not driven |
| P_PhG1 | 0.60 (10/10) | not driven |
| P_PhG2 | 1.90 (10/10) | not driven |
| P_PhG3 | 4.00 (10/10) | not driven |
| P_PhG4 | 1.60 (10/10) | not driven |
| P_PhG5 | 5.80 (10/10) | not driven |
| P_PhG6 | 3.55 (10/10) | not driven |
| P_PhG7 | 2.35 (10/10) | not driven |
| P_PhG8 | 1.25 (10/10) | not driven |
| P_PhG9 | 3.00 (10/10) | not driven |
| P_PhG10 | 1.75 (10/10) | not driven |
| P_PhG11 | 4.45 (10/10) | not driven |
| P_PhG12 | 3.05 (10/10) | not driven |
| P_PhG13 | 2.00 (10/10) | not driven |
| P_PhG14 | 2.15 (10/10) | not driven |
| P_PhG15 | 4.40 (10/10) | not driven |
| P_PhG16 | 2.25 (10/10) | not driven |
| P_all_pharyngeal | 0.10 (10/10) | not driven |
| P_PhG1_sugar_high | 0.95 (10/10) | 0.45 (10/10) |

<!-- END COMPUTED PHARYNGEAL TABLES -->

### P1 findings and limits

**Does any pharyngeal type make CEM fire?** No: all six CEMs had zero spikes in
all 190 trials (1,140 CEM-neuron-trials), including all-PhG and PhG1 + sugar high.

**Does any type move MN9 or MN11 in either direction?** Yes: PhG1, PhG4 and PhG10
activated both MN9s and MN11D/V in 10/10 trials, PhG9 produced MN11-only activity,
PhG13 one MN9 R spike, and PhG16 sparse MN9/MN11 activity; the zero-baseline
single-type conditions cannot reveal suppression below zero.

The driven-cell sanity is not just a nonzero group average: **all 1,310 driven
neuron-trials fired** (1,080 pharyngeal + 230 sugar); individual rates ranged
72–148 Hz across those source-neuron trials. Individual source rates and latencies
are retained alongside the group summaries. A 100 Hz Poisson input is a designed
input rate, not a promise that the realised spike count in every 1-second trial
will be exactly 100.

The P1 unpaired comparison against historical C2 sugar-only trials is
**superseded by the paired P2 comparison below**. Its ratio table and conclusion
are no longer used here; the original P1 raw outputs and audit remain intact
locally. The P1 condition rates themselves are retained above as historical results.

This is **n = 10 trials per condition, a screen, not a characterisation**. Zero
basal firing means a single type cannot lower the baseline below zero. CEM silence
under these particular inputs would not show that CEM cannot respond under another
background or drive. The [C2b connectivity audit](feeding_mn_readouts.md#c2b-cem-input-connectivity-no-simulation)
found 1,319 negative versus 488 positive unique final-leg synapses on two-hop
pharyngeal-to-CEM paths; these structural counts do not establish which paths are
active, prove inhibition of a recorded MN, or distinguish feed-forward inhibition
from other network effects.

MN11 activity without MN9 under PhG9 is a candidate dissociation, not proof
of a serial checkpoint chain. The PhG4 disagreement is recorded separately in OQ-9.

### Run provenance and verification

The 190 trials completed at **2026-09-13 20:14:31 UTC**, in 119.4 seconds with
13 workers, from code commit `d6cab0a37f826f7a79b802ee60d3ae05ee42001a`.
Environment: WSL2, Python 3.10.21, Brian2 2.9.0, Cython backend / Cython 3.3.0,
NumPy 1.26.4, joblib 1.6.0. The runner records actual source-byte hashes, including
the frozen model/network and input files; these were checked again after execution.

| Source | SHA-256 |
|---|---|
| Phase P protocol | `71a40572a12aa9600afb7f63ef18e9c1535adeef6c69786ce81370478475b90a` |
| Phase P runner | `789ba7d7338fc346688d839c00773dcf9d636f912397a95c2c4f1f2573e6a0eb` |
| Frozen base protocol | `9f9495033281bfcd6f3b373551817987deb2cc083ae94ab61fece9065102d82a` |
| Frozen cell sets | `f78f5071af3bf0984e2e71326f715777c567794e03c0e6369846a147015b395a` |
| Frozen connectivity parquet | `efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347` |
| C2 sugar-only reference ledger | `014e06588470bc17bc1863f45b583fb8fe5e7a6db7daba921d61c2ad3c7af0c6` |

Local, gitignored outputs are under `results/pharyngeal/p1/`: nineteen pairs of
`P_*.npz` spike files and `P_*.json` ledgers, `individual_trials.csv`,
`group_trials.csv`, `readout_summary.csv`, `summary.json`, `tables.md`, and
`run_meta.json`. Each raw file explicitly records all ten completed trials,
seeds and saved neuron IDs, so a silent neuron is distinguishable from one not saved.
The historical control is `results/mn-readouts/c2/G_shigh_bnone_wnone_inone.{json,npz}`;
its raw spikes, source identity, seeds, readout metrics and frozen left-MN9 lookup
mean are checked before it can be used.

The runner's no-simulation validation reconstructs every saved metric from raw
spikes. A separate implementation without runner imports independently verified
all 3,590 individual rows, 2,280 grouped rows, 1,368 summary fields and all combined
ratios; its local audit is `results/pharyngeal/p1/independent_audit.json`.
The six P1 readout/sanity tables above are copied verbatim from `tables.md`;
only its superseded unpaired-comparison table is omitted.

No-simulation verification (one PowerShell command per line;
`--summarize-only` regenerates derived local summaries after validating raw files):

```powershell
.\.venv\Scripts\python.exe -B -m sim.run_pharyngeal --check-design
.\.venv\Scripts\python.exe -B -m sim.run_pharyngeal --summarize-only
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -t .
node --test site/test/app.test.mjs site/test/regress.test.mjs
.\.venv\Scripts\python.exe scripts/validate_release.py
```

Verification: Phase P 37 tests; full Python suite 169 tests; Node 67 tests;
release validator and diff checks pass. No browser change requires a UI run.

Checkpoint P1 was followed by the separately authorised P2 work below.

## P2 — dose curves and paired combination

P2 uses the same frozen model, source IDs, MN target labels, rate summaries and
conditional-latency definitions as P1. Its separate
[protocol](../data/stim_protocol_pharyngeal_p2.json) references the unchanged P1
inventory/protocol and frozen base; its [runner](../sim/run_pharyngeal_p2.py)
does not alter the executed P1 code or results.

The specified design is **390 runs**, not approximately 330:
PhG1 at 0/60/80/120/200 Hz (5 × 30), PhG4 at the same levels (5 × 30), and
three paired conditions (3 × 30). Both zero-dose rows are run separately,
not pooled or silently reused. The five drive levels come from the grid's
sugar levels, not a calibration of pharyngeal sensitivity.

All runs retain the same ordered **151-unit** stimulation layout as P1,
including both PhG1 and frozen labellar sugar cells. All other drives are zero.
The paired conditions are **(a)** sugar high alone (120 Hz), **(b)** PhG1 alone
(100 Hz), and **(c)** both, each with the **same thirty seeds**. The condition
indices are 0–4 for PhG1's curve, 5–9 for PhG4's curve, and 10–12 for a/b/c;
the seed index equals the dose-condition index, while all three paired
conditions share seed index 10. The published formula remains
`20260910 + 1000 * (seed_index % 40) + trial_index`, trials 0–29.
Thus 390 trials use 330 distinct seed values; repeating a seed across a/b/c
is intentional pairing, not additional independent evidence.

Every run saves all twelve MNs, with each CEM separate. The curve's selected
PhG cells are monitored even at zero drive; paired a/b/c all monitor the same
eight PhG1 and twenty-three sugar cells, including inactive inputs. Source-cell
firing is separate from the imposed Poisson drive rate.

For each MN readout and matched trial `t`, the reported ratio is
`r_t = c_t / a_t`; the table gives **mean ± population SD of the thirty ratios**,
not a ratio of means with an unrelated SD. Any zero denominator makes the
full thirty-trial ratio undefined, with the defined-trial count retained;
no zero is replaced by an epsilon or silently excluded.

Additivity uses the paired difference `d_t = c_t - (a_t + b_t)` in Hz,
reported as mean ± population SD and counts above/equal/below zero.
“Exceeds”, “equals” and “falls short” classify the observed mean difference,
not a statistical-equivalence test or an explanation of the network mechanism.

<!-- BEGIN COMPUTED P2 TABLES -->
### PhG1_dose: MN rate (mean ± population SD, Hz; n = 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_PhG1_0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG1_60 | 44.733 ± 4.211 | 38.133 ± 3.685 | 116.583 ± 9.037 | 56.083 ± 4.317 |
| P2_PhG1_80 | 49.800 ± 4.400 | 43.400 ± 3.565 | 131.917 ± 7.729 | 64.817 ± 3.978 |
| P2_PhG1_120 | 59.833 ± 3.716 | 52.900 ± 3.360 | 148.917 ± 7.055 | 75.283 ± 2.455 |
| P2_PhG1_200 | 69.600 ± 4.152 | 62.500 ± 3.364 | 161.633 ± 6.099 | 84.250 ± 2.886 |

### PhG1_dose: Individual CEM rate (mean ± population SD, Hz; n = 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_PhG1_0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG1_60 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG1_80 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG1_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG1_200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### PhG1_dose: Monitored source sanity rate (mean ± population SD, Hz; n = 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_PhG1_0 | 0.000 ± 0.000 | not monitored |
| P2_PhG1_60 | 59.904 ± 2.389 | not monitored |
| P2_PhG1_80 | 79.483 ± 2.919 | not monitored |
| P2_PhG1_120 | 118.346 ± 3.246 | not monitored |
| P2_PhG1_200 | 197.504 ± 6.001 | not monitored |

### PhG1_dose: MN latency (median ms; active trials / 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_PhG1_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG1_60 | 31.90 (30/30) | 35.10 (30/30) | 28.45 (30/30) | 29.85 (30/30) |
| P2_PhG1_80 | 31.10 (30/30) | 36.60 (30/30) | 27.30 (30/30) | 28.75 (30/30) |
| P2_PhG1_120 | 29.10 (30/30) | 33.30 (30/30) | 24.30 (30/30) | 25.40 (30/30) |
| P2_PhG1_200 | 27.75 (30/30) | 30.75 (30/30) | 22.25 (30/30) | 23.35 (30/30) |

### PhG1_dose: Individual CEM latency (median ms; active trials / 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_PhG1_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG1_60 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG1_80 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG1_120 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG1_200 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |

### PhG1_dose: Monitored source sanity latency (median ms; active trials / 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_PhG1_0 | none (0/30) | not monitored |
| P2_PhG1_60 | 1.90 (30/30) | not monitored |
| P2_PhG1_80 | 1.40 (30/30) | not monitored |
| P2_PhG1_120 | 0.40 (30/30) | not monitored |
| P2_PhG1_200 | 0.45 (30/30) | not monitored |

### PhG4_dose: MN rate (mean ± population SD, Hz; n = 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_PhG4_0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG4_60 | 27.767 ± 3.989 | 27.033 ± 4.750 | 92.517 ± 11.419 | 45.667 ± 5.122 |
| P2_PhG4_80 | 32.933 ± 5.033 | 30.433 ± 4.104 | 109.450 ± 10.058 | 55.533 ± 4.465 |
| P2_PhG4_120 | 38.800 ± 4.167 | 33.800 ± 4.254 | 117.917 ± 9.683 | 60.650 ± 3.878 |
| P2_PhG4_200 | 40.867 ± 3.471 | 34.933 ± 3.660 | 123.950 ± 7.141 | 63.283 ± 3.822 |

### PhG4_dose: Individual CEM rate (mean ± population SD, Hz; n = 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_PhG4_0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG4_60 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG4_80 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG4_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_PhG4_200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### PhG4_dose: Monitored source sanity rate (mean ± population SD, Hz; n = 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_PhG4_0 | 0.000 ± 0.000 | not monitored |
| P2_PhG4_60 | 58.758 ± 3.768 | not monitored |
| P2_PhG4_80 | 79.108 ± 4.920 | not monitored |
| P2_PhG4_120 | 119.225 ± 6.448 | not monitored |
| P2_PhG4_200 | 196.742 ± 7.235 | not monitored |

### PhG4_dose: MN latency (median ms; active trials / 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_PhG4_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG4_60 | 61.70 (30/30) | 63.55 (30/30) | 48.95 (30/30) | 52.70 (30/30) |
| P2_PhG4_80 | 53.00 (30/30) | 54.05 (30/30) | 41.20 (30/30) | 43.25 (30/30) |
| P2_PhG4_120 | 46.90 (30/30) | 49.25 (30/30) | 33.60 (30/30) | 35.70 (30/30) |
| P2_PhG4_200 | 42.00 (30/30) | 43.70 (30/30) | 30.60 (30/30) | 32.70 (30/30) |

### PhG4_dose: Individual CEM latency (median ms; active trials / 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_PhG4_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG4_60 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG4_80 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG4_120 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_PhG4_200 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |

### PhG4_dose: Monitored source sanity latency (median ms; active trials / 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_PhG4_0 | none (0/30) | not monitored |
| P2_PhG4_60 | 2.10 (30/30) | not monitored |
| P2_PhG4_80 | 2.40 (30/30) | not monitored |
| P2_PhG4_120 | 1.60 (30/30) | not monitored |
| P2_PhG4_200 | 0.60 (30/30) | not monitored |

### paired: MN rate (mean ± population SD, Hz; n = 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_pair_a_sugar | 73.667 ± 5.088 | 53.167 ± 3.908 | 95.250 ± 11.548 | 37.783 ± 4.387 |
| P2_pair_b_PhG1 | 53.867 ± 3.730 | 48.167 ± 3.215 | 141.383 ± 5.255 | 71.183 ± 3.275 |
| P2_pair_c_both | 83.433 ± 4.544 | 58.133 ± 4.145 | 152.367 ± 8.250 | 74.467 ± 3.568 |

### paired: Individual CEM rate (mean ± population SD, Hz; n = 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_pair_a_sugar | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_pair_b_PhG1 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| P2_pair_c_both | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### paired: Monitored source sanity rate (mean ± population SD, Hz; n = 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_pair_a_sugar | 0.000 ± 0.000 | 118.519 ± 2.127 |
| P2_pair_b_PhG1 | 98.700 ± 3.573 | 0.000 ± 0.000 |
| P2_pair_c_both | 98.700 ± 3.573 | 118.499 ± 2.128 |

### paired: MN latency (median ms; active trials / 30)

| Condition | MN9_L | MN9_R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| P2_pair_a_sugar | 35.80 (30/30) | 41.10 (30/30) | 47.05 (30/30) | 50.75 (30/30) |
| P2_pair_b_PhG1 | 31.25 (30/30) | 37.10 (30/30) | 26.65 (30/30) | 27.80 (30/30) |
| P2_pair_c_both | 27.10 (30/30) | 32.15 (30/30) | 24.60 (30/30) | 26.00 (30/30) |

### paired: Individual CEM latency (median ms; active trials / 30)

| Condition | CEM_L1 | CEM_L2 | CEM_L3 | CEM_R1 | CEM_R2 | CEM_R3 |
|---|---:|---:|---:|---:|---:|---:|
| P2_pair_a_sugar | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_pair_b_PhG1 | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| P2_pair_c_both | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |

### paired: Monitored source sanity latency (median ms; active trials / 30)

| Condition | monitored_pharyngeal | monitored_sugar |
|---|---:|---:|
| P2_pair_a_sugar | none (0/30) | 0.20 (30/30) |
| P2_pair_b_PhG1 | 1.15 (30/30) | none (0/30) |
| P2_pair_c_both | 1.15 (30/30) | 0.20 (30/30) |

### Paired combination (trial-wise mean ± population SD)

| Readout | a: sugar Hz | b: PhG1 Hz | c: both Hz | c/a | c-a-b Hz | Mean relation | Above/equal/below sum trials |
|---|---:|---:|---:|---:|---:|---|---:|
| MN9_L | 73.667 ± 5.088 | 53.867 ± 3.730 | 83.433 ± 4.544 | 1.138449 ± 0.104545 | -44.100 ± 8.467 | falls short | 0/0/30 |
| MN9_R | 53.167 ± 3.908 | 48.167 ± 3.215 | 58.133 ± 4.145 | 1.099654 ± 0.114927 | -43.200 ± 7.591 | falls short | 0/0/30 |
| MN11D | 95.250 ± 11.548 | 141.383 ± 5.255 | 152.367 ± 8.250 | 1.621558 ± 0.203065 | -84.267 ± 13.638 | falls short | 0/0/30 |
| MN11V | 37.783 ± 4.387 | 71.183 ± 3.275 | 74.467 ± 3.568 | 1.994462 ± 0.224526 | -34.500 ± 6.445 | falls short | 0/0/30 |
| CEM_L1 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM_L2 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM_L3 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM_R1 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM_R2 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM_R3 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| CEM | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| monitored_pharyngeal | 0.000 ± 0.000 | 98.700 ± 3.573 | 98.700 ± 3.573 | undefined (0/30 defined) | 0.000 ± 0.000 | equal | 0/30/0 |
| monitored_sugar | 118.519 ± 2.127 | 0.000 ± 0.000 | 118.499 ± 2.128 | 0.999829 ± 0.000208 | -0.020 ± 0.024 | falls short | 0/17/13 |

Shared active-channel Poisson spike trains verified identical for every paired trial: sugar a/c and PhG1 b/c.
<!-- END COMPUTED P2 TABLES -->

### P2 findings

Both dose curves activate MN9 L/R and MN11D/V in **30/30 trials at every
nonzero dose**, with increasing mean rates across the tested levels; both
zero-dose conditions are silent. PhG1 MN9 L rises from 44.733 ± 4.211 Hz at
60 Hz drive to 69.600 ± 4.152 Hz at 200 Hz drive. PhG4 rises from
27.767 ± 3.989 to 40.867 ± 3.471 Hz over those same drives.

**PhG4 disagreement (OQ-9):** Tastekin predicts PhG4 (putative ppk28/water
association, Fig. 3E; aversive prediction, Fig. 7F), whereas stimulating that
type drives MN9/MN11 in this model.

In the matched combination, all four MN readouts **fall short of the sum in
30/30 trials**, not just in their means. Mean paired deficits `(a+b)-c` are
44.100 Hz for MN9 L, 43.200 Hz for MN9 R, 84.267 Hz for MN11D and 34.500 Hz
for MN11V. None is superadditive or equal to the sum. All four mean `c/a`
ratios exceed one, but this is not uniform for every MN9 trial: MN9 L is
above/below a in 28/2 trials; MN9 R is above/equal/below in 22/2/6;
MN11D/V each exceed a in all thirty trials. These paired results replace
the P1 historical-reference ratio and its interpretation.

The input check compares **actual Poisson events**, not merely seed metadata:
all 690 sugar target/trial trains match exactly between a and c, and all
240 PhG1 trains between b and c. Inactive channels have no Poisson events.
The modelled source neurons' own firing is recorded separately: sugar means
118.519 Hz in a and 118.499 Hz in c despite identical imposed sugar events;
PhG1 means 98.700 Hz in both b and c. All **3,300 actually driven neuron-trials
fired**, and 1,290 monitored-but-inactive neuron-trials remain separately
identified rather than counted as failed stimulation.

### CEM — conclusion across the tested inputs

All six CEMs (Table S1 `Target_Muscle = Crop Entry`) have **zero spikes in
all 390 P2 runs**, or 2,340 CEM-neuron-trials. Every condition's individual CEM
rate is 0 ± 0 Hz and latency is none (0/30); the paired CEM ratio is undefined
(0/0 in all thirty pairs), while `c-(a+b)=0` is numerical equality of silent
readouts, not an active additive response.

This adds to C1's 400 labellar grid-cell replays, C2's thirteen labellar cells
at thirty trials, and P1's sixteen pharyngeal types, all fifty together,
baseline and PhG1 + labellar sugar. The counts below are recorded observations,
not an estimate of zero response probability for all possible drives or states.
The conclusion refers to the unchanged frozen, zero-basal-firing, 1-second
protocol and the tested source sets; no alternative background was introduced.

| Evidence | Conditions × trials | CEM-neuron-trials (six cells) | CEM spikes |
|---|---:|---:|---:|
| Labellar C1 | 400 × 1 | 2,400 | 0 |
| Labellar C2 | 13 × 30 | 2,340 | 0 |
| Pharyngeal P1 | 19 × 10 | 1,140 | 0 |
| Pharyngeal P2 | 13 × 30 | 2,340 | 0 |

no gustatory input class tested in this model (labellar, 400 cells; pharyngeal, 16 types, all 50 together, and combined with labellar sugar) drives CEM; the pharyngeal station of a checkpoint-chain readout cannot be built on CEM in this model.

### P2 provenance and verification

P2 completed at **2026-09-13 23:34:04 UTC** in 174.6 seconds with thirteen
workers, from commit `23e9bf143e7c7a6b4e5668ab9bd7bf58d006f8b3`. Environment:
WSL2, Python 3.10.21, Brian2 2.9.0, Cython 3.3.0/backend, NumPy 1.26.4,
joblib 1.6.0. All actual source-byte hashes are in `run_meta.json` and checked
after execution; the executed P1 runner/protocol and frozen model remain unchanged.

| P2 source | SHA-256 |
|---|---|
| Referencing protocol | `dda5445fcb851c0370e9085288d0111d20bd87353c53dfb386807bf54f9e7df0` |
| Runner | `9f3b254bf993470a86afb3435e21c9ae0712f9a5dfd341b36212b6d166a74035` |

Local, gitignored artifacts under `results/pharyngeal/p2/` are thirteen
`P2_*.npz` spike/event files and corresponding JSON ledgers,
`individual_trials.csv`, `group_trials.csv`, `paired_trials.csv`,
`readout_summary.csv`, `summary.json`, `tables.md`, `run_meta.json` and
`independent_audit.json`. Raw files explicitly record all thirty completion
markers, exact integer neuron inventories and seeds, plus Poisson source events.
The P2 computed block above is verbatim `tables.md`; OQ-9 includes its two MN
dose tables and paired-combination table.

Independent reconstruction without project runner/metric imports verified
9,270 individual rows, 5,130 grouped rows, 1,026 summary fields, 156 paired
statistic fields and all 930 shared source trains. The runner's own
`--summarize-only` validation independently rechecks raw identities and metrics
before regenerating derived outputs; it does not simulate.

```powershell
.\.venv\Scripts\python.exe -B -m sim.run_pharyngeal_p2 --check-design
.\.venv\Scripts\python.exe -B -m sim.run_pharyngeal_p2 --summarize-only
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -t .
node --test site/test/app.test.mjs site/test/regress.test.mjs
.\.venv\Scripts\python.exe scripts/validate_release.py
```

P2's forty tests, the full Python suite (209), Node suite (67), release
validation, P1 result revalidation and diff checks pass. No browser run is
needed for this research-only change. Frozen data, existing model/P1 code,
`site/`, scoring, encoder values and README honesty tables are unchanged.
P2 is complete; no further simulation. A separately specified v2 decision
memo is the next task, not work started in this experiment.
