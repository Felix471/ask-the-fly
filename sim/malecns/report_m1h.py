"""M1h results and closing ledger from saved records; no simulation."""
import json
from sim.malecns.substrate import DATA, ROOT


def generate():
    d = json.loads((DATA / 'm1h_results.json').read_text())
    f = {r['id']: r for r in json.loads((DATA / 'phase0_female_reference.json').read_text())['rows']}
    old = {r['id']: r for r in json.loads((DATA / 'brain_unscaled_results.json').read_text())['conditions']}
    byid = {r['id']: r for r in d['conditions']}
    grid = json.loads((ROOT / 'data/lookup_table.json').read_text())
    f120 = next(r for r in grid['cells'] if r['hz'] == dict(sugar=120, bitter=0, water=0, ir94e=0))
    v = lambda b: 'PASS' if b else 'FAIL'
    rate = lambda r, s: f"{r[s+'_mean']:.3f} ± {r[s+'_sd']:.3f}"
    extent = lambda r: f"{r['median']:,.1f} [{r['min']:,}–{r['max']:,}]"
    lines = ['## M1h results checkpoint — 2026-09-14', '',
             f"**Overall on primary L10331: {v(d['overall_primary'])}.** All480 trials completed once; no extra candidate or rerun. The crossed outgoing-retention flag and dated owner waiver above remain intact.", '',
             '| Gate | L10331 primary | R16949 secondary |', '|---|---|---|']
    for k in 'ABCD':
        lines.append(f"| {k} | {v(d['gates']['L'][k])} | {v(d['gates']['R'][k])} |")
    for k in ['S1', 'S2', 'S3', 'S']:
        detail = f" ({d['shape_gate']['coverage']}/5 positive levels)" if k == 'S1' else f" (network max/min={d['shape_gate']['network_max_min_ratio']:.6f})" if k == 'S3' else ''
        lines.append(f"| {k} | {v(d['shape_gate'][k])}{detail} | Not evaluated; non-deciding |")
    lines += [f"| Overall A–D + S | {v(d['overall_primary'])} | Non-deciding |", '',
              'Historical D is the completeness predicate; baseline-zero is separately reported. S3 is the declared sugar200 spike-count max/min bound, not proof of general network stability. S and acceptance apply only to L10331.', '',
              'B fails because bitter25→50 raises the L mean from2.367 to4.700 Hz, despite98.7% endpoint suppression at bitter200. C fails because bitter-alone25/50/100 means2.300/3.167/1.400 Hz exceed the unchanged1 Hz limit. D literal baseline-zero passes on both sides. Sugar200 ranges5,317–285,822 network spikes, failing S3; no new mechanism is assigned.', '',
              '### Five-level sugar curve', '',
              'Mean ± population SD, Hz, n=30. Female Shiu L/R are historical aliases (contralateral/ipsilateral); male L10331 is ipsilateral. Female25/50/100/200 come from historical pre-correction Phase0,120 from the corrected frozen grid, so this is not a matched five-level female rerun. M1f unscaled is the previously recorded brain endpoint graph at confidence0.5 and recurrent0.275. [Female reference](../data/malecns/phase0_female_reference.json), [female120](../data/lookup_table.json), [M1f unscaled](../data/malecns/brain_unscaled_results.json).', '',
              '| Sugar Hz | M1h L | M1h R | Female Shiu L | Female Shiu R | M1f unscaled L | M1f unscaled R |', '|---|---:|---:|---:|---:|---:|---:|']
    for level in [25, 50, 100, 120, 200]:
        cid = f'A_s{level}_b0' if level != 120 else 'AP_sugar_120'
        female = [rate(f[cid], s) for s in ['R', 'L']] if level != 120 else [f"{f120['mn9_'+s+'_mean']:.3f} ± {f120['mn9_'+s+'_std']:.3f}" for s in ['left', 'right']]
        values = [rate(byid[cid], s) for s in ['L', 'R']] + female + [rate(old[cid], s) for s in ['L', 'R']]
        lines.append(f'| {level} | ' + ' | '.join(values) + ' |')
    lines += ['', '### Every condition: both MN9s and network counts', '',
              '| Condition | L Hz | R Hz | Network spikes median [min–max] | Neurons fired median [min–max] |', '|---|---:|---:|---:|---:|']
    for r in d['conditions']:
        lines.append(f"| {r['id']} | {rate(r,'L')} | {rate(r,'R')} | {extent(r['whole_network_spikes'])} | {extent(r['neurons_fired'])} |")
    lines += ['', '### A′ sugar17 versus LB3c12 at120 Hz', '',
              '| Side | Sugar17 Hz | LB3c12 Hz | Paired subset−union Hz | Lower/equal/higher trials |', '|---|---:|---:|---:|---:|']
    for s in ['L', 'R']:
        a = d['a_prime'][s]
        counts = '/'.join(str(a[k+'_trials']) for k in ['lower', 'equal', 'higher'])
        lines.append(f"| {s} | {rate(byid['AP_sugar_120'],s)} | {rate(byid['AP_sugar_lb3c_120'],s)} | {a['mean_hz']:.3f} ± {a['sd_hz']:.3f} | {counts} |")
    m = d['metadata']
    lines += ['', '### Execution and verification', '',
              f"Protocol/source freeze `e163c6e`, execution-plan commit `02db48f`; run HEAD `{m['git_commit']}`. Same91 physical slots and M1 seeds20260910–20260939,420 A–D plus60 A′ trials. {m['memory']['workers']} workers, reserve{m['memory']['reserve_gib']:.2f}GiB, budget{m['memory']['worker_budget_gib']:.1f}GiB/worker. Wall{m['walltime_s']:.1f}s; peak worker{m['peak_worker_rss_gib']:.3f}GiB; completed{m['completed_utc']}.", '',
              'Actual weights checked after construction and restore: recurrent0.275 mV per signed synapse and stimulus68.75 mV/event. [Results](../data/malecns/m1h_results.json), [protocol](../data/malecns/stim_protocol_malecns_density_matched.json), [saved-event audit](../data/malecns/m1h_runs_audit.json). Raw spikes, per-trial ledgers and live weight logs are retained locally. The audit reconstructs480 trials/960 MN9-neuron trials, all network counts, gates, A′, and verifies identical Poisson input arrays against M1. Repeated seeds and A200/B0 are not independent extra replicates.', '',
              'Cost: confidence0.869 retains56.8% of brain contacts; recall there is unknown (Berg S8E gives0.81 at0.5). This is a heavily pruned graph, density-matched by construction. Gate results do not establish behavioural calibration or compensate for reconstruction differences.', '',
              '## Male line closing decision — 2026-09-14', '',
              'Per the owner’s instruction before M1h results, **the male line is closed pending replies from Tastekin and the fly-brain-minecraft author**. Every attempted variant remains in the record. No intermediate weight, additional candidate, M2, or product change follows this checkpoint.', '',
              '| Variant | Structural rationale / design | Recorded result under its declared rule |', '|---|---|---|',
              '| [M1](#hard-gates) | Whole CNS, original Shiu weights, typed male inputs | Neither side passes A–D. L fails A/B/C; R fails A. S not yet declared. |',
              '| [M1c all](../data/malecns/rescale_all_results.json) | Scale recurrent and tied external weights by whole-network mean density ratio | Passes original A–D-on-at-least-one-side rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |',
              '| [M1c mn9](../data/malecns/rescale_mn9_results.json) | Scale by equal-side mean density of strongest MN9 input partners, with the declared137-partner exception | Passes original A–D rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |',
              '| [M1d](../data/malecns/split_results.json) | Keep female external kick; scale recurrent weights by whole-network density | FAIL: A–D pass on L, S1 fails (1/5). Saved activity identical to M1c all. |',
              '| [M1f unscaled](../data/malecns/brain_unscaled_results.json) | Brain endpoint cut, original recurrent weight, female kick | FAIL: L B/C fail; graded sugar and S pass. |',
              '| [M1f density](../data/malecns/brain_density_results.json) | Same brain cut; recurrent weight scaled by its density | FAIL: L A–D pass; S1 fails (2/5). |',
              f"| [M1h](#m1h-results-checkpoint--2026-09-14) | Confidence-pruned brain graph matched to female density; original weight/kick; outgoing flag explicitly waived | {v(d['overall_primary'])} under A–D + S on L10331; full gate breakdown above. |", '',
              'This closure is an owner decision about further work pending external information, not a claim that every possible male model fails. Historical M1c passes retain their original rule; the later S gate is not applied retroactively. Female pipeline, frozen scores, site and README honesty table remain unchanged.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    print(generate())
