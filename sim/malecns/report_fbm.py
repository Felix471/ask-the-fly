"""Append or verify the reproducible M1i results checkpoint; no simulation."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sim.malecns.audit_fbm import read, require, equal
from sim.malecns import report_m1h
from sim.malecns.substrate import DATA, ROOT, file_record

MARKER = '## M1i results checkpoint — 2026-09-18'
DOCUMENT = ROOT / 'docs/malecns_phase0.md'
LEDGER = '## Male line closing ledger — eight variants (2026-09-18)'


def verdict(value):
    return 'PASS' if value else 'FAIL'


def mean_sd(mean, sd):
    return f'{mean:.3f} ± {sd:.3f}'


def extent(value):
    return f"{value['median']:,.1f} [{value['min']:,.0f}–{value['max']:,.0f}]"


def generate():
    a, b, audit = (read(DATA / name) for name in ('m1i_a_results.json', 'm1i_b_results.json', 'm1i_runs_audit.json'))
    require(audit['status'] == 'PASS', 'A passing independent audit is required')
    for run in ('a', 'b'):
        require(audit['runs'][run]['status'] == 'PASS', f'Run {run} audit failed')
        equal(file_record(DATA / f'm1i_{run}_results.json'), audit['runs'][run]['sources'][0], 'Audited summary')
    equal(file_record(ROOT / audit['auditor']['path']), audit['auditor'], 'Auditor source')
    p = read(DATA / 'stim_protocol_malecns_fbm.json')
    counts = read(DATA / 'substrate_record_fbm.json')['counts']
    byid = {r['id']: r for r in a['conditions']}
    failing = [k for k in 'ABCD' if not a['gates']['L'][k]] + [k for k in ('S1', 'S2', 'S3') if not a['shape_gate'][k]]
    overall = verdict(a['overall_primary'])
    rate = lambda r, s: mean_sd(r[s + '_mean'], r[s + '_sd'])
    lines = [MARKER, '',
             f"**Run (a): {overall} on primary L10331; failing gates: {', '.join(failing) if failing else 'none'}.** "
             'PASS requires A, B, C, D, S1, S2 and S3 all to pass on L10331. R16949 is recorded, not deciding.', '',
             '### Run metadata', '',
             '| Run | Completed UTC | Simulation commit in run_meta | Brian2 / backend | Workers used (budget) | Trials | Seeds | Wall seconds | Peak worker RSS GiB |',
             '|---|---|---|---|---:|---:|---|---:|---:|']
    for run, result in [('b', b), ('a', a)]:
        meta, checked = result['metadata'], audit['runs'][run]
        lines.append(f"| {run} | {meta['completed_utc']} | {checked['simulation_commit_in_run_meta'] or 'Not recorded'} | "
                     f"{meta['brian2']} / {meta['codegen']} | {checked['observed_worker_pids']} ({meta['memory']['workers']}) | "
                     f"{meta['total_trials']} | {p['seeds'][0]}–{p['seeds'][-1]}" + ('; KC first five' if run == 'b' else '') +
                     f" | {meta['walltime_s']:.3f} | {meta['peak_worker_rss_gib']:.6f} |")
    lines += ['',
              f"The launch was reported at `{audit['runs']['a']['source_text_verified_at_commit']}`. The run_meta files omit a git commit; "
              'the audit verifies every executed source-file hash exactly against metadata and compares its text to that commit with only LF/CRLF normalization. '
              'Workers used are the distinct PIDs in the condition ledgers; the replication pool caps the memory budget at four workers. '
              'The checkpoint date is 2026-09-18 local; completion timestamps above are 2026-09-19 UTC.', '',
              f"Whole CNS: **{counts['neurons']:,} neurons / {counts['edges']:,} edges / {counts['synapses']:,} synapses**, "
              f"edges >=5 after autapse removal; w_syn {p['model']['w_syn_mV']:.5f} mV per signed synapse. "
              'KC input gain 0.25 changes the declared KC-target signed weights only. '
              '[Outgoing retention and fixed top-20 last-hop table](#m1i-substrate-checkpoint--2026-09-18) remain recorded, not stop conditions.', '',
              '### Run (b): replication', '',
              'Rates are mean ± population SD across n=30 trials per main condition and n=5 for KC. '
              'Bin min/median/max pool all 20 two-cell 50 ms bins per trial; positive trials refer to the two-cell mean.', '',
              '| Condition | L10331 Hz | R16949 Hz | Two-cell mean Hz | Bin min / median / max Hz | Positive trials | Network spikes median [min–max] | Their reported Hz | Criterion |',
              '|---|---:|---:|---:|---:|---:|---:|---|---|']
    for row in b['conditions']:
        cid = row['id']
        values = [mean_sd(row[k]['mean'], row[k]['sd']) for k in ('L_hz', 'R_hz', 'bilateral_mean_hz')]
        bins = ' / '.join(f"{row['bilateral_bin_hz'][k]:g}" for k in ('min', 'median', 'max'))
        if cid == 'fbm_sugar_kc':
            diff = b['kc_paired_difference']['metrics']['bilateral_mean_hz']
            criterion = f"KC−base {mean_sd(diff['mean'], diff['sd'])} Hz; no criterion"
            reference = 'not reported'
        else:
            criterion = 'MATCH' if b['replication_criteria'][cid] else 'NO MATCH'
            reference = '30–90' if cid == 'fbm_sugar' else '0'
        lines.append(f"| {cid} | " + ' | '.join(values) + f" | {bins} | {row['bilateral_mean_hz']['positive_trials']}/{row['n_trials']} | "
                     f"{extent(row['whole_network_spikes'])} | {reference} | {criterion} |")
    lines += ['',
              'Their number is a per-tick two-cell mean from one 600 ms run at dt 0.5 ms; ours is thirty 1 s trials at dt 0.1 ms '
              f"on a {counts['neurons']:,}-neuron roster (the KC check has five trials). MATCH denotes only the declared replication criteria.", '',
              'Declared confound: ' + p['confound'], '',
              'KC−base paired differences use the first five fbm_sugar trials with identical Poisson events, not the thirty-trial sugar mean. '
              + '; '.join(f"{label}: {mean_sd(b['kc_paired_difference']['metrics'][key]['mean'], b['kc_paired_difference']['metrics'][key]['sd'])} Hz"
                          for key, label in [('L_hz', 'L10331'), ('R_hz', 'R16949'), ('bilateral_mean_hz', 'two-cell mean')]) + '. No criterion.', '',
              '### Run (a): declared gates', '',
              '| Gate | L10331 primary | R16949 secondary |', '|---|---|---|']
    for gate in ('A', 'B', 'C', 'D', 'C_literal_zero', 'D_literal_zero'):
        lines.append(f"| {gate} | {verdict(a['gates']['L'][gate])} | {verdict(a['gates']['R'][gate])} |")
    for gate in ('S1', 'S2', 'S3', 'S'):
        detail = f" ({a['shape_gate']['coverage']}/5 positive levels; requires >=4)" if gate == 'S1' else (
            f" (network max/min={a['shape_gate']['network_max_min_ratio']:.6f}; requires <3)" if gate == 'S3' else '')
        lines.append(f"| {gate} | {verdict(a['shape_gate'][gate])}{detail} | Not evaluated; non-deciding |")
    lines += [f'| Overall A–D + S | {overall} | Non-deciding |', '',
              'Historical D is completeness, not literal baseline zero. C allows the declared baseline mean + 2 SD + 1 Hz; '
              'its literal-zero addition is reported separately and does not change acceptance. S3 applies only to sugar200 network counts. '
              'R16949 is silent throughout run (a).', '',
              '### Run (a): five-level sugar curve', '', 'Mean ± population SD in Hz, n=30 at every level.', '',
              '| Sugar Hz | L10331 | R16949 |', '|---|---:|---:|']
    for level in (25, 50, 100, 120, 200):
        row = byid['AP_sugar_120' if level == 120 else f'A_s{level}_b0']
        lines.append(f"| {level} | {rate(row, 'L')} | {rate(row, 'R')} |")
    lines += ['', '### Run (a): every condition', '', 'Mean ± population SD, Hz; n=30 per condition.', '',
              '| Condition | L10331 Hz | R16949 Hz | Network spikes median [min–max] | Neurons fired median [min–max] |',
              '|---|---:|---:|---:|---:|']
    for row in a['conditions']:
        lines.append(f"| {row['id']} | {rate(row, 'L')} | {rate(row, 'R')} | {extent(row['whole_network_spikes'])} | {extent(row['neurons_fired'])} |")
    lines += ['', '### Run (a): A′ sugar17 versus LB3c12 at 120 Hz', '',
              'Mean ± population SD, n=30 paired seeds; difference is LB3c12 minus sugar17.', '',
              '| Side | Sugar17 Hz | LB3c12 Hz | Paired subset−union Hz | Lower/equal/higher trials |', '|---|---:|---:|---:|---:|']
    for side in ('L', 'R'):
        pair = a['a_prime'][side]
        trials = '/'.join(str(pair[k + '_trials']) for k in ('lower', 'equal', 'higher'))
        lines.append(f"| {side} | {rate(byid['AP_sugar_120'], side)} | {rate(byid['AP_sugar_lb3c_120'], side)} | "
                     f"{mean_sd(pair['mean_hz'], pair['sd_hz'])} | {trials} |")
    aa, bb = audit['runs']['a'], audit['runs']['b']
    lines += ['', '### Execution and verification', '',
              f"The [independent raw audit](../data/malecns/m1i_runs_audit.json) passes {audit['raw_trials']} raw trial JSON/NPZ pairs "
              f"({bb['raw_trials']} b + {aa['raw_trials']} a), {audit['MN9_neuron_trials']} MN9-neuron trials, "
              f"{bb['bilateral_bin_rows']} bilateral bin rows and {aa['poisson_unit_trials'] + bb['poisson_unit_trials']:,} Poisson-unit trials. "
              'It reconstructs counts, rates, first-spike latencies, network counts and every scientific summary field, including the unchanged A–D/S predicates and both paired comparisons. '
              'Every Poisson event index/time is reproduced from the declared seed, rates, dt and physical layout without running a network. '
              f"The {bb['kc_identical_input_pairs']} KC pairs ({bb['kc_identical_unit_trains']} unit trains), "
              f"{aa['AP_identical_shared_unit_trains']} A′ shared trains and {aa['A200_B0_identical_network_pairs']} A200/B0 whole-network pairs match exactly. "
              'Repeated seeds are not independent extra replicates.', '',
              '[Run b summary](../data/malecns/m1i_b_results.json), [run a summary](../data/malecns/m1i_a_results.json), '
              '[audit implementation](../sim/malecns/audit_fbm.py), [report and corruption tests](../sim/malecns/test_fbm_report.py). '
              'Verification covers audit structure, deliberately corrupted trial data, input reconstruction, report regeneration, the male and main Python suites, and release validation. '
              'No new simulation, rerun, M2, alternative gain/threshold, product or frozen-data change is part of this results checkpoint.', '',
              LEDGER, '', '| Variant | Structural rationale / design | Recorded result under its declared rule |', '|---|---|---|']
    # Preserve all seven earlier rows and their historical acceptance rules verbatim.
    historical = report_m1h.generate().split('## Male line closing decision — 2026-09-14', 1)[1]
    lines.extend(line for line in historical.splitlines() if line.startswith('| [M1'))
    lines += [f"| [M1i](#m1i-results-checkpoint--2026-09-18) | Whole CNS, edges >=5, gain 0.65; replication inputs and sugar17 gates declared separately | "
              + '; '.join(f"b {key}: {'MATCH' if value else 'NO MATCH'}" for key, value in b['replication_criteria'].items())
              + f". a: {overall} under A–D + S on L10331; failing gates: {', '.join(failing) if failing else 'none'}. |", '',
              'Per the declared stop rule, the male line stops after M1i whatever the result. '
              + ('Run (a) passed; product work is a separate owner decision. ' if a['overall_primary'] else 'Run (a) fails; the male line is Closed after eight variants. ')
              + 'No further variant, gain, threshold change or M2 follows. Historical M1c passes retain their original rules; S is not applied retroactively. '
              'No product, frozen-data, copy or honesty-table changes.', '']
    return '\n'.join(lines)


def check_or_append(path=DOCUMENT):
    text = path.read_text(encoding='utf-8')
    block = generate()
    if MARKER not in text:
        with path.open('a', encoding='utf-8', newline='') as stream:
            stream.write('\n' + block)
        text = path.read_text(encoding='utf-8')
    equal(text.count(MARKER), 1, 'Unique M1i checkpoint')
    equal(MARKER + text.split(MARKER, 1)[1], block, 'M1i report regeneration')
    print('M1i report regeneration PASS')


if __name__ == '__main__':
    check_or_append()
