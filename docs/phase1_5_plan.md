# Phase 1.5: Literature-grounded input encoding (v2 groundwork)

**Status: QUEUED (2026-09-10). Gated on: Phase 1 characterization report delivered AND user has confirmed dimensionality. Not started. Must not change anything in v1.**

## Why
v1 encodes a dish as three abstract levels (sugar/bitter/water) chosen by us. v2 should encode a dish as chemical composition, then map composition to gustatory cell-class activation using published dose-response data. The connectome can only address cell classes, not receptors, so the goal is: every taste indicator collapses onto the four or five GRN classes that exist in the brain connectome, with a cited reason.

## Task A: Cell-class inventory (cheap, do first)

> **SUPERSEDED (2026-09-10).** The source list and label scheme below are replaced by **Amendment 2, "Task A, revised source"** at the end of this file. Codex: follow Amendment 2 only; this section is kept for history.

1. Check the FlyWire v783 annotations (and Engert et al. 2022, "The gustatory sensory neuron connectome of Drosophila", if its classes were integrated) for these labellar/pharyngeal GRN classes: sugar, bitter, water, Ir94e, ppk23 (glutamatergic, high-salt/pheromone-associated), and any pharyngeal GRN classes.
2. For each: does the class exist in v783, how many cells, which hemisphere, and where did the label come from. Add any newly found sets to cells.json with a hemisphere field and provenance, same standard as 0.2.
3. If ppk23 cannot be found, say so plainly. That determines whether "high salt" gets its own line or has to go through bitter only.

**Amendment (user, 2026-09-10):**
- Primary source for the GRN class inventory: Tastekin et al. 2026, *Cell* 189(18):5527–5551.e5, doi:10.1016/j.cell.2026.08.016 (the gustatory companion to the MaleCNS paper). It cross-matches GRN types between MaleCNS and FAFB/FlyWire and maps receptor driver lines (e.g. Gr33a, Gr61a, Gr64e, ppk28) to named GRN classes. Check its supplementary tables for FlyWire v783 root IDs per class. Engert et al. 2022 becomes the secondary source.
- Main table: only classes with v783 IDs we can stimulate. Appendix: classes that exist only in MaleCNS (leg GRNs, wing GRNs, most pharyngeal, any ppk23 subdivisions), marked "requires MaleCNS".
- Read the full text (not the abstract) before using either of these claims anywhere: (a) feeding is default-inhibited and sweet input acts by disinhibition; (b) the authors validated pathways with the Shiu model. Cite figure or section if true; drop if not found. cell.com blocks automated fetches (HTTP 403), so the full text must be obtained another way (user-provided PDF, institutional access, or PMC once deposited).
- See docs/open_questions.md OQ-2 for the MaleCNS constraints and the product-copy wording.

Output: docs/grn_classes.md.

## Task B: Indicator-to-class map with sources

> **SUPERSEDED (2026-09-10).** The row list below is replaced by **Amendment 2, "Task B, revised map"** at the end of this file. Codex: follow Amendment 2 only.

Produce a table mapping each taste indicator to connectome cell classes, with a citation for each row. Expected shape:
- sugars → sugar GRNs (Shiu 2024 has a sucrose-concentration-to-Hz calibration; use it as the anchor)
- bitter compounds → bitter GRNs
- water / low osmolarity → water GRNs
- fatty acids → sugar GRNs (IR56d is expressed in sweet GRNs; not separable in the connectome)
- acids → primarily bitter GRNs, plus suppression of sugar GRNs
- low salt → weak activation of sugar GRNs
- high salt → bitter GRNs plus ppk23 (if found)
- Ir94e → its own class; direction per Shiu 2024 (aversive), not labeled "salt"

For each row: which class(es), direction (excitatory drive or suppression of another class), approximate concentration-to-rate relation if the literature gives one, and the source. If a row has no usable quantitative source, mark it "direction only, magnitude designed" — do not invent numbers.

Output: docs/indicator_class_map.md.

## Task C: v2 encoder schema proposal (design only, no implementation)
Propose the v2 dish schema: chemical composition fields (sugar concentration band, bitter presence/strength, salt concentration band, acidity, fat content, free water) and the deterministic rule that turns composition into per-class Hz using Task B. Keep it a proposal in docs/encoder_v2_proposal.md. Wait for the user's decision before any code.

## Constraints
- Nothing here touches v1: stim_protocol.json, the v1 encoder, dishes.json, or the Phase 1 grid stay as they are.
- Any new cell set follows the 0.2 standard: IDs traceable to a named source, validated against v783.
- Wait for the Phase 1 water and Ir94e curves before proposing magnitudes in Task C; the connectome's sensitivity to weak drive and to suppression determines whether low-salt and acid effects are even visible at MN9.
- Phase 1.5 is v2 groundwork, gated on Phase 1 completion.

---

## Amendment 2 (user, 2026-09-10) — revised sources and new Task D. Still gated on Phase 1 completion and dimensionality confirmation.

Done immediately (not gated): OQ-2 resolved in docs/open_questions.md; parameter cross-check in docs/parameter_crosscheck.md; README honesty section; Berg items F.1–F.3 recorded in open_questions (v3 note, OQ-4); v3 note updated.

### Task A, revised source

**Before using Table S1:** confirm which FlyWire materialization version its root IDs belong to (the paper cross-matched to FAFB/FlyWire; root IDs are version-specific and change with proofreading). If the IDs are not v783, map them to v783 via github.com/flyconnectome/flywire_annotations (which carries per-version root IDs / supervoxel mappings) BEFORE any cross-check against cells.json or the v783 completeness table, and record the version and the mapping method in docs/grn_classes.md. Unmappable IDs are listed, not dropped silently.
Primary source is **Tastekin Table S1** (user will place the supplementary file in docs/papers/). It contains Body IDs for all GRN and feeding-MN cell types in both MaleCNS and FAFB/FlyWire. Use the FlyWire columns.
1. Build the class inventory from Table S1 with these labels and receptor matches (Tastekin Fig 2E, 2J, 3E, 3J, 4J):
   - LB1a–d: bitter (Gr33a), aversive
   - LB1e: Ir94e, mild aversion to amino acids/glutamate. Label "amino-acid aversion", never "salt".
   - LB2a–d: no receptor match, putatively aversive, projects to pumping/crop-entry MNs. LB2d exists only in MaleCNS.
   - LB3a: water (ppk28)
   - LB3b: sugar + low salt (Gr64f + Ir56b)
   - LB3c: sugar (Gr64f)
   - LB3d: high salt / heavy metal (ppk23, Ir7c, Ir47a), glutamatergic, aversive
   - LB4a/b: no receptor match, clusters with attractive
   - tpGRNs: dtpGRN (Gr5a, Ir60d) and ctpGRN (Ir56d, Gr64e: carbonation, fatty acids, glycerol). FlyWire has ~37 per side.
   - phGRNs PhG1–16: PhG1 = Gr64e; PhG3&4 = ppk28; PhG13 = Ir67c; PhG15 = Gr77a; PhG16 = Ir60d; PhG9/11 = Ir10a. PhG2 is a feeding-suppressing type.
   - lgAGRNs: LgAG1 = Gr33a (aversive), LgAG2 = Gr61a (appetitive). Present in FlyWire (37 per side).
   Main table = classes with FlyWire v783 IDs. Appendix = leg-local and wing GRNs (MaleCNS/MANC only).
2. Cross-check our frozen v1 sets against Table S1: overlap of our 23 sugar IDs with LB3b∪LB3c (right hemisphere), our 42 bitter IDs with LB1a–d, our water set with LB3a, our Ir94e set with LB1e. List IDs present in one but not the other. Do not modify the v1 sets; documentation only.
3. Cross-check all IDs against github.com/flyconnectome/flywire_annotations (Berg et al. revised 4.6% of FlyWire types). Note any retyped cells.

### Task B, revised map (docs/indicator_class_map.md, each row citing the Tastekin figure)
- sugars → LB3b + LB3c
- low salt → LB3b (Ir56b co-expressed in sugar GRNs); a weak drive on the sugar channel, now with a citation
- high salt → LB3d, glutamatergic aversive. Replaces the earlier "route high salt through bitter" design with a real class, if LB3d IDs resolve in v783.
- Ir94e (amino acids/glutamate) → LB1e, aversive
- water → LB3a
- fatty acids / carbonation / glycerol → ctpGRNs (taste pegs). Taste pegs are only exposed after labellar opening, and their effective connectivity to proboscis-positioning MNs differs between MaleCNS and FlyWire (Tastekin Fig S14A); characterize before using.
- bitter → LB1a–d
- acids → no labellar class identified in this paper; remains "direction only, magnitude designed"
- LB2, LB4 → not used by the encoder (no receptor identity)

### Task D (new): feeding-MN sequence readouts (design only, gated)
Tastekin typed 24 feeding MN types in both datasets (Table S1, Fig 6D). Extract FlyWire IDs for: MN9 (rostrum protraction, our current readout), MN4a (haustellum extension), MN6 (labellar extension), MN8 (labellar spreading), MN11D/MN11V (pharyngeal pumping), CEM (crop entry). Verify our frozen MN9 ID (720575940660219265) appears in their MN9 set. Propose, in docs/encoder_v2_proposal.md, a "feeding sequence" readout: for a given stimulus, which stages fire in the model. v2 product feature ("how far along the feeding sequence does the fly get"), not a change to v1. Expectation from their effective-connectivity results: LB3 and LB1a reach proboscis-positioning MNs, LB2 reaches pumping/CEM.
