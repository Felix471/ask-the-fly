# SPDX-License-Identifier: MIT
"""Generate or exactly verify both audited Phase 2 report blocks; no simulation."""
import argparse
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sim.malecns import male_v1_adapter as adapter, male_v1_grid as grid
from sim.malecns.audit_male_v1_phase1 import equal, require
from sim.malecns.report_male_v1_phase1 import table
from sim.malecns.substrate import DATA, ROOT, file_record

BEGIN = '<!-- male-v1-phase2:begin -->'
END = '<!-- male-v1-phase2:end -->'
REPORT = ROOT / 'docs/malecns_phase2.md'
PROGRAM = ROOT / 'docs/male_fly_v2.md'
STATES = ('eats', 'mouth_moves', 'proboscis_only', 'no_response')


def percent(rate):
    return 'undefined (no eligible pairs)' if rate is None else f'{100*rate:.3f}%'


def statements(comparison):
    c = comparison
    a = c['attribution_pairs']
    below = c['distributions']['below_5hz_dishes']
    return [f"The flies agree on {percent(c['pairwise']['agreement_rate'])} of the {c['n_pairs']} dish pairs.",
            f"The male fly's primary MN9 is below 5 Hz for {below['male']} of {c['n_dishes']} dishes (female {below['female']}).",
            f"Water removes {a['removed_by_water']} and Ir94e removes {a['removed_by_ir94e']} of the "
            f"{a['disagreeing_pairs']} disagreeing pairs; {a['removed_by_neither']} are removed by neither."]


def render(summary, lookup, comparison, audit):
    m, s, c, a = summary['metadata'], lookup['substrate'], comparison, audit
    lines = [BEGIN, '# Male-v1 Phase 2 grid and comparison', '',
             f"Completed UTC: {m['completed_utc']}; Brian2 {m['brian2']} / cython; workers {m['memory']['workers']}; "
             f"{a['cells']} × 30 = {m['total_trials']:,} trials; seed rule: {grid.SEED_RULE}; "
             f"wall {m['walltime_s']:.3f} s; peak worker RSS {m['peak_worker_rss_gib']:.6f} GiB. "
             f"Audit PASS: {a['raw_trials']:,} trials, {a['readout_neuron_trials']:,} readout-neuron trials, "
             f"{a['poisson_unit_trials']:,} Poisson-unit trials, {a['cells']} cells, {a['dishes']} dishes, "
             f"{a['pairs']:,} pairs and {a['replays']} replays.", '',
             f"MaleCNS v1.0 whole CNS: {s['neurons']:,} neurons, {s['edges']:,} edges, {s['synapses']:,} synapses, "
             f">={s['min_synapses']} synapses per connection and {s['autapses_removed']} autapses removed; "
             "w_syn 0.17875 mV and bilateral Tastekin-typed sugar/bitter/water/ir94e sets (34/38/17/19). "
             "Primary MN9 L10331 decides, with R16949 recorded secondary; MN11D/MN11V/CEM are per-trial "
             "three/two/six-cell means. The female uses FlyWire v783, all connections, Shiu's 0.275 mV "
             "and unilateral Shiu sets (23/42/18/18), its frozen primary MN9 and two-cell MN11D. These are "
             "two experiments side by side, not one calibrated model. Shared encoder levels and our >=5 Hz "
             "state threshold are design choices; states use unrounded 30-trial means. Ir94e is amino-acid aversion.", '']
    lines += [f'{i}. {text}' for i, text in enumerate(lookup['product_commitments'], 1)]+['']
    for kind, count in [('cells', a['cells']), ('dishes', c['n_dishes'])]:
        lines += [f'## R3: states over {count} {kind}', '',
                  table(['state', 'male', 'female'], [[state, c['distributions']['male'][kind][state],
                                                      c['distributions']['female'][kind][state]] for state in STATES]), '']
    lines += [table(['below 5 Hz dishes', 'male', 'female'],
                    [['count', c['distributions']['below_5hz_dishes']['male'], c['distributions']['below_5hz_dishes']['female']]]), '',
              f"Distinct occupied grid cells: female {c['n_distinct_female_cells']}; male {c['n_distinct_male_cells']}.", '',
              'Female state (rows) × male state (columns):', '',
              table(['female / male', *STATES], [[s, *[c['distributions']['cross_table'][s][t] for t in STATES]] for s in STATES]), '',
              '## R4: dish pairs', '',
              f"Agreement: {c['pairwise']['agreeing_pairs']} / {c['n_pairs']} = {percent(c['pairwise']['agreement_rate'])}. "
              f"Neither fly ties in {c['pairwise']['strict_pairs']} pairs; strict agreement {percent(c['pairwise']['strict_agreement_rate'])}. "
              f"Both flies tie in {c['pairwise']['both_tie_pairs']} pairs.", '',
              'First means the earlier dish in the frozen dictionary; ties use abs(score difference) <1e-9.', '']
    outcomes = ('first', 'second', 'tie')
    lines += [table(['female / male', *outcomes], [[s, *[c['pairwise']['cross_table'][s][t] for t in outcomes]] for s in outcomes]), '',
              '## R5: pair attribution', '', table(['quantity', 'pairs'], list(c['attribution_pairs'].items())), '',
              '“By either” is the union of the two single-channel interventions; “by neither” is its complement '
              'among disagreeing pairs, including the separately listed only-by-both subset. '
              'These categories overlap. The female scores stay fixed.', '',
              '## R6: dish attribution', '', table(['quantity', 'count'], list(c['attribution_dishes'].items())), '',
              'Counterfactual lower counts are recomputed over every female-winning pair, so they may include newly lost pairs. '
              'Partly includes fully; ranks are 1 plus the number of strictly higher stored scores.', '',
              '## R7: channel sign over dishes', '',
              table(['channel', 'fly', 'lower', 'equal', 'higher', 'dishes'],
                    [[ch, fly, *[c['channel_sign'][ch][fly][k] for k in ('lower', 'equal', 'higher', 'n_dishes')]]
                     for ch in ('water', 'ir94e') for fly in ('male', 'female')]), '',
              '## Descriptive statements', '', *statements(c), '', '## Every dish', '']
    keys = ['key', 'en', 'zh', 'sugar', 'bitter', 'water', 'ir94e', 'female_score', 'female_rank', 'female_state',
            'male_score', 'male_rank', 'male_state', 'lower', 'lower_water', 'lower_ir94e']
    def display(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines += [table(keys, [[display(r[k]) for k in keys] for r in c['dishes']]), '', '## Execution and verification', '',
              'The [runner](../sim/malecns/male_v1_grid.py) uses the declared seeds and store/restore path. '
              'The [lookup builder](../sim/malecns/build_lookup_male.py), '
              '[comparison](../sim/malecns/male_female_comparison.py) and '
              '[replay packer](../scripts/pack_replay_male.py) produce additive artifacts. '
              'The independent [audit](../sim/malecns/audit_male_v1_grid.py) reconstructs the raw events, '
              'Poisson trains, statistics, comparison and replay bytes. Each replay is grid trial 0, one of the 30 '
              'trials behind the lookup mean; its MN9 counts equal that trial’s rates, not the 30-trial mean. '
              '[Synthetic tests](../sim/malecns/test_male_v1_grid_outputs.py) exercise corruption rejection. '
              'Verify both generated blocks with '
              '`.venv\\Scripts\\python -m sim.malecns.report_male_v1_grid --check`; the '
              '[generator](../sim/malecns/report_male_v1_grid.py) preserves the declaration and later sections.', '',
              table(['replay size statistic', 'bytes'], [[k, a['replay_sizes'][k]] for k in
                    ('min_bytes', 'median_bytes', 'max_bytes', 'total_bytes', 'index_bytes', 'manifest_bytes')]), '', END, '']
    return '\n'.join(lines)


def replace_block(existing, block):
    before, found, rest = existing.partition(BEGIN)
    content, ended, after = rest.partition(END)
    require(found and ended and BEGIN not in rest and END not in before+after, 'Exactly one ordered Phase 2 block required')
    return before+block.rstrip('\n')+after


def verify_block(existing, block):
    equal(existing, replace_block(existing, block), 'Report regeneration differs')


def program_text(existing, comparison, audit):
    marker = '## Phase 2\n'
    require(existing.count(marker) == 1, 'Exactly one Phase 2 section required')
    start = existing.index(marker)+len(marker)
    # Retain any later top-level section, whether or not it is named Phase 3.
    end = existing.find('\n## ', start)
    end = len(existing) if end < 0 else end
    body = existing[start:end]
    block = '\n'.join([BEGIN, f"Completed and independently audited {audit['cells']} × 30 = {audit['raw_trials']:,} trials; "
                        'see the [Phase 2 grid and comparison report](malecns_phase2.md).',
                        *statements(comparison), END])
    if BEGIN in body or END in body:
        require('### Results\n' in body, 'Results heading missing')
        body = replace_block(body, block)
    else:
        require('### Results\n' not in body, 'Unmarked Results subsection exists')
        body += '\n### Results\n\n'+block+'\n'
    return existing[:start]+body+existing[end:]


def generate(check=False, result_path=None, lookup_path=None, comparison_path=None, audit_path=None,
             report_path=REPORT, program_path=PROGRAM):
    adapter.load_configuration()
    result_path = grid.RESULT if result_path is None else result_path
    lookup_path = ROOT / 'data/lookup_table_male.json' if lookup_path is None else lookup_path
    comparison_path = DATA / 'male_female_comparison.json' if comparison_path is None else comparison_path
    audit_path = DATA / 'male_v1_grid_audit.json' if audit_path is None else audit_path
    summary, lookup, comparison, audit = [adapter.read(p) for p in (result_path, lookup_path, comparison_path, audit_path)]
    for key, expected in dict(status='PASS', raw_trials=12000, readout_neuron_trials=156000,
                              poisson_unit_trials=1296000, cells=400, dishes=174, pairs=15051, replays=400).items():
        equal(audit[key], expected, 'Complete audit required: '+key)
    for record in audit['sources']+[audit['auditor']]+audit['dependencies']+summary['metadata']['sources']:
        adapter.check_file(record)
    for path in (result_path, lookup_path, comparison_path):
        require(file_record(path) in audit['sources'], 'Audit must cover report input '+str(path))
    equal(audit['auditor']['path'], 'sim/malecns/audit_male_v1_grid.py', 'Phase 2 auditor required')
    block = render(summary, lookup, comparison, audit)
    old_program = program_path.read_text(encoding='utf-8')
    new_program = program_text(old_program, comparison, audit)
    old_report = report_path.read_text(encoding='utf-8') if report_path.exists() else None
    if check:
        require(old_report is not None, 'Report missing')
        verify_block(old_report, block)
        equal(old_program, new_program, 'Program Phase 2 regeneration differs')
    else:
        updated = replace_block(old_report, block) if old_report is not None else block
        report_path.write_text(updated, encoding='utf-8', newline='\n')
        program_path.write_text(new_program, encoding='utf-8', newline='\n')
        verify_block(report_path.read_text(encoding='utf-8'), block)
        equal(program_path.read_text(encoding='utf-8'), new_program, 'Program write verification')
    print('Male-v1 Phase 2 report regeneration PASS' if check else 'Male-v1 Phase 2 report generated')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    generate(parser.parse_args().check)


if __name__ == '__main__':
    main()
