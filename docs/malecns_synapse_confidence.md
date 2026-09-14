# MaleCNS synapse-confidence feasibility — M1g

Research only, 2026-09-14. **A precision-matched cutoff cannot currently be identified from the published figures inspected.** Higher confidence filters are technically buildable, and their graph sizes can be bounded tightly, but the required female operating-point precision and male cutoff-to-precision calibration are not established. No cutoff is selected, no recommendation is made, and no simulation or model-substrate replacement occurred.

The [accepted M1f reading](malecns_phase0.md#accepted-reading--2026-09-14) is that the two candidates bracket the desired behaviour: unscaled brain-only has graded sugar responses but fails bitter gates and runs hot; density scaling passes A–D and sugar-200 S3 but lacks coverage. “Stable” does not mean stability at every condition. No intermediate `w_syn` will be tried.

## 1. What the precision figures measure

Precision means the fraction of predicted items judged correct, not a confidence score or a synapse-capture fraction. A pre-to-post synaptic contact, a T-bar, and an aggregated neuron-to-neuron edge are distinct items. The male CSV's “connection” is a pre-to-post contact, not a multi-synapse graph edge.

| Male region / source | Connection precision | Connection recall | T-bar precision | T-bar recall |
|---|---:|---:|---:|---:|
| GNG | 94.2% | 90.0% | 70.6% | 82.6% |
| SAD | 89.5% | 91.9% | 70.8% | 87.8% |
| PRW | 80.0% | 100.0% | 73.3% | 91.2% |
| Overall, CSV | Not supplied | Not supplied | Not supplied | Not supplied |
| Overall, Berg final-paper Results | 82% | 81% | Not separately stated in that sentence | Not separately stated |

Regional numbers are direct entries in the pinned [connection CSV](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/supplemental_data/male-cns-v1.0-synapse-connection-precision-recall-by-roi.csv#L1-L82) and [T-bar CSV](https://github.com/flyconnectome/2025malecns/blob/67767d2233657983993ff6c2be48e836a935863c/supplemental_data/male-cns-v1.0-synapse-tbar-precision-recall-by-roi.csv#L1-L82). Each has 81 ROI rows, no `overall` or `SEZ` aggregate and no threshold column. GNG, SAD and PRW are reported separately; they are not pooled here. `actual_size` is ROI volume, not a validation denominator, so averaging rows or weighting by that column would not recover pooled precision. The repository README calls these Fig. 1i source data; the final paper calls the regional plot Fig. S1I.

[Berg et al., Cell 2026](https://doi.org/10.1016/j.cell.2026.08.015), p.5505, reports overall precision/recall **0.82/0.81**. STAR Methods, “EM Volume Synapse Identification,” pp.e2–e3, describes 114 validation cubes spanning 81 ROIs, 2,303 annotated T-bars and 16,870 partners. It defines synapse evaluation as requiring both components correct and refers to overall curves in Fig. S8E and regional points in S1I. The CSVs supply neither pooled true/false-positive counts nor numerical cutoffs. **Their explicit calibration to cutoff 0.5 is not established.** The supplementary S8E plot was not retrieved in this audit (publisher access returned 403), so any cutoff labels on that plot remain unchecked. No machine-readable cutoff curve was found in the source repository. The paper and regional numbers are preserved without inventing a reconciliation or multiplying T-bar and connection precision.

| Female source | Published number / cutoff | Applicability to our frozen female graph |
|---|---|---|
| Buhmann et al. 2021, Methods, Model Validation | Best validation configuration: precision **0.72**, recall **0.77**, F-score **0.74**, on 540 CREMI validation synapses | Not a measurement of the final v783 cleft-filtered graph. The selected whole-volume network was the smaller network, not that best large-network configuration. |
| Buhmann Fig. 2a | Regional precision–recall curves; best cleft-filtered F-scores **0.75/0.69/0.67/0.60** for calyx/lateral horn/ellipsoid body/protocerebral bridge | F-scores are not precision. Neither these optima nor CREMI precision provide a global precision at the final FlyWire cutoff. |
| Dorkenwald et al. 2024, Methods, Synaptic connections | Discard score **≤50**, unassigned endpoints, and duplicate annotations within 100 nm for the same partners | Defines the released filtering, but does **not** report synapse-detection precision for that exact operating point, overall or GNG. |

Sources: [Buhmann author manuscript, Model Validation and Fig. 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC7611460/); [Dorkenwald, Synaptic connections and Connection threshold](https://www.nature.com/articles/s41586-024-07558-y). Dorkenwald's 99.2% reconstruction F1 and 94% neurotransmitter majority-vote accuracy are different measurements, not synapse-detection precision. Its five-synapse edge threshold applies to selected analyses, not our [unthresholded frozen connectivity](malecns_phase0.md#m1f-edge-threshold-check--2026-09-14). The score-50 boundary is written here as Dorkenwald specifies it; it must not be numerically equated with MaleCNS confidence 0.5.

## 2. Downloadable files and reconstruction cost

The [official download page](https://male-cns.janelia.org/download/) and a complete [public bucket listing](https://storage.googleapis.com/storage/v1/b/flyem-male-cns/o?prefix=v1.0%2Fconnectome-data%2Fflat-connectome%2F&fields=items(name,size),nextPageToken) were checked on 2026-09-14. **No `minconf-0.7` or other confidence-cutoff weights file is listed.** The three weights files all use 0.5; their suffixes change the body selection, not confidence.

All names below have prefix `v1.0/connectome-data/flat-connectome/` in `gs://flyem-male-cns/`. Sizes are decimal bytes, independently obtained from the listing.

| File | Bytes | Role |
|---|---:|---|
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1,051,241,946 | Full aggregate graph |
| `connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather` | 508,025,642 | Body-filtered aggregate graph |
| `connectome-weights-male-cns-v1.0-minconf-0.5-significant-only.feather` | 502,169,298 | Body-filtered aggregate graph |
| `syn-partners-male-cns-v1.0-minconf-0.5.feather` | 6,777,179,098 | Full contact pairs with confidence and body IDs |
| `syn-partners-male-cns-v1.0-minconf-0.5-traced-only.feather` | 2,965,367,002 | Smaller contact-pair export; downloaded for this audit |
| `syn-partners-male-cns-v1.0-minconf-0.5-significant-only.feather` | 2,965,702,122 | Alternative body-filtered contact pairs |
| `syn-points-male-cns-v1.0-minconf-0.5.feather` | 13,061,489,098 | Individual points, body IDs and ROIs |
| `tbar-neurotransmitters-male-cns-v1.0.feather` | 2,651,680,218 | NT predictions; **not** detection-confidence connectivity |

Thus the advertised **2.7 GB NT file is not sufficient** to change the detection cutoff. The partner table contains `body_pre`, `conf_pre`, `body_post`, `conf_post`, coordinates and `primary_post`. The [exporter's filter](https://github.com/janelia-flyem/flyem-snapshot/blob/e6357d20044f648c3fd516d0daa4e63c8b11ee7c/flyem_snapshot/inputs/synapses.py#L356-L389) requires **both** confidence fields ≥ cutoff. Group retained pairs by body IDs to obtain weights, then apply our unchanged roster, sign rule and M1f endpoint cut. The points and NT files are unnecessary for this operation. Cutoffs below 0.5 cannot be reconstructed from these already-filtered exports.

For an exact rebuild of our original roster, use the full **6.78 GB** partner file: the traced-only subset misses some of our edges. Estimated processing budget on this machine: **1–5 minutes plus download**, roughly **8–16 GiB RAM** for an in-memory aggregation or less with streaming, and **10–20 GB disk headroom**. These are engineering estimates, not a benchmark of a completed full-file build. The smaller-table read/count/baseline audit below took **32.2 s**. At an assumed 25–100 MB/s, full-file transfer alone is about 1.1–4.5 minutes, excluding overhead. No model-ready graph was built.

## 3. Confidence distribution and resulting graph sizes

[Read-only calculation](../sim/malecns/confidence_counts.py), [hashed source and results](../data/malecns/confidence_counts.json). The downloaded table has 124,025,046 contacts; 124,009,893 survive our original roster. All **25,558,671** represented edge weights match the frozen whole-CNS graph exactly, but full-graph equality **fails**: 24,267 edges / 167,724 synapses are absent. Within the unchanged M1f brain cut, the omission is **16,873 edges / 141,179 synapses**. The subset is not silently substituted for the frozen substrate.

For cutoffs above 0.5, the lower bound counts retained contacts in the downloaded subset; the upper bound adds every omitted baseline contact/edge. This is a deterministic missing-data bound, not a confidence interval or a precision estimate. At 0.5, exact original counts are already known. Keep all 146,221 brain neurons in the denominator, including newly isolated neurons. Density is `(retained synapses / 146221) / (54492922 / 138639)`, consistent with M1f. Illustrative 0.6–0.9 values describe graph construction only; they are **not pre-declared simulation candidates**. Any cutoff above 0.5 is mechanically buildable from the full table.

| Minimum pre AND post confidence | Male brain edges | Male brain synapses | Density ratio to female |
|---|---:|---:|---:|
| 0.5, existing M1f | 21,884,935 | 101,220,515 | **1.761181** |
| 0.6 | 20,847,267–20,864,140 | 94,920,838–95,062,017 | 1.651571–1.654027 |
| 0.7 | 19,653,247–19,670,120 | 86,240,752–86,381,931 | 1.500542–1.502998 |
| 0.8 | 17,540,309–17,557,182 | 70,516,254–70,657,433 | 1.226944–1.229401 |
| 0.9 | 14,272,685–14,289,558 | 49,610,485–49,751,664 | 0.863195–0.865652 |

The result JSON also provides whole-CNS bounds at the same cutoffs. Filtering preserves the stored float32 confidence arrays and compares Python scalar cutoffs, as in the exporter's pandas filter; an independent direct pre/post-mask recount agrees at all five levels. Signs, cell sets and neuron rosters are unchanged. These counts establish retention, **not correctness**; confidence-score distributions contain no true/false-positive labels. Equal mean degree would not imply equal precision.

## 4. Is there a precision-matched cutoff?

**Not determinable from the inspected sources; existence is neither established nor ruled out.** They do not establish a female precision target for the exact filtered release or a calibrated male precision function for the joint pre/post cutoff. Consequently there is **no identified matching cutoff and no density ratio assignable to one**. The commonly quoted female 0.72 validation precision is not such a target, and the male overall 0.82 and regional CSV points cannot supply a higher-cutoff calibration. The unretrieved S8E plot remains a source-access limitation, not evidence that a calibration does not exist.

Identifying a match would require comparable ground-truth evaluation at the female release's filtering and male precision-by-cutoff data using the same unit, scoring convention and regional weighting. Raising confidence removes contacts but does not by itself establish an equal error rate across detectors, tissues or ROIs. The size bounds above do not fill that evidence gap. No M1g run is authorised or started.

## M1h source follow-up — 2026-09-14

The [Berg supplement](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009426-mmc1.pdf) was subsequently retrieved and Fig. S8E visually inspected. Its caption explicitly anchors the purple connection point to cutoff **0.5**, precision **0.82**, recall **0.81**. This resolves the earlier access limitation and the overall released-cutoff calibration above. The other points along the precision–recall curves have no confidence labels, and the two ROI CSVs have no threshold column. Recall at a newly selected cutoff therefore remains unidentifiable from these materials; it cannot be inferred by interpolating unlabeled curve positions or substituting our graph's contact-retention fraction. The female operating-point gap also remains. No precision-matched cutoff is identified; its nonexistence has not been established. [M1h](malecns_phase0.md#m1h-pre-declaration--2026-09-14) instead uses the owner's separately declared density target, not a precision or recall target.
