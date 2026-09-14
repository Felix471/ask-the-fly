# v2 decision memo

2026-09-13. Decision proposals for the owner, not a roadmap or an authorisation
to run experiments. No new analysis or simulation accompanies this memo.

## What the product is today

Ask the Fly ranks dishes by one readout, mean left-MN9 firing, with the promise
“It only does the first bite.” [Product description](../README.md#what-the-model-does--and-what-it-doesnt), [readout provenance](feeding_mn_readouts.md#mn9-sanity-an-important-seed-distinction).
Its four labellar input axes are sugar, bitter, water and Ir94e (amino-acid
aversion), with dish-to-level assignments designed by us. [Site behaviour](site.md#behaviour), [product description](../README.md#what-you-see-on-screen).
Scores come from the frozen 400-cell grid, with 30 trials per cell, not a live
simulation. [Grid provenance](grid_provenance.md).
The brain display plays recorded, additional one-second trials rather than
the 30-trial averages used for ranking. [Replay design](site.md#replay-pack-and-brain-view).
The bilingual README honesty tables distinguish model outputs, our design
choices and what the product does not establish. [English table](../README.md#what-the-model-does--and-what-it-doesnt), [Chinese README](../README.zh.md).

## What we learned that constrains v2

(a) **CEM is not an available checkpoint under the tested design.** All six
CEM cells recorded zero spikes: labellar C1, 400 cells × 1 trial; labellar
C2, 13 × 30; pharyngeal P1, 19 × 10; pharyngeal P2, 13 × 30.
This includes all 16 PhG types separately, all 50 cells together and PhG1
combined with labellar sugar, not every possible input or background. [CEM conclusion](pharyngeal_screen.md#cem--conclusion-across-the-tested-inputs).

(b) **Pharyngeal sugar supplies drive, not evidence for an independent
additive channel.** PhG1 is putatively sugar-associated; at 100 Hz alone,
P2 mean rates were 53.867/48.167 Hz for MN9 L/R and 141.383/71.183 Hz for
MN11D/V, each over 30 trials. Combined with labellar sugar at 120 Hz, means
exceeded either alone, but all four readouts fell below their sum in 30/30
trials. Shared-target saturation is a consistent interpretation, not an
established mechanism. [P0/P2 report](pharyngeal_screen.md), [OQ-9 interpretation](open_questions.md#oq-9-pharyngeal-screen-activates-mn9mn11-but-not-cem-2026-09-13).

(c) **MN11 is not interchangeable with MN9.** In C2's 30-trial results at
sugar 120 Hz, bitter 60 Hz retained 31.8%/29.9% of no-bitter MN9 L/R versus
91.4%/93.6% for MN11D/V; at bitter 100 Hz, these were 2.28%/3.05% versus
66.19%/66.74%. The bitter veto acts on MN9 at lower bitter drives than on
MN11; this is not temporal or causal ordering. [C2 finding and limits](feeding_mn_readouts.md#c2-finding-and-limits).

(d) **Adding a brake does not by itself supply disinhibition.** Phase T
(60 conditions × 30 trials) found that CB0806 and CB0862 driven at 100 Hz
reduced left MN9 at sugar-high to 0.1 and 3.1 Hz, versus 72.7 and 73.2 Hz
without their drive. Disinhibition was not observed under the three-brake
design; sugar instead recruited CB0465, whose own undriven rate rose from
0 to 25.6 Hz across sugar levels, a feed-forward inhibitory path already
inside the frozen responses. [Phase T reading](tonic_inhibition.md#reading).

(e) **Re-typing is a change of inputs, not a clerical correction.** Seven
sugar-set cells are LB3d, seven water-set cells are LB3c, and seven Ir94e-set
cells are LB2a/b/c under Tastekin's typing. Four additional sugar-set LB4b
cells bring the mismatch total to 25/101; all 42 bitter cells match.
These are annotation differences, not a failed pipeline, and their effects
have not been isolated. [Cell-set findings](cell_set_crosscheck.md#findings-recorded-not-acted-on), [OQ-7](open_questions.md#oq-7-25-of-101-frozen-v1-grns-fall-outside-the-mapped-tastekin-subtypes-2026-09-12).

(f) **PhG4 disagreement remains unresolved.** Tastekin predicts aversion
for PhG4 (putative ppk28/water association), whereas P2 activated MN9 L/R
and MN11D/V in 30/30 trials at each nonzero dose, 60/80/120/200 Hz. [P0 association and prediction](pharyngeal_screen.md#p0--what-tastekin-reports-for-phg1phg16), [P2 disagreement](pharyngeal_screen.md#p2-findings).

## Candidates and verdicts — unranked

Closed means the specified route is unsupported under the current design;
Open means worth a bounded next decision, not ready to ship; Blocked means
a prerequisite is missing. Verdicts and next steps below are proposals based
on the linked evidence. Run counts are rough design budgets, not findings
or commitments; one run means one simulated trial.

### Checkpoint-chain readout: leg → labellum → pharynx — Closed

Close the current CEM-based route: its pharyngeal endpoint is silent, and
MN9/MN11 separation does not demonstrate a serial chain. Do not relabel
parallel firing measurements as stages reached. [CEM conclusion](pharyngeal_screen.md#cem--conclusion-across-the-tested-inputs), [C2 limits](feeding_mn_readouts.md#c2-finding-and-limits).

### Pharyngeal input axis in the product — Blocked

PhG1 changes the existing outputs, but the reports supply neither a
dish-to-pharyngeal-drive mapping nor a defensible new behavioural meaning
for a product axis; additional response curves alone would not supply those.
Unblocking requires owner-approved semantics and a source-backed or explicitly
designed mapping, without treating the inputs as independent additive channels.
[P0/P2 findings](pharyngeal_screen.md), [encoder-map gap](phase1_5_plan.md#task-c-v2-encoder-schema-proposal-design-only-no-implementation).

That prerequisite is a design decision costing **0 new runs**, not a request
for more simulation.

### MN11 as a second readout — Open

The replicated bitter separation justifies considering another displayed
measurement, not replacing MN9 or claiming how far feeding progressed. [C2 limits](feeding_mn_readouts.md#c2-finding-and-limits).

Smallest next step: a paper prototype using the existing thirteen-cell C2
tables, keeping MN11D/V separate until an explicit readout rule is chosen;
**0 new runs** for that decision, not a claim of product-wide coverage. [C2 tables](feeding_mn_readouts.md#c2-thirteen-cell-30-trial-rerun).

### Re-freezing cell sets to Tastekin's typing — Open

The mismatch warrants a controlled comparison, not silently replacing
published inputs; membership and hemisphere policy need an explicit decision.
Shipping replacement sets would require a full grid rerun and new replays. [Cell-set comparison](cell_set_crosscheck.md), [OQ-7](open_questions.md#oq-7-25-of-101-frozen-v1-grns-fall-outside-the-mapped-tastekin-subtypes-2026-09-12).

Smallest next step: approve the exact candidate sugar set, then a matched-layout
old/new sugar-only pilot at five drives and 30 trials: about **300 runs**;
this would not validate the water/Ir94e replacements or authorise re-freezing. [Set definitions](cell_set_crosscheck.md#summary), [existing five-drive design](tonic_inhibition.md#method).

### MaleCNS as the substrate — Blocked

The existing substrate audit identifies signed-edge-list reconstruction and
renewed Phase 0 checks as prerequisites; Tastekin's LB3 200 Hz → MN9 result
is precedent, not a validated drop-in migration. Unblocking requires a
versioned, model-ready substrate and a separately approved validation plan. [Substrate audit](open_questions.md#v3-note-updated-2026-09-10-malecns-as-a-substrate).

### Salt (LB3b/LB3d) as a fifth axis — Open

The 25 LB3b and 29 LB3d FlyWire IDs are available in v783, but ID availability
does not establish a separable salt response or a concentration-to-drive map. [Inventory](cell_set_crosscheck.md#feeding-mn-types-available-with-flywire-ids), [proposed mapping](phase1_5_plan.md#task-b-revised-map-docsindicator_class_mapmd-each-row-citing-the-tastekin-figure).

Smallest next step: isolated LB3b and LB3d screens in one fixed layout, at a
designed 100 Hz with other inputs undriven, plus baseline; **3 × 10 ≈ 30 runs**,
recording MN9 and MN11 before choosing any dose curve or fifth-axis mapping.
This borrows P1's screening design, not a calibrated salt concentration. [P1 design](pharyngeal_screen.md#p1--ten-trial-single-type-screen).

## What would change a Closed verdict

Checkpoint chain: reopen with a reproducibly active, input-selective pharyngeal
readout under a justified protocol/substrate, plus evidence that it and the
leg/labellar stations form a sequence rather than concurrent outputs. [Current endpoint and sequencing limits](pharyngeal_screen.md#cem--conclusion-across-the-tested-inputs), [C2 limits](feeding_mn_readouts.md#c2-finding-and-limits).

## Standing caveats

Our simulation findings are inside Shiu's FlyWire model, not calibrated against
behaviour; stimulus choices and proposed budgets are ours. [Phase T scope](tonic_inhibition.md#what-is-designed-here), [Phase P scope](pharyngeal_screen.md).
C1 is a one-trial screen, P1 a ten-trial screen; C2/P2 use 30 trials, and C2
reproduces the original grid seeds rather than adding an independent sample. [C2 provenance](feeding_mn_readouts.md#c2-thirteen-cell-30-trial-rerun), [P1/P2](pharyngeal_screen.md).
MN target labels remain the workbook's `Target_Muscle` values: MN9 `9`,
MN11D `11D`, MN11V `11V`, CEM `Crop Entry`, without added functional labels. [Source labels](feeding_mn_readouts.md#source-target-muscle-labels).
The memo changes no frozen data, scoring, site, encoder values or README
honesty-table rows; the owner chooses whether any candidate proceeds.
