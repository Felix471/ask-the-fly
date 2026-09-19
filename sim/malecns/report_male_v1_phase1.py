# SPDX-License-Identifier: MIT
"""Generate or exactly verify the audited male Phase 1 report; no simulation."""
import argparse
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sim.malecns import male_v1_adapter as adapter
from sim.malecns.substrate import DATA, ROOT, file_record

BEGIN = '<!-- male-v1-phase1:begin -->'
END = '<!-- male-v1-phase1:end -->'
REPORT = ROOT / 'docs/malecns_phase1.md'
PROGRAM = ROOT / 'docs/male_fly_v2.md'


def verdicts(rows):
    values = {r['id']:r['L_mean'] for r in rows}
    def value(s=0,w=0,i=0):
        return values[f's{s}_b0_w{w}_i{i}']
    water = (value(w=240) > 5 or any(value(s=60,w=w)-value(s=60) > 5 for w in (60,180,240)))
    water_line = 'Water is ' + ('an appetitive driver on the male' if water else
                               'not observed as an appetitive driver under this design') + '.'
    curve = [value(s=200,i=i) for i in (0,60,120,200)]
    # "Falls monotonically": non-increasing at every step, with a net fall;
    # an all-zero/flat curve is not suppression.
    suppresses = all(b <= a for a,b in zip(curve,curve[1:])) and curve[-1] < curve[0] and value(i=200) < 5
    ir94e = ('suppresses' if suppresses else 'excites MN9' if any(value(i=i)>5 for i in (60,120,200))
             else 'no monotone suppression observed under this design')
    return water_line, 'Ir94e ' + ir94e + '.'


def female_cell(female, condition):
    # Water low and medium have the same 60 Hz drive but separate grid seeds.
    matches = [r for r in female['cells'] if all(r['hz'][c] == condition[c+'_hz'] for c in adapter.CHANNELS)
               and (condition['water_hz'] != 60 or r['water'] == 'low')]
    if len(matches) != 1 or matches[0]['n_trials'] != 30:
        raise ValueError('Female coordinate missing, duplicated, or wrong n')
    return matches[0]


def pair(row, prefix, sd='sd'):
    return f"{row[prefix+'_mean']:.3f} ± {row[prefix+'_'+sd]:.3f}"


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str,row)) + ' |' for row in rows])


def render(summary, female):
    m = summary['metadata']
    by_id = {r['id']:r for r in summary['conditions']}
    lines = [BEGIN, '# Male-v1 Phase 1 characterisation', '',
             f"Completed UTC: {m['completed_utc']}; Brian2 {m['brian2']} / cython; workers {m['memory']['workers']}; "
             f"35 conditions × 30 = 1,050 trials; seeds 20260910–20260939 shared across conditions; "
             f"wall {m['walltime_s']:.3f} s; peak worker RSS {m['peak_worker_rss_gib']:.6f} GiB.", '',
             'MaleCNS v1.0 whole CNS, M1i >=5-synapse graph with 33 autapses removed: 166,700 neurons, '
             '6,242,085 edges, 89,859,938 synapses; w_syn 0.17875 mV exactly, external kick w_syn*f_poi = 44.6875 mV. '
             'The frozen male protocol uses 108 bilateral typed inputs and primary MN9 L10331; R16949 is secondary.', '',
             'All rates are mean ± population SD in Hz, n=30. Male MN11D/MN11V/CEM statistics are computed '
             'over per-trial means across 3/2/6 cells, respectively. Latencies below are medians among positive trials; '
             'a group latency is its earliest member spike. The female reference uses unilateral Shiu sets on '
             'FlyWire v783, all connections, w_syn 0.275 mV; these are different experiments and are not paired trials.', '',
             'Female values come from frozen [lookup_table_v1_2.json](../data/lookup_table_v1_2.json), '
             '`mn9_left_mean`/`mn9_left_std`, `mn9_right_mean`/`mn9_right_std`, '
             '`mn11d_mean`/`mn11d_sd`, and `mn11v_mean`/`mn11v_sd`, at identical Hz coordinates with bitter 0. '
             'Water 60 uses the `low` grid cell. Female CEM: not recorded in the female grid. '
             'The numerical tables below use the grid, not the earlier characterisation screen.', '']
    index = 0
    for channel in ('water','ir94e'):
        for kind in ('alone','x_sugar'):
            index += 1
            lines += [f'### Table {index}: {channel} ' + ('alone' if kind=='alone' else '× sugar'), '']
            rows = []
            for entry in summary['tables'][channel+'_'+kind]:
                male = by_id[entry['id']]
                f = female_cell(female,male)
                if kind == 'alone':
                    rows.append([male[channel+'_hz'],pair(male,'L'),pair(male,'R'),pair(male,'mn11d'),pair(male,'mn11v'),
                                 pair(male,'cem'),male['whole_network_spikes_median'],pair(f,'mn9_left','std'),
                                 pair(f,'mn9_right','std'),pair(f,'mn11d'),pair(f,'mn11v')])
                else:
                    rows.append([male['sugar_hz'],male[channel+'_hz'],pair(male,'L'),pair(f,'mn9_left','std'),
                                 pair(male,'mn11d'),pair(f,'mn11d')])
            headers = ([channel+' Hz','male L10331','male R16949','male MN11D','male MN11V','male CEM',
                        'male network median','female left MN9','female right MN9','female MN11D','female MN11V']
                       if kind=='alone' else ['sugar Hz',channel+' Hz','male L10331','female left MN9','male MN11D','female MN11D'])
            lines += [table(headers,rows),'']
    lines += ['## Descriptive verdicts', '', *verdicts(summary['conditions']), '',
              'These are descriptive, pre-declared screen criteria, not gates. Water is called appetitive if '
              'water 240 alone gives L10331 >5 Hz or any tested water dose raises L10331 at sugar 60 by >5 Hz '
              'against sugar 60 alone. Ir94e suppression means non-increasing L10331 across ir94e 0/60/120/200 '
              'at sugar 200 with a net decrease and ir94e 200 alone <5 Hz; otherwise any ir94e-alone '
              'level >5 Hz gives “excites MN9”, otherwise no monotone suppression is observed.', '',
              'The [female characterisation](phase1_characterization.md#channel-summary) reports water as '
              'excitatory alone and facilitating as a modifier of sugar. It reports Ir94e as having no effect '
              'alone and being suppressive as a modifier of sugar under that design. These historical female '
              'screen classifications use their original criteria, not the male descriptive criteria.', '',
              '## Every condition and readout', '']
    for r in summary['conditions']:
        lines += [f"### {r['id']}", '']
        keys = [k[:-5] for k in r if k.endswith('_mean')]
        rows = [[k,pair(r,k),r[k+'_firing_trials'],r[k+'_latency_median_ms'] if r[k+'_latency_median_ms'] is not None else 'not observed'] for k in keys]
        lines += [table(['readout (Body_ID where individual)','Hz','positive trials / 30','latency median ms'],rows),'']
        lines += [f"Network spikes median [min–max]: {r['whole_network_spikes_median']} "
                  f"[{r['whole_network_spikes_min']}–{r['whole_network_spikes_max']}]; neurons fired median [min–max]: "
                  f"{r['neurons_fired_median']} [{r['neurons_fired_min']}–{r['neurons_fired_max']}].",'']
    lines += ['## Execution and verification', '',
              'The [runner](../sim/malecns/male_v1_phase1.py) uses a spawn pool, one build per worker, '
              'restore before every trial, 1,000 ms duration and 0.1 ms dt; driven inputs have zero refractory '
              'and inactive inputs retain 2.2 ms. Existing outputs are refused, with no retry/resume. '
              'Sources and the compile-only plan are hashed in the [results](../data/malecns/male_v1_phase1_results.json). '
              'The independent [audit](../data/malecns/male_v1_phase1_audit.json) recomputes 1,050 raw trials, '
              'all 13 individual readouts, group means, latencies, network/source counts, every Poisson train '
              'from its seed/rates/layout, and every summary and derived-table field. '
              '[Tests](../sim/malecns/test_male_v1_phase1.py) cover configuration tampering, synthetic corruption, '
              'verdict logic and exact report regeneration. Run the report generator with `--check` to verify '
              'this entire generated block and the program Phase 1 section; later report sections are preserved.', '', END, '']
    return '\n'.join(lines)


def replace_block(existing, block):
    if existing.count(BEGIN) != 1 or existing.count(END) != 1:
        raise ValueError('Report must contain exactly one generated block')
    start, end = existing.index(BEGIN), existing.index(END)+len(END)
    if end < start:
        raise ValueError('Report markers reversed')
    return existing[:start]+block.rstrip('\n')+existing[end:]


def verify_block(existing, block):
    if existing != replace_block(existing,block):
        raise ValueError('Report regeneration differs')


def program_text(existing, summary):
    start_marker, end_marker = '## Phase 1\n\n', '\n## Phase 2\n'
    if existing.count(start_marker) != 1 or existing.count(end_marker) != 1:
        raise ValueError('Program phase markers missing or duplicated')
    start = existing.index(start_marker)+len(start_marker)
    end = existing.index(end_marker,start)
    water, ir94e = verdicts(summary['conditions'])
    replacement = ('Completed and independently audited 35 conditions × 30 = 1,050 trials; see the '
                   '[Phase 1 characterisation report](malecns_phase1.md). '
                   + water.rstrip('.')+'; '+ir94e[0].lower()+ir94e[1:]+'\n')
    return existing[:start]+replacement+existing[end:]


def generate(check=False):
    adapter.load_configuration()
    summary = adapter.read(DATA / 'male_v1_phase1_results.json')
    audit = adapter.read(DATA / 'male_v1_phase1_audit.json')
    if audit['status'] != 'PASS' or audit['raw_trials'] != 1050:
        raise ValueError('Successful full audit required')
    for record in audit['sources']+[audit['auditor']]+audit['dependencies']+summary['metadata']['sources']:
        adapter.check_file(record)
    if file_record(DATA / 'male_v1_phase1_results.json') not in audit['sources']:
        raise ValueError('Audit does not cover current results')
    block = render(summary,adapter.read(ROOT / 'data/lookup_table_v1_2.json'))
    old_program = PROGRAM.read_text(encoding='utf-8')
    new_program = program_text(old_program,summary)
    if check:
        verify_block(REPORT.read_text(encoding='utf-8'),block)
        if old_program != new_program:
            raise ValueError('Program Phase 1 regeneration differs')
    else:
        text = replace_block(REPORT.read_text(encoding='utf-8'),block) if REPORT.exists() else block
        REPORT.write_text(text,encoding='utf-8',newline='\n')
        PROGRAM.write_text(new_program,encoding='utf-8',newline='\n')
        verify_block(REPORT.read_text(encoding='utf-8'),block)
    print('Male-v1 Phase 1 report regeneration PASS' if check else 'Male-v1 Phase 1 report generated')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    generate(parser.parse_args().check)
