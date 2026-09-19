"""Generate and verify the M1j results checkpoint and closing ledger; no simulation."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sim.malecns.audit_m1j import read, equal, require, result_path, right_shape
from sim.malecns.report_fbm import mean_sd, extent, verdict
from sim.malecns.substrate import ROOT, DATA, file_record

MARKER = '## M1j results checkpoint — 2026-09-19'
LEDGER = '## Male line closing ledger — nine variants (2026-09-19)'
DOCUMENT = ROOT / 'docs/bilateral_sugar_policy.md'
LEDGER_DOCUMENT = ROOT / 'docs/malecns_phase0.md'


def rate(row, side='L'):
    return mean_sd(row[side+'_mean'], row[side+'_sd'])


def failures(result):
    return [g for g in 'ABCD' if not result['gates']['L'][g]] + [g for g in ('S1','S2','S3') if not result['shape_gate'][g]]


def generate():
    results = {b:read(result_path(b)) for b in ('male','female')}
    audit = read(DATA / 'm1j_runs_audit.json')
    require(audit['status']=='PASS', 'Independent audit required')
    for b,r in results.items():
        require(audit['runs'][b]['status']=='PASS', b + ' audit required')
        equal(file_record(result_path(b)),audit['runs'][b]['sources'][0],'Audited summary')
    for record in [audit['auditor'],audit['m0']['source']] + audit['dependencies']:
        equal(file_record(ROOT / record['path']),record,'Audit provenance')
    m0 = read(DATA / 'm0_recheck.json')
    differing = [s['path'] for s in m0['sources'] if s['differs']]
    byid = {b:{r['id']:r for r in v['conditions']} for b,v in results.items()}
    lines = [MARKER,'', '**Adoption verdict: ' + ('ADOPTED' if all(r['overall_primary'] for r in results.values()) else 'REJECTED') + '.** '
             + '; '.join(f"{b}: {verdict(r['overall_primary'])}, failing required gates: {', '.join(failures(r)) or 'none'}" for b,r in results.items())
             + '. Adoption requires both primary readouts to pass A–D and S1–S3. The male line closes at nine variants either way.', '',
             '### M0 environment recheck','',
             f"**{m0['verdict']}**: {len(m0['trials'])} trials, {m0['neurons_compared']:,} neuron spike-time arrays and {m0['spikes_compared']:,} spikes compared exactly; both MN9 rates and latencies are identical. "
             + ('Sources differing from stored M0 hashes: ' + ', '.join(differing) if differing else 'None of the six source files differs from its stored M0 hash')
             + '. The saved hashes and identical outputs are reported as recorded, without assuming intervening edits. '
             + '[M0 record](../data/malecns/m0_recheck.json).', '',
             'M0 records neuron trains only, with no saved Poisson event trains. The audit reconstructs the declared 91-unit inputs but cannot compare them with unsaved inputs; '
             'all ten whole-network per-neuron comparisons are exact. This input-comparison limitation is not a failed output recheck.', '',
             '### Run metadata','',
             '| Brain | Completed UTC | Brian2 / backend | Workers used (budget) | Trials | Seeds | Wall seconds | Peak worker RSS GiB |',
             '|---|---|---|---:|---:|---|---:|---:|']
    for b,r in results.items():
        m=r['metadata']
        lines.append(f"| {b} | {m['completed_utc']} | {m['brian2']} / {m['codegen']} | {audit['runs'][b]['observed_worker_pids']} ({m['memory']['workers']}) | {m['total_trials']} | 20260910–20260939 | {m['walltime_s']:.3f} | {m['peak_worker_rss_gib']:.6f} |")
    counts=read(DATA / 'substrate_record_fbm.json')['counts']
    lines += ['',f"Male: whole CNS, {counts['neurons']:,} neurons / {counts['edges']:,} edges / {counts['synapses']:,} synapses, edges >=5 after autapse removal, w_syn 0.17875 mV; bilateral sugar34, 108 physical input units. "
              'Female: unchanged frozen FlyWire v783 graph, w_syn 0.275 mV; bilateral sugar57, 128 physical input units. '
              'Both use 1 s trials, dt 0.1 ms, n=30 per condition. The seven female water-overlap roots occupy sugar slots only.', '',
              '### Declared gates, both brains','',
              '| Gate | Male L10331 primary | Male R16949 recorded | Female frozen left primary | Female right recorded |',
              '|---|---|---|---|---|']
    for g in ('A','B','C','D','C_literal_zero','D_literal_zero','S1','S2','S3','S','Overall'):
        values=[]
        for b in ('male','female'):
            r=results[b]
            for side in ('L','R'):
                shape=r['shape_gate'] if side=='L' else audit['runs'][b]['secondary_shape_gate']
                if g in r['gates'][side]:
                    value=verdict(r['gates'][side][g])
                elif g=='Overall':
                    value=verdict(r['gates'][side]['overall'] and shape['S'])
                else:
                    value=verdict(shape[g])
                    if g=='S1': value+=f" ({shape['coverage']}/5)"
                    if g=='S3': value+=f" ({shape['network_max_min_ratio']:.6f})"
                values.append(value)
        lines.append('| '+g+' | '+' | '.join(values)+' |')
    c=byid['male']['C_s0_b25']
    lines += ['', 'Secondary S/Overall cells are descriptive evaluations of the same predicates from audited summaries; the saved results declare S and Overall only for the primary. '
              'C_literal_zero and D_literal_zero are additional observations, not extra acceptance gates; historical D tests completeness. '
              f"Male C fails: bitter25 alone is {rate(c)} Hz against its {results['male']['gates']['L']['C_limit_hz']:.3f} Hz limit. Male R is silent throughout.", '',
              '### Sugar curves side by side','',
              'Mean ± population SD, Hz; n=30 per level. Historical references use different input sets/layouts and are not paired with M1j. '
              'Female historical values are the frozen 23-cell left readout in the [Phase 0 report](phase0_report.md#results); 120 Hz was not measured there.', '',
              '| Sugar Hz | Male L | Male R | Female left | Female right | Historical M1i sugar17 L | Historical female23 left |',
              '|---|---:|---:|---:|---:|---:|---:|']
    old={r['id']:r for r in read(DATA / 'm1i_a_results.json')['conditions']}
    # Read the original report column directly, avoiding the male-side remapping
    # in phase0_female_reference.json (its R corresponds to Shiu frozen left).
    history={}
    for line in (ROOT / 'docs/phase0_report.md').read_text(encoding='utf-8').splitlines():
        parts=[x.strip() for x in line.split('|')]
        if len(parts)>5 and parts[1]=='A' and parts[2].endswith('Hz sugar'):
            history[int(parts[2].split()[0])]=parts[4]
    for level in (25,50,100,120,200):
        cid='AP_sugar_120' if level==120 else f'A_s{level}_b0'
        values=[rate(byid[b][cid],s) for b in ('male','female') for s in ('L','R')]
        lines.append(f"| {level} | " + ' | '.join(values+[rate(old[cid]),history.get(level,'Not measured')])+' |')
    lines += ['', '### Every condition','', 'Mean ± population SD, Hz; n=30 for every row. Network and neuron counts are median [min–max].','',
              '| Brain | Condition | MN9 L Hz | MN9 R Hz | Whole-network spikes | Neurons fired |', '|---|---|---:|---:|---:|---:|']
    for b,r in results.items():
        for row in r['conditions']:
            lines.append(f"| {b} | {row['id']} | {rate(row)} | {rate(row,'R')} | {extent(row['whole_network_spikes'])} | {extent(row['neurons_fired'])} |")
    lines += ['', '### A′ at 120 Hz','', 'n=30 paired seeds per brain; difference is bilateral LB3c subset minus bilateral LB3b union LB3c.','',
              '| Brain / side | Union Hz | LB3c-only Hz | Paired subset−union Hz | Lower/equal/higher trials |','|---|---:|---:|---:|---:|']
    for b,r in results.items():
        for side in ('L','R'):
            a=r['a_prime'][side]
            counts='/'.join(str(a[k+'_trials']) for k in ('lower','equal','higher'))
            lines.append(f"| {b} / {side} | {rate(byid[b]['AP_sugar_120'],side)} | {rate(byid[b]['AP_sugar_lb3c_120'],side)} | {mean_sd(a['mean_hz'],a['sd_hz'])} | {counts} |")
    lines += ['', '### Scope of S3 and recorded activity','',
              'S3 tests consistency within sugar 200 trials, not absolute activity. Whole-network spikes, median [min–max]: '
              + '; '.join(f"{b} sugar100 {extent(byid[b]['A_s100_b0']['whole_network_spikes'])}, sugar200 {extent(byid[b]['A_s200_b0']['whole_network_spikes'])}" for b in ('male','female'))+'.', '',
              f"The female sugar100 range and sugar200 counts above, and female A′ LB3c-only {rate(byid['female']['AP_sugar_lb3c_120'])} Hz above union {rate(byid['female']['AP_sugar_120'])} Hz on the primary, are recorded observations. "
              'No mechanism is inferred. Female S2 passes despite the 100→120 decrease because it is within the declared pooled population-SD allowance.', '',
              '### Execution and verification','',
              'The saved WSL runs were launched from commits `4f12a89` / `b859f68`; run metadata records source hashes rather than a launch git commit. '
              'The audit checks those hashes, plans, raw ledgers, every trial rate/latency, source counts, network counts and neurons fired, '
              'and reconstructs every summary field with the unchanged A–D/S predicates. No simulation or runner change was performed for this report.', '',
              f"Independent audit: {audit['raw_trials']} M1j trials, {audit['MN9_neuron_trials']} MN9-neuron trials, {audit['poisson_unit_trials']:,} saved Poisson-unit trials exactly reconstructed. "
              + '; '.join(f"{b}: {a['AP_paired_trials']} A′ pairs / {a['AP_identical_shared_unit_trains']} shared unit trains / {a['AP_silent_non_subset_unit_trials']} silent non-subset unit trials, {a['A200_B0_identical_network_pairs']} identical A200/B0 networks" for b,a in audit['runs'].items())
              + '. M0 adds ten exact output comparisons; its saved-input limitation is stated above. Repeated seeds are not independent extra replicates.', '',
              '[Male results](../data/malecns/m1j_male_results.json), [female results](../data/m1j_female_results.json), '
              '[independent audit](../data/malecns/m1j_runs_audit.json), [audit implementation](../sim/malecns/audit_m1j.py), '
              '[report/corruption tests](../sim/malecns/test_m1j_report.py). '
              'No product, frozen-data, copy or honesty-table changes. No further variant, gain/threshold change, M2 or product migration follows.', '']
    return '\n'.join(lines)


def ledger():
    text=LEDGER_DOCUMENT.read_text(encoding='utf-8')
    old=text.split('## Male line closing ledger — eight variants (2026-09-18)',1)[1].split('\n## ',1)[0]
    rows=[line for line in old.splitlines() if line.startswith('| [M1')]
    equal(len(rows),8,'Eight historical ledger rows')
    male=read(result_path('male')); female=read(result_path('female'))
    return '\n'.join([LEDGER,'','| Variant | Structural rationale / design | Recorded result under its declared rule |','|---|---|---|',*rows,
        '| [M1j](bilateral_sugar_policy.md#m1j-results-checkpoint--2026-09-19) | Bilateral typed sugar34 male / sugar57 female; unchanged respective substrates; both primary A–D + S required for adoption | '
        + f"Male {verdict(male['overall_primary'])}: failing gates {', '.join(failures(male)) or 'none'}; female {verdict(female['overall_primary'])}: failing gates {', '.join(failures(female)) or 'none'}. Adoption "
        + ('ADOPTED' if male['overall_primary'] and female['overall_primary'] else 'REJECTED')+'; male R silent. |','',
        'Per the declared stop rule, the male line is Closed after nine variants whatever the M1j result. No further variant, gain, threshold change, M2 or product migration follows. '
        'Historical M1c passes retain their original rules; S is not applied retroactively. No product, frozen-data, copy or honesty-table changes.',''])


def check_or_append(path=DOCUMENT, marker=MARKER, block=None):
    text=path.read_text(encoding='utf-8')
    block=generate() if block is None else block
    if marker not in text:
        with path.open('a',encoding='utf-8',newline='') as stream:
            stream.write('\n'+block)
        text=path.read_text(encoding='utf-8')
    equal(text.count(marker),1,'Unique checkpoint')
    tail=marker+text.split(marker,1)[1]
    require(tail.startswith(block),'Report regeneration mismatch')
    require(not tail[len(block):] or tail[len(block):].startswith('\n## '),'Report boundary mismatch')
    print('M1j report regeneration PASS: '+path.name)


if __name__ == '__main__':
    check_or_append()
    check_or_append(LEDGER_DOCUMENT,LEDGER,ledger())
