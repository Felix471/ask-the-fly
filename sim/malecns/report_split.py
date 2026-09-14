"""Render audited M1d checkpoint from saved results only."""
import json
from sim.malecns.substrate import DATA, ROOT


def generate():
    d=json.loads((DATA/'split_results.json').read_text())
    audit=json.loads((DATA/'split_audit.json').read_text())
    female={r['id']:r for r in json.loads((DATA/'phase0_female_reference.json').read_text())['rows']}
    grid=json.loads((ROOT/'data/lookup_table.json').read_text())
    f120=next(r for r in grid['cells'] if r['hz']==dict(sugar=120,bitter=0,water=0,ir94e=0))
    rows={r['id']:r for r in d['conditions']}; m=d['metadata']; sg=d['shape_gate']
    rate=lambda r,s:f"{r[s+'_mean']:.3f} ± {r[s+'_sd']:.3f}"
    extent=lambda s:f"{s['median']:,.1f} [{s['min']:,}–{s['max']:,}]"
    verdict=lambda b:'PASS' if b else 'FAIL'
    lines=['## M1d checkpoint — split stimulus and recurrent weights','',
           '**Overall primary L10331: '+verdict(d['overall_primary'])+'.** A–D pass, but shape gate S fails coverage S1: only '+str(sg['coverage'])+' of five levels has a positive mean. S2 and S3 pass. This failed variant remains in the record; no automatic follow-up variant is run.','',
           '[Pre-run protocol](../data/malecns/stim_protocol_malecns_split.json); [plan](../data/malecns/split_plan.json); [results](../data/malecns/split_results.json); [raw-event audit](../data/malecns/split_audit.json).', '',
           f"Protocol/source declaration `dc633d7`; run commit `{m['git_commit']}`. Exactly 480 trials, seeds20260910–20260939, 30 per condition, duration1 s. Eight workers; WSL free {m['memory']['wsl_available_gib']:.2f} GiB, host free {m['memory']['host_free_gib']:.2f} GiB, reserve {m['memory']['reserve_gib']:.2f} GiB, budget5.4 GiB/worker (>1.5× M1 peak). Brian2 {m['brian2']} cython; wall {m['walltime_s']:.1f} s, peak worker {m['peak_worker_rss_gib']:.3f} GiB. Completed {m['completed_utc']}.",'',
           '| Gate | L10331 primary | R16949 secondary (not deciding) |','|---|---|---|']
    for k in ['A','B','C','D']:
        lines.append(f"| {k} | {verdict(d['gates']['L'][k])} | {verdict(d['gates']['R'][k])} |")
    lines += [f"| S1: coverage ≥4/5 | {verdict(sg['S1'])}: {sg['coverage']}/5 | Not evaluated |",
              f"| S2: adjacent decrease ≤ pooled SD | {verdict(sg['S2'])} | Not evaluated |",
              f"| S3: network max/min <3 at200 | {verdict(sg['S3'])}: {sg['network_max_min_ratio']:.6f} | Not evaluated |",
              f"| S overall | {verdict(sg['S'])} | Not evaluated |",
              f"| A–D plus S | {verdict(d['overall_primary'])} | Not deciding |",'',
              'Historical D checks completeness; additionally, baseline and bitter-alone MN9 rates are literally zero on both sides. A retains its historical adjacent-zero exception, which is why A can pass while S1 fails. S3 is the owner-defined count-ratio criterion, not a general statistical test proving unimodality.','',
              '### Five-level sugar curve','',
              'Mean ± population SD, Hz. Female is frozen23 throughout: historical pre-correction Phase0 at25/50/100/200; **120 uses the corrected frozen grid**, not the typed33 A′ arm. Different layouts/seed schemes and historical refractory handling make this a contextual comparison, not one matched female curve or a controlled sex comparison. Female Shiu L is contralateral; Shiu R is ipsilateral. [Female Phase0 source](../data/malecns/phase0_female_reference.json); [grid source](../data/lookup_table.json).','',
              '| Sugar Hz | Male L10331 ipsi | Male R16949 contra | Female Shiu L contra | Female Shiu R ipsi | Male network spikes: median [min–max] |','|---|---:|---:|---:|---:|---:|']
    for level in [25,50,100,120,200]:
        cid=f'A_s{level}_b0' if level!=120 else 'AP_sugar_120'; r=rows[cid]
        if level==120:
            fL=f"{f120['mn9_left_mean']:.3f} ± {f120['mn9_left_std']:.3f}"; fR=f"{f120['mn9_right_mean']:.3f} ± {f120['mn9_right_std']:.3f}"
        else:
            fL=rate(female[cid],'R'); fR=rate(female[cid],'L')
        lines.append(f"| {level} | {rate(r,'L')} | {rate(r,'R')} | {fL} | {fR} | {extent(r['whole_network_spikes'])} |")
    lines += ['', '### Every condition and A′','',
              '| Condition (sugar/bitter Hz) | L10331 Hz | R16949 Hz | Network spikes: median [min–max] | Neurons fired: median [min–max] |','|---|---:|---:|---:|---:|']
    for r in d['conditions']:
        lines.append(f"| {r['id']} | {rate(r,'L')} | {rate(r,'R')} | {extent(r['whole_network_spikes'])} | {extent(r['neurons_fired'])} |")
    lines += ['', 'A′: sugar17 versus LB3c12 at120 Hz, same layout/seeds. Both are **0 ±0 Hz on both MN9s**; paired subset-minus-union is **0 ±0 Hz**, equal in30/30 trials on each side. Duplicate A200/B0 runs are not pooled as n=60.','',
              f"Saved-event audit: {audit['raw_trials']} trials / {audit['MN9_neuron_trials']} MN9-neuron trials; all rates, latencies, source-cell counts, network counts, summaries, gates and paired differences verified. All480 Poisson event arrays match M1; all360 shared A′ LB3c trains match; all30 A200/B0 whole-network pairs match. No female simulation or product/frozen-data change. 49 male tests,315 existing Python tests,67 Node tests and release validation pass.",'',
              'M1e is the separate [community survey](malecns_community_survey.md). Stop at this checkpoint; no further variant is selected or run.','']
    return '\n'.join(lines)


if __name__=='__main__':
    print(generate())
