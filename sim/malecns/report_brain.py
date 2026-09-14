"""Render the M1f checkpoint from audited saved results, never simulate."""
import json
from sim.malecns.substrate import DATA,ROOT


def generate():
    record=json.loads((DATA/'substrate_record_brain.json').read_text())
    audit=json.loads((DATA/'brain_runs_audit.json').read_text())
    female={r['id']:r for r in json.loads((DATA/'phase0_female_reference.json').read_text())['rows']}
    grid=json.loads((ROOT/'data/lookup_table.json').read_text())
    f120=next(r for r in grid['cells'] if r['hz']==dict(sugar=120,bitter=0,water=0,ir94e=0))
    data={c:json.loads((DATA/f'brain_{c}_results.json').read_text()) for c in ['unscaled','density']}
    rate=lambda r,s:f"{r[s+'_mean']:.3f} ± {r[s+'_sd']:.3f}"
    extent=lambda s:f"{s['median']:,.1f} [{s['min']:,}–{s['max']:,}]"
    verdict=lambda b:'PASS' if b else 'FAIL'
    count=record['counts']; density=record['density']
    lines=['## M1f checkpoint — brain-only endpoint approximation','',
           'Results: '+', '.join(f"**{c}: {verdict(d['overall_primary'])}**" for c,d in data.items())+'. No candidate is selected automatically; no additional variant is run.','',
           'Structural rationale, cut limitations, two weights and S criteria were declared above before results. Source declaration `4d1bb58`; preflight `b2dbc51`. Unscaled started at `b2dbc51`, density at `7140e47` after the separate edge-threshold audit commit; all frozen simulation-source and protocol hashes stayed identical. Same91 physical input slots and M1 seeds20260910–20260939,30 trials per condition;480 per candidate,960 total. Pools sequential,8 workers; reserve15.13 GiB from60.51 GiB WSL available (host80.45 GiB),5.4 GiB/worker budget.','',
           '| Substrate | Neurons | Edges | Synapses | Mean unsigned in-degree | Male/female ratio |','|---|---:|---:|---:|---:|---:|',
           f"| Male brain endpoint cut | {count['neurons']:,} | {count['edges']:,} | {count['synapses']:,} | {density['male_mean']:.6f} | {density['r_brain']:.9f} |",
           '| Male whole CNS (M0) | 166,700 | 25,582,938 | 124,177,617 | 744.916719 | 1.895191250 |',
           f"| Female frozen | {density['female_neurons']:,} | 15,091,983 | {density['female_synapses']:,} | {density['female_mean']:.6f} | 1 |",'',
           '[Brain record and SHA256 hashes](../data/malecns/substrate_record_brain.json); [edge-for-edge audit](../data/malecns/brain_substrate_audit.json). This is not an exact anatomical brain cut: crossing-body VNC synapses cannot be removed from aggregate endpoint counts. No sign rule, female substrate, product or scoring changes.','',
           '| Gate, L10331 only | Unscaled0.275 | Density-scaled0.156145179 |','|---|---|---|']
    for k in ['A','B','C','D']:
        lines.append('| '+k+' | '+' | '.join(verdict(d['gates']['L'][k]) for d in data.values())+' |')
    for k in ['S1','S2','S3','S']:
        vals=[]
        for d in data.values():
            sg=d['shape_gate']; detail=f" ({sg['coverage']}/5 positive)" if k=='S1' else f" (max/min {sg['network_max_min_ratio']:.6f})" if k=='S3' and sg['network_max_min_ratio'] is not None else ''
            vals.append(verdict(sg[k])+detail)
        lines.append('| '+k+' | '+' | '.join(vals)+' |')
    lines.append('| Overall A–D + S | '+' | '.join(verdict(d['overall_primary']) for d in data.values())+' |')
    lines += ['', '| Secondary R16949 gate | Unscaled | Density-scaled |', '|---|---|---|']
    for k in ['A','B','C','D']:
        lines.append('| '+k+' | '+' | '.join(verdict(d['gates']['R'][k]) for d in data.values())+' |')
    lines += ['', 'R16949 is recorded but not used for acceptance; S is evaluated on L10331 only, as pre-declared. Historical D is the completeness predicate; literal baseline-zero passes on both sides for both candidates. S3 is the specified sugar200 max/min bound, not a general statistical test of unimodality.','',
              '### Five-level sugar curve','',
              'Mean ± population SD, Hz, n=30. Female frozen23 reference is historical pre-correction Phase0 at25/50/100/200 and the corrected frozen-grid120 point; not a matched five-level female rerun. Shiu L is female contralateral, Shiu R ipsilateral; male L is ipsilateral. Hypnagogia reports **80.4 Hz at200**, with brain-only144,209 neurons,0.581 scaling, different roster/sign and mapped-input definitions; no matched bilateral values or lower-dose curve are supplied by that reported comparison. It is contextual evidence, not a gate or target fit. [Female references](../data/malecns/phase0_female_reference.json); [grid120](../data/lookup_table.json); [hypnagogia source](https://github.com/ankthba/hypnagogia/blob/86da5f93e25a2f1ac78c2fa810f34a4a57992b66/results.md#L45-L60).','',
              '| Sugar Hz | Unscaled L | Unscaled R | Density L | Density R | Female Shiu L | Female Shiu R | Hypnagogia MN9 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for level in [25,50,100,120,200]:
        cid=f'A_s{level}_b0' if level!=120 else 'AP_sugar_120'
        vals=[]
        for d in data.values():
            r=next(r for r in d['conditions'] if r['id']==cid)
            vals.extend(rate(r,s) for s in ['L','R'])
        if level==120:
            vals.extend([f"{f120['mn9_left_mean']:.3f} ± {f120['mn9_left_std']:.3f}",f"{f120['mn9_right_mean']:.3f} ± {f120['mn9_right_std']:.3f}"])
        else:
            vals.extend(rate(female[cid],s) for s in ['R','L'])
        lines.append(f'| {level} | '+' | '.join(vals)+(' | 80.4 (reported mean) |' if level==200 else ' | Not reported |'))
    lines += ['', '### All conditions: network activity and both MN9s','',
              '| Condition | Unscaled L Hz | Unscaled R Hz | Unscaled network spikes median [min–max] | Density L Hz | Density R Hz | Density network spikes median [min–max] |','|---|---:|---:|---:|---:|---:|---:|']
    for a,b in zip(data['unscaled']['conditions'],data['density']['conditions']):
        assert a['id']==b['id']
        lines.append(f"| {a['id']} | {rate(a,'L')} | {rate(a,'R')} | {extent(a['whole_network_spikes'])} | {rate(b,'L')} | {rate(b,'R')} | {extent(b['whole_network_spikes'])} |")
    lines += ['', '### A′ at120 Hz','',
              'Both sets are newly run with paired seeds and identical91-slot layout; subset=LB3c12, union=sugar17.','',
              '| Candidate | L subset−union Hz | R subset−union Hz | L lower/equal/higher trials | R lower/equal/higher trials |','|---|---:|---:|---:|---:|']
    for c,d in data.items():
        ap=d['a_prime']
        lines.append('| '+c+' | '+' | '.join(f"{ap[s]['mean_hz']:.3f} ± {ap[s]['sd_hz']:.3f}" for s in ['L','R'])+' | '+' | '.join('/'.join(str(ap[s][k+'_trials']) for k in ['lower','equal','higher']) for s in ['L','R'])+' |')
    lines += ['', '### Execution and verification','',
              '| Candidate | Parallel wall seconds | Peak worker GiB | Completion UTC |','|---|---:|---:|---|']
    for c,d in data.items():
        m=d['metadata'];lines.append(f"| {c} | {m['walltime_s']:.1f} | {m['peak_worker_rss_gib']:.3f} | {m['completed_utc']} |")
    lines += ['', 'Live per-worker weights were checked after construction and restore before positive-duration runs: stimulus68.75 mV/event for both; recurrence0.275 or0.1561451789913389 mV per signed synapse. All worker logs are hashed in the result manifests. [Unscaled result](../data/malecns/brain_unscaled_results.json); [density result](../data/malecns/brain_density_results.json).','',
              f"[Saved-event audit](../data/malecns/brain_runs_audit.json): {sum(x['raw_trials'] for x in audit['candidates'].values())} trials /1920 MN9-neuron trials reconstructed; rates, latencies, driven-cell counts, network counts, gates and A′ statistics pass. Every input array matches M1; {audit['cross_candidate_input_trains_identical']:,} cross-candidate input trains match; each candidate has360 identical shared A′ trains and30 identical A200/B0 network pairs. Repeated A200/B0 or seeds across variants are not independent extra replicates. Raw spikes remain ignored under data/malecns/runs/m1f/.",'',
              'Interpretation under the unchanged gates: the unscaled brain cut has a five-level rising mean sugar curve, but fails B because the mean rises from0 at bitter100 to0.033 Hz at bitter200, and fails C because bitter-alone L means25.067–76.600 Hz exceed1 Hz. The density-scaled cut passes A–D but has positive L means only at120 and200 Hz, so fails S1. Large network counts can persist when MN9 is silent; passing S3 at200 does not establish network stability at other conditions. Neither candidate passes the complete pre-declared rule.','',
              'Verification:55 male tests,315 existing Python tests,67 Node tests, release validation,82 local report links, generated-report comparison and diff whitespace checks pass.','',
              'Checkpoint only: no further variant is selected or run.','']
    return '\n'.join(lines)


if __name__=='__main__':
    print(generate())
