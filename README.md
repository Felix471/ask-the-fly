# Ask the Fly
Ask the Fly probes how a connectome-scale fruit-fly brain model responds to taste.

## Layout
- `scripts/` — extraction and analysis utilities
- `sim/` — simulation code (added in a later phase)
- `data/` — frozen inputs, protocols, and generated results
- `docs/` — project documentation
- `vendor/` — gitignored, read-only upstream reference data and code

## Attribution and data provenance
- FlyWire v783 connectome data: CC BY-NC 4.0.
- Shiu et al. (2024), *Nature*, model code: MIT.
- Eon fly-brain benchmark repository: GPL-2.0; used as read-only reference/data, with no code copied.

## Citations
Simulation basis (what the scores come from):
- Shiu, P.K., et al. (2024). A Drosophila computational brain model reveals sensorimotor processing. *Nature*. PMC11446845. Model code (MIT): github.com/philshiu/Drosophila_brain_model.
- FlyWire v783 connectome (Dorkenwald et al. 2024; Schlegel et al. 2024), CC BY-NC 4.0.

Related work, not part of this simulation (see docs/open_questions.md, OQ-2):
- Berg, S., Beckett, I.R., Costa, M., … Hess, H.F., Rubin, G.M., Jefferis, G.S.X.E. (2026). Sexual dimorphism in the complete Drosophila male central nervous system connectome. *Cell* 189(18), 5504–5526.e15. https://doi.org/10.1016/j.cell.2026.08.015 (MaleCNS; male brain + VNC).
- Tastekin, I., de Haan Vicente, I., Beresford, R.J., Morris, B.J., Beckett, I., Schlegel, P., Gkantia, M., Marin, E.C., Costa, M., Jefferis, G.S.X.E., Ribeiro, C. (2026). The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior. *Cell* 189(18), 5527–5551.e5. https://doi.org/10.1016/j.cell.2026.08.016.

Product copy for provenance: "Scores come from a published female-brain LIF model (Shiu 2024 / FlyWire v783). The September 2026 papers describe a more complete taste wiring diagram that is not part of this simulation."

## Honesty: what this simulation does and does not do
| Claim | Status | Source |
|---|---|---|
| Scores come from a published female-brain LIF model on FlyWire v783 | yes | Shiu et al. 2024; docs/phase0_report.md |
| Sugar drives, bitter suppresses, MN9 as the proboscis-extension readout | reproduced (directions) | docs/phase0_report.md, gates A–D |
| The model has spontaneous activity | **no** — baseline is 0 Hz by construction | Shiu 2024 Methods; our condition D |
| Disinhibition (the enriched LB3 → Quasimodo → MN motif) is expressed | **no** — zero basal firing means there is no tonic inhibition to release; v1 captures the feedforward Clavicle path only | Tastekin et al. 2026, Fig 6I/6J, Fig S17; docs/open_questions.md OQ-3 |
| Covers the whole feeding sequence | **no** — real feeding is a chain of checkpoints: leg bristles → labellar bristles → taste pegs → pharynx. This simulation covers the labellar-bristle checkpoint only. | Tastekin et al. 2026, Discussion, "Sequential checkpoints and action control" |
| Water is a separate taste quality in the model | **no** — in this model water acts as a second appetitive drive that mainly boosts weak sugar (sugar 40 Hz + water 40 Hz gives 24 Hz MN9 vs 4 Hz alone; at sugar 200 Hz it adds 7%). That is why a wet savory dish outranks a dry one. This is a property of the connectome model, not a rule we wrote. | docs/phase1_characterization.md, sugar × water |
| Uses the September 2026 complete gustatory wiring (MaleCNS) | **no** — a different animal, not part of this simulation | docs/open_questions.md, v3 note |

In this model weak water is only visible as a helper to sugar; the fly notices water when the food is mostly water. The lookup grid therefore gives water "low" and "medium" the same cell (60 Hz): the fixed-path recheck (docs/fixed_path_recheck.md) could not separate them on any curve.

Product line: "It only does the first bite."
