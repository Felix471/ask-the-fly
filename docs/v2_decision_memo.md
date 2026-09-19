# v2 decision memo

2026-09-13, updated 2026-09-14 after M1h and male-line closure. Records the owner's salt and
cell-set decisions; other candidates remain unranked proposals, not a roadmap
or an authorisation to run experiments. Findings are taken from linked reports.

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
These are annotation differences, not a failed pipeline. R1's typed sugar33
passes all four Phase 0 gates; its count and membership effects are not
isolated. [Cell-set findings](cell_set_crosscheck.md#findings-recorded-not-acted-on), [R1 gates](salt_and_refreeze.md#full-candidate-phase-0-gates).

(f) **PhG4 disagreement remains unresolved.** Tastekin predicts aversion
for PhG4 (putative ppk28/water association), whereas P2 activated MN9 L/R
and MN11D/V in 30/30 trials at each nonzero dose, 60/80/120/200 Hz. [P0 association and prediction](pharyngeal_screen.md#p0--what-tastekin-reports-for-phg1phg16), [P2 disagreement](pharyngeal_screen.md#p2-findings).

(g) **LB3d disagreement:** 100 Hz drives left MN9 to 61.5 Hz, or 18.7 Hz
without the seven sugar-overlap cells; adding the other 22 to sugar raises
all four readouts in 10/10 trials, contrary to predicted high-salt aversion.
No explanation is assigned. [S1 and sign check](salt_and_refreeze.md#checkpoint-decisions--recorded-not-executed).

## Candidates and verdicts — unranked

Closed means the specified route is unsupported under the current design;
Open means worth a bounded next decision, not ready to ship; Blocked means
a prerequisite is missing. Decided records owner policy without execution.
Salt and cell-set decisions supersede their earlier proposals; remaining
next steps are not authorisations. One run means one simulated trial.

### Checkpoint-chain readout: leg → labellum → pharynx — Closed

Close the current CEM-based route: its pharyngeal endpoint is silent, and
MN9/MN11 separation does not demonstrate a serial chain. Do not relabel
parallel firing measurements as stages reached. [CEM conclusion](pharyngeal_screen.md#cem--conclusion-across-the-tested-inputs), [C2 limits](feeding_mn_readouts.md#c2-finding-and-limits).

### Pharyngeal input axis in the product — Blocked

PhG1 changes the existing outputs, but the reports supply neither a
dish-to-pharyngeal-drive mapping nor a signed-off user-facing meaning
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

### Cell-set policy — Decided, not executed

**v1 keeps the frozen Shiu sets.** Above 80 Hz, MN9 curve differences remain
within R1's predeclared two-SD trial-spread rule; a swap costs a full grid
rerun and new replays for prospective ranking changes the owner judges near
noise. Mixed-taste ranking changes were not measured, nor was equivalence
established. [R1 curves and limits](salt_and_refreeze.md#curves-normalised-to-their-own-200-hz-mean).

**v2 uses Tastekin typing on both brains.** In the planned two-brain design,
the male cell sets must be defined that way; the typed sugar set passes all
four Phase 0 gates on the female brain. A-prime shows that adding LB3b13 to
LB3c20 contributes 10.667 ± 6.529 Hz to left MN9 at 120 Hz, so LB3b stays in
the v2 sugar set. This records policy, not a re-freeze or male-substrate
validation. No further female-brain runs; male validation is separate.
[Owner decision and A-prime](open_questions.md#r1-checkpoint-decision-v1-retained-v2-typed-not-executed-2026-09-13).

Owner follow-up (2026-09-19): because bilateral sugar includes seven frozen
water cells, v2 re-typing must also redefine water as LB3a; M1j keeps water
unchanged. [Bilateral policy declaration](bilateral_sugar_policy.md).

### MaleCNS as the substrate — Closed after eight variants

M1i's declared whole-CNS >=5 graph at gain 0.65 matches all three
replication criteria: sugar two-cell mean 52.367 ± 2.225 Hz, bitter and
combined inputs zero, n=30 each. Their sugar drive uses 204 cells including
pharyngeal and tarsal GRNs; ours uses 17 labellar cells. With our inputs,
L10331 passes A–D, S2 and S3 but fails S1 (3/5 positive levels); overall
FAIL under the unchanged rule. R16949 remains silent. The five-trial KC
check has no criterion. [M1i results](malecns_phase0.md#m1i-results-checkpoint--2026-09-18).

The declared stop rule closes the line after M1i whatever its result.
M1c's two candidates retain their original A–D passes; S is not applied
retroactively. L10331's post-M1c selection and secondary R16949 remain
recorded. No further variant, gain, threshold change, M2 or product
integration follows. [Eight variants and original rules](malecns_phase0.md#male-line-closing-ledger--eight-variants-2026-09-18), [readout decision](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).

### Salt (LB3b/LB3d) as a fifth axis — Closed

The owner closes this route: S1 does not express high-salt aversion under
the tested design, contrary to Tastekin's LB3d prediction; the combined
response instead rises in all four readouts in 10/10 trials. Record the
disagreement without explanation or a product salt mapping. [OQ-10](open_questions.md#oq-10-salt-fifth-axis-closed--lb3d-aversion-not-expressed-under-s1-2026-09-13).

## What would change a Closed or Blocked verdict

Salt: reopen with reproducible high-salt-associated aversion under a justified, versioned input/substrate design and an explicit product mapping. [Checkpoint decision](salt_and_refreeze.md#checkpoint-decisions--recorded-not-executed).

Checkpoint chain: reopen with a reproducibly active, input-selective pharyngeal
readout under a justified protocol/substrate, plus evidence that it and the
leg/labellar stations form a sequence rather than concurrent outputs. [Current endpoint and sequencing limits](pharyngeal_screen.md#cem--conclusion-across-the-tested-inputs), [C2 limits](feeding_mn_readouts.md#c2-finding-and-limits).

Pharyngeal product axis: unblock with a dish-to-pharyngeal-drive mapping that cites its source or states an explicitly designed rule, plus a user-facing meaning signed off by the owner. [Mapping basis](phase1_5_plan.md#task-c-v2-encoder-schema-proposal-design-only-no-implementation), [Pharyngeal evidence](pharyngeal_screen.md).

MaleCNS: Closed after eight variants; M1i matches the replication criteria but fails our declared gates. Its stop rule authorises no further variant, gain, threshold change or M2. Any future reopening or product integration requires a separate owner decision; the owner has declared [M1j as a v2 bilateral-sugar policy test](bilateral_sugar_policy.md). [M1i results](malecns_phase0.md#m1i-results-checkpoint--2026-09-18), [eight-variant closing ledger](malecns_phase0.md#male-line-closing-ledger--eight-variants-2026-09-18).

## Standing caveats

Our simulation findings are inside Shiu's model, not calibrated against
behaviour; stimulus choices and proposed budgets are ours. [Phase T scope](tonic_inhibition.md#what-is-designed-here), [Phase P scope](pharyngeal_screen.md).
C1 is a one-trial screen, P1 a ten-trial screen; C2/P2 use 30 trials, and C2
reproduces the original grid seeds rather than adding an independent sample. [C2 provenance](feeding_mn_readouts.md#c2-thirteen-cell-30-trial-rerun), [P1/P2](pharyngeal_screen.md).
S1 is a ten-trial screen; R1 uses thirty-trial conditions, not a full replacement grid. [S1/R1 provenance](salt_and_refreeze.md#provenance-verification-and-limits).
MaleCNS M0 uses five-trial benchmarks; M1–M1h use thirty-trial conditions, not behavioural calibration. [Male provenance](malecns_phase0.md#provenance-and-side-convention), [closing ledger](malecns_phase0.md#male-line-closing-decision--2026-09-14).
MN target labels remain the workbook's `Target_Muscle` values: MN9 `9`,
MN11D `11D`, MN11V `11V`, CEM `Crop Entry`, without added functional labels. [Source labels](feeding_mn_readouts.md#source-target-muscle-labels).
The memo changes no frozen data, scoring, site, encoder values or README
honesty-table rows; the owner chooses whether any candidate proceeds.
