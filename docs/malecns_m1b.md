# MaleCNS M1b: saved-spike diagnosis

M1b only: **zero simulations**. All 480 saved M1 trials are inspected (16 conditions, 30 each), including A′. Each one-second recording is checked against its saved spike hash and MN9 counts. A200 and B0 are identical-drive/seed repeats, not 60 independent observations. No change to the female pipeline, either frozen substrate, site, scores, or primary-readout choice.

Sources: [M1 report](malecns_phase0.md), [M1b summary/provenance](../data/malecns/m1b_diagnosis.json), [analysis code](../sim/malecns/diagnose_m1.py). Full per-trial ledger, source hashes, 50-ms spike bins, regional counts, and selected partner IDs are retained locally at `data/malecns/runs/m1b/full_diagnosis.json`, with its hash in the versioned summary.

## Network activity per condition

Median [minimum–maximum] across 30 trials. Neurons fired means distinct neuron IDs with at least one spike in [0, 1 s); Poisson-source events are not network spikes.

Female columns are existing full-network grid replays: **n=1**, different seeds, not paired with male trials. A25/0 and C0/25 do not exist in the frozen grid (sugar levels 0/60/80/120/200, bitter 0/30/60/100/160); no substitute or new run was used. A dash means not requested. [Replay files, seeds and hashes](../data/malecns/rescale_preflight.json); [grid provenance](grid_provenance.md).

| Condition: sugar/bitter Hz | Male network spikes | Male neurons fired | High-count trials / 30 | Female spikes (n=1) | Female neurons (n=1) |
|---|---:|---:|---:|---:|---:|
| A_s25_b0 | 315,526 [101,199–987,904] | 17,778 [7,552–18,643] | 13 | no 25 Hz cell | no 25 Hz cell |
| A_s50_b0 | 935,017 [144,175–1,048,059] | 18,421.5 [8,155–18,857] | 25 | — | — |
| A_s100_b0 | 1,107,911 [994,456–1,141,791] | 18,125 [17,698–18,596] | 30 | — | — |
| A_s200_b0 | 1,156,672.5 [1,132,192–1,166,319] | 17,709 [17,369–17,975] | 30 | 17,150 | 402 |
| B_s200_b0 | 1,156,672.5 [1,132,192–1,166,319] | 17,709 [17,369–17,975] | 30 | — | — |
| B_s200_b25 | 1,146,230.5 [1,100,800–1,156,474] | 17,771 [17,449–18,060] | 30 | — | — |
| B_s200_b50 | 1,148,973.5 [1,097,898–1,158,387] | 17,650 [17,442–18,226] | 30 | — | — |
| B_s200_b100 | 1,152,283.5 [1,114,405–1,157,934] | 17,652.5 [17,406–17,880] | 30 | 18,219 | 401 |
| B_s200_b200 | 1,164,084 [1,129,965–1,170,541] | 17,741.5 [17,444–17,990] | 30 | — | — |
| C_s0_b25 | 1,062,197 [224,387–1,091,812] | 18,028.5 [8,716–18,361] | 29 | no 25 Hz cell | no 25 Hz cell |
| C_s0_b50 | 1,096,009 [1,064,489–1,121,085] | 17,984.5 [17,564–18,385] | 30 | — | — |
| C_s0_b100 | 1,097,902 [237,110–1,112,628] | 18,018 [8,799–18,345] | 29 | — | — |
| C_s0_b200 | 1,113,387.5 [1,092,999–1,134,876] | 17,994.5 [17,548–18,345] | 30 | — | — |
| D_s0_b0 | 0 [0–0] | 0 [0–0] | 0 | 0 | 0 |
| AP_sugar_120 | 1,128,043.5 [1,104,520–1,143,597] | 17,963 [17,548–18,255] | 30 | — | — |
| AP_sugar_lb3c_120 | 1,100,944.5 [866,930–1,138,771] | 18,391 [18,053–18,734] | 30 | — | — |

## Quiet / runaway split

**Descriptive analyst rule, not a biological threshold or gate:** quiet <500,000 network spikes in one second; runaway/high-count ≥500,000. “Quiet” is relative and does not mean silent. One shared threshold is applied without looking at MN9 to assign groups; this is a post-hoc screen, not proof of two discrete dynamical states. The threshold does not affect density or either proposed rescaling. Rates below are mean ± population SD, Hz, within the indicated group.

| Condition | Group | n | MN9 R, contra | MN9 L, ipsi |
|---|---|---:|---:|---:|
| A_s25_b0 | quiet | 17 | 16.471 ± 13.899 | 64.176 ± 49.626 |
| A_s25_b0 | runaway | 13 | 2.462 ± 3.153 | 15.385 ± 14.835 |
| B_s200_b25 | quiet | 0 | — | — |
| B_s200_b25 | runaway | 30 | 0.000 ± 0.000 | 9.700 ± 29.703 |
| C_s0_b25 | quiet | 1 | 0.000 ± 0.000 | 130.000 ± 0.000 |
| C_s0_b25 | runaway | 29 | 0.000 ± 0.000 | 15.172 ± 38.130 |

Sensitivity: high-count trial counts at alternative descriptive cutoffs (no gate recalculation):

| Cutoff (spikes) | A25/0 | B200/25 | C0/25 |
|---|---:|---:|---:|
| 300,000 | 15 | 30 | 29 |
| 500,000 | 13 | 30 | 29 |
| 750,000 | 12 | 30 | 29 |

## Onset and anatomical distribution in high-count trials

Time to 1,000 means the timestamp of the 1,000th sorted whole-network spike, measured from stimulus onset; it is not necessarily the onset of the later high-activity episode.

**Source limitation:** the frozen v1.0 body annotations contain no `region` column. We instead use the documented `superclass` anatomy in [Berg et al., Methods: Cell annotations / Superclass](https://doi.org/10.1016/j.cell.2026.08.015). `cb_*`, `ol_*` and visual projection/centrifugal classes are brain; `vnc_*` are VNC; ascending/descending classes are crossing; ENS remains unclassified. This is a neuron-class proxy, not anatomical localization of each spike or synapse. Crossing neurons are not assigned to a single region. Exact mapping and population sizes are in the [M1b record](../data/malecns/m1b_diagnosis.json).

First window = [0, 50 ms); last window = [500, 1,000 ms). The following four-part cells give mean distinct neurons per trial as **brain / VNC / crossing / unclassified**. All high-count conditions are shown, not only the three highlighted gate failures.

| Condition | n | Time to 1,000, ms: median [min–max] | First 50 ms: neurons | Last 500 ms: neurons |
|---|---:|---:|---|---|
| A_s25_b0 | 13 | 133.9 [96.1–453.9] | 21.8 / 1.5 / 3.0 / 0.0 | 13953.4 / 1811.7 / 582.5 / 0.0 |
| A_s50_b0 | 25 | 80.5 [60.7–190.3] | 67.1 / 17.0 / 17.1 / 0.0 | 13964.6 / 1854.2 / 586.8 / 0.0 |
| A_s100_b0 | 30 | 56.1 [49.1–79.7] | 215.8 / 113.8 / 76.0 / 0.0 | 13835.8 / 1851.1 / 573.8 / 0.0 |
| A_s200_b0 | 30 | 39.5 [35.7–45.1] | 2903.8 / 246.3 / 160.7 / 0.0 | 13863.3 / 1810.8 / 569.5 / 0.0 |
| B_s200_b0 | 30 | 39.5 [35.7–45.1] | 2903.8 / 246.3 / 160.7 / 0.0 | 13863.3 / 1810.8 / 569.5 / 0.0 |
| B_s200_b25 | 30 | 38.4 [35.2–43.4] | 2896.7 / 209.7 / 155.0 / 0.0 | 13963.2 / 1747.5 / 586.3 / 0.0 |
| B_s200_b50 | 30 | 36.6 [32.9–38.5] | 2862.9 / 334.8 / 167.0 / 0.0 | 13982.2 / 1762.9 / 587.1 / 0.0 |
| B_s200_b100 | 30 | 31.6 [27.8–33.1] | 2658.5 / 496.7 / 194.9 / 0.0 | 13980.6 / 1773.0 / 584.1 / 0.0 |
| B_s200_b200 | 30 | 26.1 [24.5–27.9] | 3171.7 / 611.1 / 227.0 / 0.0 | 13990.5 / 1801.0 / 585.8 / 0.0 |
| C_s0_b25 | 29 | 47.0 [42.5–51.7] | 570.6 / 132.2 / 79.2 / 0.0 | 13877.5 / 1805.7 / 575.5 / 0.0 |
| C_s0_b50 | 30 | 40.5 [36.1–44.3] | 807.4 / 342.7 / 139.5 / 0.0 | 13888.3 / 1816.1 / 580.2 / 0.0 |
| C_s0_b100 | 29 | 34.1 [31.1–36.3] | 967.2 / 552.4 / 195.2 / 0.0 | 13918.3 / 1838.3 / 586.2 / 0.0 |
| C_s0_b200 | 30 | 27.9 [26.4–29.9] | 1147.3 / 573.2 / 196.3 / 0.0 | 13937.0 / 1873.5 / 591.0 / 0.0 |
| AP_sugar_120 | 30 | 51.4 [42.0–66.1] | 495.4 / 155.7 / 101.6 / 0.0 | 13837.2 / 1879.2 / 570.2 / 0.0 |
| AP_sugar_lb3c_120 | 30 | 52.3 [48.8–63.9] | 249.0 / 175.2 / 93.8 / 0.0 | 13864.6 / 1871.6 / 580.8 / 0.0 |

For the three highlighted conditions, pooled spike shares within each window (not neuron fractions; unclassified is retained in the denominator):

| Condition | Window | Brain | VNC | Crossing | Unclassified |
|---|---|---:|---:|---:|---:|
| A_s25_b0 | early | 86.96% | 3.93% | 9.11% | 0.00% |
| A_s25_b0 | late | 93.37% | 4.48% | 2.16% | 0.00% |
| B_s200_b25 | early | 89.28% | 5.46% | 5.26% | 0.00% |
| B_s200_b25 | late | 93.91% | 3.90% | 2.19% | 0.00% |
| C_s0_b25 | early | 74.70% | 14.21% | 11.10% | 0.00% |
| C_s0_b25 | late | 93.85% | 3.99% | 2.16% | 0.00% |

In the 72 high-count trials of these three highlighted conditions, an additional 20-bin (50 ms per bin) audit finds **no individual-trial bin with a VNC majority of spikes**. Maximum pooled VNC shares across the 20 bins are A_s25_b0: 38.31%, B_s200_b25: 5.46%, C_s0_b25: 22.21%. The two requested endpoint windows are brain-dominated by both spikes and recruited-neuron counts. **VNC is briefly the largest category (but not a majority)** in three individual A25 bins: trial 3 at 50–100 ms (561/1,202 spikes, 46.67%), trial 9 at 200–250 ms (137/285, 48.07%), and trial 16 at 50–100 ms (215/487, 44.15%). Thus transient VNC plurality is observed, not sustained VNC-dominated late activity. This does not test VNC causality or exclude a VNC contribution.

## Synaptic in-degree and the two proposed scaling rules

In-degree here is **unsigned incoming synapse count**, `sum(Connectivity)` per postsynaptic neuron, not distinct-partner count or signed excitation minus inhibition. All-roster statistics include isolated and zero-input neurons. Female is the frozen v783 substrate; male is frozen whole CNS. For each MN9 we rank presynaptic partners by synapses **onto that MN9**, with numeric body ID breaking ties, then measure each selected partner’s **entire incoming** synapse count.

| Population | Female n | Male n | Female mean / median | Male mean / median | Male/female mean ratio | Median ratio |
|---|---:|---:|---:|---:|---:|---:|
| All neurons | 138639 | 166700 | 393.056 / 198.0 | 744.917 / 346.0 | 1.895191 | 1.747475 |
| contra MN9 partners (available up to 200) | 200 | 137 | 1832.370 / 1409.5 | 3628.219 / 2678.0 | 1.980069 | 1.899965 |
| ipsi MN9 partners (available up to 200) | 200 | 200 | 1820.750 / 1399.5 | 3625.085 / 2694.5 | 1.990984 | 1.925330 |

**Exact 200-per-MN9 specification cannot be met:** male R16949 has 137 partners total (male L has 278; female contra/ipsi have 227/241). Its displayed statistics use all 137, explicitly not 200. No zero padding or invented partners. Therefore the requested exact `r_mn9` was left undefined at M1b. The owner subsequently approved this available-partner exception before M1c, with equal weighting of the two side means.

| MN9 relative side | Female incoming synapses | Male incoming synapses |
|---|---:|---:|
| contra | 5,579 | 556 |
| ipsi | 5,886 | 6,012 |

Use of **means** (not medians) gives `r_all = 1.895191250`, hence `0.275 / r_all = 0.145104089 mV`.

The owner-confirmed definition is **min(200, available) partners per MN9**, then the ratio of equally weighted side means: `(male_contra_mean + male_ipsi_mean) / (female_contra_mean + female_ipsi_mean)`. Shared partners count once in each neighborhood; this is not a pooled 337-versus-400 mean. That alternative gives `1.985509367` and `0.138503502 mV`. Both definitions were accepted before any M1c gate outcome. Full-precision ratios are used; the displayed weights round to 0.145104 and 0.138504 mV. These are pre-declared design definitions, not values selected by searching gate outcomes.

Changing `w_syn` also changes the existing external Poisson kick `w_syn * f_poi`; `f_poi` and that formula would remain unchanged. This is not a recurrent-edge-only rescaling. Source: [unchanged network builder](../sim/network.py).

## MN9 tracing-status check before M1c

Sources: [neuPrint male-cns:v1.0](https://neuprint.janelia.org/), [release annotation provenance](../data/malecns/substrate_record.json), and Tastekin Table S1 (local workbook `MNs!A66:G67`). The [preflight record](../data/malecns/rescale_preflight.json) records the query response hash, release fields, workbook hash and exact IDs.

| Body / XLSX side | status (live and release) | statusLabel (live and release) | neuPrint pre / post | Retained incoming synapses |
|---|---|---|---:|---:|
| 16949 / R | Traced | RT Hard to trace | 244 / 633 | 556 |
| 10331 / L | Traced | Roughly traced | 172 / 6,358 | 6,012 |

Neither record provides a numerical tracing-completeness field or a cropped flag; absent metadata is unknown, not evidence of complete tracing. Both have `exitNerve=PhN` and `group=10331`. neuPrint post counts differ from the proofread-endpoint-filtered substrate incoming counts. The workbook, Berg release annotations and live type query identify only these two MN9 bodies: no alternative MN9-typed body on either side. Reconstruction incompleteness is a likely cause of the laterality reversal given the R tracing label and 556 versus 6,012 retained inputs, **a hypothesis, not established causation**; both M1c sides must be read before drawing a conclusion. [OQ-11](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).

### Additional mapping and ROI-capture check

**Source check only; no new conclusion.** In the [cross-brain mapping](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/supplemental_data/mcns_fw_edge_comp_mappings.json), both female MN9 IDs `720575940660219265` and `720575940618238523` have the label **CB0701**. Exactly two male bodies share that label: **10331 and 16949**. Thus **16949 is included**. These four IDs are the complete label group; this mapping is a cross-matched group assignment, not a one-to-one left/right pairing.

The saved neuPrint response (`male-cns:v1.0`, retrieved 2026-09-14T08:23:39.950382+00:00) gives the following status and postsynaptic ROI counts. The local body-annotation export has no dendrite-ROI field; `roiInfo.post` identifies input locations, **not explicitly segmented dendritic arbors**.

| Male body / side | status | statusLabel | Mapping label | GNG postsynapses | CentralBrain-unspecified postsynapses |
|---|---|---|---|---:|---:|
| 16949 / R | Traced | RT Hard to trace | CB0701 | 433 | 200 |
| 10331 / L | Traced | Roughly traced | CB0701 | 4,920 | 1,438 |

These leaf counts sum to 633 (R) and 6,358 (L). `CentralBrain` is the parent ROI, not an additional disjoint compartment. Both leaf ROIs contain postsynapses in both bodies.

The requested [capture CSV](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/supplemental_data/male-cns-v1.0-traced-synapse-capture-by-roi.csv) reports ROI-wide fractions:

| ROI | Presynapses on proofread neurons | Postsynapses on proofread neurons | Connections with both endpoints proofread |
|---|---:|---:|---:|
| GNG | 90.7709% | 35.3665% | 32.2026% |
| CentralBrain-unspecified | not reported | not reported | not reported |
| CentralBrain (parent, context only) | 94.5107% | 36.8483% | 35.1027% |

GNG is CSV line 31; CentralBrain is line 3 (header counted). There is no `CentralBrain-unspecified` row and no left/right GNG breakdown. The parent fraction is not substituted for the missing leaf fraction. These are **ROI-wide capture fractions, not either MN9’s tracing-completeness percentage**. [Source definitions](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/README.md#synapse-capture); [extracted fields, source commit, sizes and SHA256 hashes](../data/malecns/mn9_mapping_capture.json). No simulation, body substitution, verdict or causal conclusion is added.

## Tastekin comparison

[Tastekin Figure S17B, condition 1](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc1.pdf) shows LB3 activation at 200 Hz as an MN9 boxplot, n=30. No exact numerical mean or median is printed next to that condition; visual inspection places its median at approximately **105 Hz** (graph estimate, not an extracted numerical result). Our M1 means are **34.367 Hz R / 129.800 Hz L**. The caption does not identify the MN9 side or equate its LB3 pool with our one-sided typed17; this is not an established matched-condition replication.

Supplement: 28-page publisher PDF, Figure S17 on PDF page 18, legend on page 27; 16,121,775 bytes; SHA256 `099586a04f8ff0f02bf0fd9bcf8cedfa7531cffced664720e43d6800011d71a7`. Downloaded to ignored `data/malecns/downloads/Tastekin_Cell_2026_supplement_mmc1.pdf`. The [main paper](https://doi.org/10.1016/j.cell.2026.08.016) describes robust firing but does not provide an exact LB3-only rate in its modelling passage.

## What the failure is

The unscaled male model recruits a broad brain-and-VNC population after gustatory drive, but not the entire network: typically about 18,000 of 166,700 neurons fire, and late activity is predominantly in brain-class neurons. Sugar25 has a wide spread of network spike counts; its high-count trials have **lower**, not higher, mean MN9 rates than its low-count trials. All sugar200/bitter25 trials are high-count despite their variable L-MN9 response, and bitter25 alone can drive L even in the one low-count trial. The failure is therefore not merely rare network runaways inflating MN9 averages: network activity and MN9 selection/suppression are distinct outcomes under this design. Higher unsigned density and strongly asymmetric direct MN9 input are measured structural differences, not proven causes; saved spikes alone do not establish which feedback circuit or parameter caused the failed gates. Density rescaling remains a pre-declared test, not an already justified cure.

## Verification

All 480 trial counts/seeds, condition medians/ranges, window/bin totals, and 737 selected partner rows were cross-checked; incoming degrees were reconstructed independently using grouped sums. Onset and regional counts were independently rechecked from raw spikes for the 72 highlighted high-count trials. The [audit summary](../data/malecns/m1b_audit.json) references the full local bin ledger at `data/malecns/runs/m1b/audit.json`. Thirty male-only unit tests (including five diagnosis tests), 315 existing Python tests, 67 Node tests and release validation passed. These software checks do not change any M1 gate verdict.

## Checkpoint

The [pre-declared M1c stop rule](malecns_phase0.md#m1b--m1c-decision-boundary-declared-before-rescaled-runs) was recorded before any rescaled run. The owner accepted M1b and both mean-based definitions, including the 137-partner exception. M1c uses exactly these two weights and the unchanged tied external kick; no third weight will be tried.
