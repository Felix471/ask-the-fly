# Cell IDs

Cell IDs are extracted without executing the vendor notebooks. `data/cells.json` is the machine-readable record.

| Set | Count | Source | Present in v783 |
|---|---:|---|---:|
| sugar | 23 | `example.ipynb::sugar_GRNs` | 23 |
| sugar_bench21 | 21 | `benchmark.py::EXPERIMENTS.sugar.neu_exc` | 21 |
| sugar_fig21 | 21 | `figures.ipynb::neu_sugar` | 20 |
| sugar_left10 | 10 | `figures.ipynb::neu_sugar_left` | 9 |
| bitter | 42 | `example.ipynb::bitter_GRNs` | 42 |
| bitter_fig21 | 21 | `figures.ipynb::neu_bitter` | 20 |
| water | 18 | `figures.ipynb::neu_water` | 18 |
| ir94e | 18 | `figures.ipynb::neu_ir94e` | 18 |

## Overlaps

The primary sugar set shares 19 IDs with the figures set and 20 with the benchmark set. The figures and benchmark sugar sets share 20 IDs, so they are not identical; 19 IDs are common to all three. The left-hemisphere sugar set shares no IDs with any of those sets. The primary bitter set contains 20 of the 21 figure bitter IDs.

## MN9 and aggregation

The primary IDs from `example.ipynb` are left `720575940660219265` and right `720575940618238523`; both are present in v783. `figures.ipynb` uses the same left ID but lists right `720575940645521262`, which is absent from v783. The frozen readout is therefore `left_only`, matching the paper's contralateral left-MN9 readout. Right MN9 is still recorded and reported, but it is not used for gates. Side-label note (2026-09-12): Tastekin et al.'s supplementary table and the Schlegel et al. 2024 annotation label `720575940660219265` as R and `720575940618238523` as L by soma side; our "left MN9" for the former follows Shiu's contralateral naming, so the two conventions describe the same two neurons and nothing is swapped (docs/cell_set_crosscheck.md).
