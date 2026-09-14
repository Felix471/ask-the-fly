# SPDX-License-Identifier: MIT
"""Render M1c sections from saved summaries, retaining unscaled M1 columns."""
import json
from sim.malecns.substrate import DATA


def generate():
    old=json.loads((DATA/'phase0_results.json').read_text())
    baseline={r['id']:r for r in old['conditions']}
    activity={r['condition']:r for r in json.loads((DATA/'m1b_diagnosis.json').read_text())['conditions']}
    plan=json.loads((DATA/'rescale_plan.json').read_text())
    audit=json.loads((DATA/'rescale_audit.json').read_text())
    def rate(r,s):
        return f"{r[s+'_mean']:.3f} ± {r[s+'_sd']:.3f}"
    def extent(s):
        median=f"{s['median']:,.1f}".removesuffix('.0')
        return f"{median} [{s['min']:,.0f}–{s['max']:,.0f}]"
    def verdict(value):
        return 'PASS' if value else 'FAIL'
    lines=['## M1c — two pre-declared rescalings', '',
           'Only `w_syn` changes; the external Poisson kick remains tied as `w_syn*f_poi`. '
           'The full-precision definitions and stop rule above were frozen before any candidate result. '
           'Both candidates reuse the unchanged M1 trial runner, physical 91-cell input layout, '
           'seeds 20260910–20260939, one-second duration, and historical gate predicates. '
           'No readout was substituted and no third weight or M2 was run.', '',
           f"The [pre-run plan](../data/malecns/rescale_plan.json) chose {plan['memory']['workers']} workers: "
           f"WSL available {plan['memory']['wsl_available_gib']:.2f} GiB, host free {plan['memory']['host_free_gib']:.2f} GiB, "
           f"reserve {plan['memory']['reserve_gib']:.2f} GiB, budget {plan['memory']['worker_budget_gib']:.1f} GiB/worker "
           '(over 1.5× measured M1 peak). Candidate pools ran sequentially. Each candidate has 420 A–D '
           'plus 60 A′ trials, **960 total**, not 840 including A′. Means ± population SD use n=30. '
           'Network counts are median [minimum–maximum]; Poisson-source events are excluded.', '']
    passing=[]
    for name in ['all','mn9']:
        d=json.loads((DATA/f'rescale_{name}_results.json').read_text())
        p=json.loads((DATA/f'stim_protocol_malecns_{name}.json').read_text())
        m=d['metadata']
        lines += [f'### Candidate `{name}` — {p["model"]["w_syn_mV"]:.9f} mV', '',
                  f"[Protocol and derivation](../data/malecns/stim_protocol_malecns_{name}.json); "
                  f"[results and raw-ledger hash](../data/malecns/rescale_{name}_results.json). "
                  f"Simulation commit `{m['git_commit']}`; Brian2 {m['brian2']} / {m['codegen']}; "
                  f"parallel walltime {m['walltime_s']:.1f} s, peak worker RSS {m['peak_worker_rss_gib']:.3f} GiB. "
                  f"Completed {m['completed_utc']}.", '',
                  '| Condition | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | M1 network spikes | Rescaled network spikes |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for r in d['conditions']:
            if r['gate']=='AP':
                continue
            o=baseline[r['id']]
            lines.append(f"| {r['id']} | {rate(o,'R')} | {rate(o,'L')} | {rate(r,'R')} | {rate(r,'L')} | {extent(activity[r['id']]['spikes'])} | {extent(r['whole_network_spikes'])} |")
        lines += ['', '| Gate | M1 R | M1 L | Rescaled R16949 (contra) | Rescaled L10331 (ipsi) |', '|---|---|---|---|---|']
        for key,label in [('A','A: sugar rises'),('B','B: bitter suppresses'),('C','C: bitter-alone limit'),('D','D: completeness'),
                          ('D_literal_zero','Baseline literal zero (additional)'),('C_literal_zero','Bitter-alone literal zero (additional)'),('overall','Overall A–D')]:
            values=[old['gates'][s][key] for s in ['R','L']]+[d['gates'][s][key] for s in ['R','L']]
            lines.append('| '+label+' | '+' | '.join(verdict(v) for v in values)+' |')
        for side in ['R','L']:
            g=d['gates'][side]
            if g['overall']:
                passing.append(f'{name}/{side}')
        a=[r for r in d['conditions'] if r['gate']=='A']
        for side in ['R','L']:
            sugar_means='/'.join(f"{r[side+'_mean']:.3f}" for r in a)
            lines += ['', f"{side} sugar means at 25/50/100/200 Hz: **{sugar_means} Hz**. "+
                      ('A passes the historical adjacent-zero exception and >5 Hz endpoint; this is not evidence of a graded response over the lower levels.' if d['gates'][side]['A'] and any(r[side+'_mean']==0 for r in a) else
                       'A does not pass.' if not d['gates'][side]['A'] else 'A passes the unchanged predicate.')]
        if all(r['R_mean']==0 for r in d['conditions'] if r['gate']=='B'):
            lines += ['', 'R is silent in every B condition: B fails its strict endpoint test (`0 < 0` is false), not a measured reversal of bitter suppression.']
        lines += ['', '| Soft indicator (not a gate) | Rescaled R | Rescaled L |', '|---|---:|---:|']
        dose=[]; suppression=[]
        for side in ['R','L']:
            endpoint=a[-1][side+'_mean']
            dose.append(f"{a[-2][side+'_mean']/endpoint:.3f}" if endpoint else 'undefined (0/0)')
            v=d['gates'][side]['bitter200_suppression_fraction']
            suppression.append(f'{100*v:.2f}%' if v is not None else 'undefined (0/0)')
        lines += ['| Sugar100 / sugar200 | '+' | '.join(dose)+' |',
                  '| Bitter200 suppression vs bitter0 | '+' | '.join(suppression)+' |']
        lines += ['', '**A′ at 120 Hz:** same seeds and fixed layout; difference = LB3c12 minus sugar17.', '',
                  '| Set / comparison | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | Network spikes |',
                  '|---|---:|---:|---:|---:|---:|']
        for cid in ['AP_sugar_120','AP_sugar_lb3c_120']:
            r=next(r for r in d['conditions'] if r['id']==cid); o=baseline[cid]
            lines.append(f"| {cid} | {rate(o,'R')} | {rate(o,'L')} | {rate(r,'R')} | {rate(r,'L')} | {extent(r['whole_network_spikes'])} |")
        fmt_ap=lambda obj,s: f"{obj['a_prime'][s]['mean_hz']:.3f} ± {obj['a_prime'][s]['sd_hz']:.3f}"
        lines.append('| Paired difference | '+' | '.join([fmt_ap(old,s) for s in ['R','L']]+[fmt_ap(d,s) for s in ['R','L']])+' | — |')
        lines += ['', 'Paired lower/equal/higher trial counts: '+', '.join(f"{s} {d['a_prime'][s]['lower_trials']}/{d['a_prime'][s]['equal_trials']}/{d['a_prime'][s]['higher_trials']}" for s in ['R','L'])+'.', '',
                  '| Condition | Neurons fired: median [min–max] | R latency median, ms (firing trials/30) | L latency median, ms (firing trials/30) |',
                  '|---|---:|---:|---:|']
        for r in d['conditions']:
            lat=[]
            for s in ['R','L']:
                v=r[s+'_latency_median_ms']
                lat.append(('none' if v is None else f'{v:.2f}')+f" ({r[s+'_firing_trials']}/30)")
            lines.append(f"| {r['id']} | {extent(r['neurons_fired'])} | {' | '.join(lat)} |")
        lines += ['', 'Latency medians include firing trials only; silence is none, not zero latency.', '']
    lines += ['### M1c checkpoint and stop rule', '',
              ('Passing candidate/side combinations: **'+', '.join(passing)+'**. These satisfy the pre-declared gate rule, not behavioural calibration or a primary-readout decision.') if passing else
              '**Neither candidate passes all four gates on either side. The male line stops under the pre-declared rule; no third value will be tried in this task.**', '',
              'The tracing-status evidence and 556-versus-6,012 input asymmetry remain a likely '
              'reconstruction explanation, not a causal demonstration: rescaling does not repair or '
              'control tracing completeness. Both sides are reported; the primary readout remains an '
              'owner decision. [Tracing preflight and female replay comparison](malecns_m1b.md).', '',
              f"[Raw-event audit](../data/malecns/rescale_audit.json): {audit['total_trials']} trials / "
              f"{2*audit['total_trials']} MN9-neuron trials reconstructed; all network counts, rates, "
              'latencies, summaries, A′ paired differences and bilateral gates agree. All 960 complete '
              'Poisson event arrays match their M1 counterparts; 43,680 physical-slot trains match '
              'between candidates. Each candidate has 30 identical A200/B0 whole-network pairs and '
              '360 identical shared A′ LB3c input trains. Duplicate A200/B0 observations are not n=60; '
              'the two weights and M1 are paired by seed, not pooled replicates.', '',
              'Brian2 retained the historical `rates` namespace warning and used its internal variable; '
              'input-event equality was checked rather than suppressing the warning. Raw spikes, source '
              'rates and ledgers remain ignored under `data/malecns/runs/m1c/`. Female frozen data, '
              'pipeline, site, scoring and README honesty table are unchanged. Stop here; no M2.', '']
    lines += ['Software verification: 40 male-only unit tests, 315 existing Python tests, '
              '67 Node tests and release validation pass. These checks do not establish behavioural validity.', '']
    lines += ['### Post-M1c decision — 2026-09-14', '',
              "**Post-M1c owner decision — 2026-09-14:** the primary male readout is **L10331**, chosen on reconstruction-completeness grounds; **R16949 remains recorded as secondary**. R16949 has 556 retained incoming synapses versus 6,012 for L10331, with neuPrint status labels `RT Hard to trace` versus `Roughly traced`. GNG postsynaptic capture is approximately 35% (35.3665%), an **ROI-wide figure, not either neuron's completeness estimate**. The owner records reconstruction completeness as the most likely explanation for the laterality reversal, not a demonstrated causal result. The cross-brain mapping places both bodies with the female MN9s in CB0701; it does not indicate that Table S1 identified the wrong bodies.", '',
              'This decision was made **after M1c completed and its results were reported**. '
              'The completed runs, candidate protocols and original pre-declared stop rule '
              'remain unchanged: all four gates must pass on at least one side. **Both '
              'candidates passed under that original rule, on L10331.** This is not a '
              'retrospective amendment to the run design. Candidate selection is still '
              'pending; no rerun is performed or authorised by this record. '
              '[Mapping, tracing and ROI-capture evidence](malecns_m1b.md#additional-mapping-and-roi-capture-check); '
              '[OQ-11](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).', '']
    return '\n'.join(lines)


if __name__=='__main__':
    print(generate())
