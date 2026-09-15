"""Render M1h substrate checkpoint from its saved record; no simulation."""
from collections import Counter
import json
from sim.malecns.density_match_substrate import RECORD


def generate():
    r = json.loads(RECORD.read_text())
    c, d = r['counts'], r['density']
    lines = ['## M1h substrate checkpoint — 2026-09-14', '',
             '**STOP before simulation:** 79 of 91 input cells lose more than half their incoming synapses. Neither MN9 crosses that threshold. No M1h trial has run.', '',
             'Density-only declaration `a8234d3`; builder `5187492`. Full-file contacts reproduce every M1f brain edge count at0.5 exactly. Same roster, endpoint cut and signs; VNC-local contacts between retained crossing neurons remain. The cutoff is selected without reading any trial activity.', '',
             '| Measure | Value |', '|---|---:|',
             f"| `c*` (display) | {r['c_star']:.3f} |",
             f"| `c*` (exact stored float32 value) | {r['c_star']!r} |",
             f"| Neurons, including isolated | {c['neurons']:,} |",
             f"| Edges | {c['edges']:,} |", f"| Synapses | {c['synapses']:,} |",
             f"| Male mean unsigned in-degree | {d['male_mean']:.9f} |",
             f"| Female mean unsigned in-degree | {d['female_mean']:.9f} |",
             f"| Ratio | {d['ratio']:.9f} |", f"| M1f ratio at0.5 | {d['baseline_ratio']:.9f} |",
             f"| Contacts retained versus brain0.5 | {r['retention']['contacts_fraction']:.4%} |", '',
             f"Full [partner file]({r['source_url']}): **{r['source']['bytes']:,} bytes**; SHA256 `{r['source']['sha256']}`. [Substrate record, exact histogram, per-cell degrees and artifact hashes](../data/malecns/substrate_record_density_matched.json). Build/count/audit wall time {r['wall_seconds']:.1f}s, excluding download. No Brian2 run.", '',
             'The selected breakpoint is the closest density match among all486,079 distinct stored brain confidence values. Neighbouring achievable choices establish the discontinuity; no contacts tied at the cutoff are selectively removed:', '',
             '| Cutoff | Retained synapses | Density ratio |', '|---|---:|---:|']
    for x in r['selection']['neighbouring_breakpoints']:
        lines.append(f"| {x['cutoff']!r} | {x['synapses']:,} | {x['ratio']:.9f} |")
    lines += ['', '### Synapses per edge', '', '| Synapses per edge | Number of edges |', '|---|---:|']
    hist = r['synapses_per_edge_histogram']
    for w in [1, 2, 3, 4]:
        lines.append(f"| {w} | {sum(x['edges'] for x in hist if x['synapses_per_edge']==w):,} |")
    lines += [f"| ≥5 | {sum(x['edges'] for x in hist if x['synapses_per_edge']>=5):,} |",
              f"| Total | {c['edges']:,} |", '',
              'The record contains every integer-weight bin, not just the grouped ≥5 bin.', '',
              '### Recall cost and source limitation', '',
              'The newly retrieved [Berg supplement, Fig. S8E](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009426-mmc1.pdf) explicitly reports precision0.82 and recall0.81 at released cutoff0.5. The rest of its precision–recall curve has no confidence labels. The published ROI connection/T-bar tables likewise contain no cutoff column. Therefore **recall at0.869 is unavailable from these sources**, not0.81 and not56.8%. Contact retention is a graph-size measurement, not ground-truth recall; neither multiplication by0.81 nor interpolation along an unlabeled curve establishes it. This missing calibration is a cost uncertainty at the checkpoint. Supplement SHA256 `a7bd4e6e572a658635f082ae7e812b096ef0f7c9b964bb7adf35d207191572fb`,10,650,236 bytes; whole S8 page and caption visually inspected. See the [M1g source follow-up](malecns_synapse_confidence.md#m1h-source-follow-up--2026-09-14).', '',
              '### Incoming synapse loss before any run', '',
              'Comparison is within the same M1f brain roster at0.5, not the whole-CNS degree. Loss means incoming synapse count, not unique partners; strictly greater than50% is flagged. All91 inputs have nonzero baseline degree. The flag does not measure loss of the external Poisson drive, which remains unchanged.', '',
              '| Class | Cells flagged / total |', '|---|---:|']
    for name in ['sugar', 'bitter', 'water', 'ir94e']:
        rows = [x for x in r['input_and_readout_degrees'] if x['label']==name]
        lines.append(f"| {name} | {sum(x['loss_gt_half'] for x in rows)}/{len(rows)} |")
    lines += ['', '| Cell / class | Body ID | Incoming at0.5 | Incoming at `c*` | Retained | Loss >50% |', '|---|---:|---:|---:|---:|---|']
    for x in r['input_and_readout_degrees'][-2:] + r['input_and_readout_degrees'][:-2]:
        lines.append(f"| {x['label']} | {x['bodyId']} | {x['incoming_at_0_5']:,} | {x['incoming_at_c_star']:,} | {x['retained_fraction']:.2%} | {'FLAG' if x['loss_gt_half'] else 'No'} |")
    lines += ['', 'The 480-trial experiment, final variant ledger/closing section and corresponding memo closure remain pending this checkpoint. No gate result or pass/fail is assigned to M1h yet.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    print(generate())
