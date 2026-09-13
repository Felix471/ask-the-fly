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

### PhG1 + sugar-high versus existing sugar-only C2 (descriptive)

| Readout | Sugar only, n = 30, mean ± SD Hz | PhG1 + sugar, n = 10, mean ± SD Hz | Ratio |
|---|---:|---:|---:|
| MN9_L | 74.633 ± 4.476 | 82.800 ± 4.812 | 1.109424 |
| MN9_R | 54.700 ± 4.713 | 57.100 ± 2.982 | 1.043876 |
| MN11D | 92.733 ± 8.514 | 151.000 ± 6.546 | 1.628325 |
| MN11V | 37.383 ± 3.991 | 74.150 ± 3.795 | 1.983504 |
| CEM_L1 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |
| CEM_L2 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |
| CEM_L3 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |
| CEM_R1 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |
| CEM_R2 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |
| CEM_R3 | 0.000 ± 0.000 | 0.000 ± 0.000 | undefined (zero reference) |

Descriptive unpaired comparison, n=10 Phase P versus n=30 existing C2. Phase P constructs 151 Poisson units versus C2's 101, changing random-stream consumption even for reused seed values; statistical independence is not established by this layout change.
<!-- END COMPUTED PHARYNGEAL TABLES -->

### Combined-condition comparison and limits

**Does any pharyngeal type make CEM fire?** No: all six CEMs had zero spikes in
all 190 trials (1,140 CEM-neuron-trials), including all-PhG and PhG1 + sugar high.

**Does any type move MN9 or MN11 in either direction?** Yes: PhG1, PhG4 and PhG10
activated both MN9s and MN11D/V in 10/10 trials, PhG9 produced MN11-only activity,
PhG13 one MN9 R spike, and PhG16 sparse MN9/MN11 activity; suppression was not
observed against the zero baseline or in the historical-reference combined test.

For PhG1 + sugar high, MN9 L/R means were 82.800/57.100 Hz and MN11D/V means
151.000/74.150 Hz, versus 74.633/54.700 and 92.733/37.383 Hz for historical
sugar high alone. Ratios of means were **1.109424 / 1.043876 / 1.628325 / 1.983504**,
respectively: none was below one. These results do not support the proposed
PhG1 suppression under this drive design. All-PhG also remained CEM-silent,
despite MN9 L/R 23.000/18.600 Hz and MN11D/V 127.550/67.700 Hz.

The driven-cell sanity is not just a nonzero group average: **all 1,310 driven
neuron-trials fired** (1,080 pharyngeal + 230 sugar); individual rates ranged
72–148 Hz across those source-neuron trials. Individual source rates and latencies
are retained alongside the group summaries. A 100 Hz Poisson input is a designed
input rate, not a promise that the realised spike count in every 1-second trial
will be exactly 100.

The positive reference for the combined condition is the **existing C2 sugar-high
only** condition (30 trials, sugar 120 Hz, other labellar drives zero). No additional
sugar-control simulation is included in these 190 runs. Comparison with that
reference is descriptive and **unpaired**: the trial seeds and stimulation-layout
random-number consumption differ. It can flag a lower response for follow-up,
but is not a matched-control estimate of a PhG1 effect.

This is **n = 10 trials per condition, a screen, not a characterisation**. Zero
basal firing means a single type cannot lower the baseline below zero. CEM silence
under these particular inputs would not show that CEM cannot respond under another
background or drive. The [C2b connectivity audit](feeding_mn_readouts.md#c2b-cem-input-connectivity-no-simulation)
found 1,319 negative versus 488 positive unique final-leg synapses on two-hop
pharyngeal-to-CEM paths; these structural counts do not establish which paths are
active, prove inhibition of a recorded MN, or distinguish feed-forward inhibition
from other network effects.

P0 and P1 answer different questions: the paper's proposed tastant/valence labels
and MaleCNS effective-connectivity scores are not validated or refuted by this
unconditioned FlyWire stimulation screen. PhG4's response, for example, does not
justify changing its paper-derived putative valence label. MN11 activity without
MN9 under PhG9 is a candidate dissociation for further investigation, not proof
of a serial checkpoint chain; a firing CEM checkpoint was not observed here.

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
The computed tables above are copied verbatim from `tables.md`.

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

Checkpoint P1 ends here. Any 30-trial characterisation, matched-layout control,
additional background, or product checkpoint-chain design requires a new decision.
Frozen data, `site/`, scoring, encoder values and README honesty tables are unchanged.
