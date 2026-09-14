# SPDX-License-Identifier: MIT
"""Render the saved-spike M1b checkpoint; no model imports or simulation."""
import json
from sim.malecns.substrate import DATA


def generate():
    d=json.loads((DATA/'m1b_diagnosis.json').read_text())
    full=json.loads((DATA/'runs/m1b/full_diagnosis.json').read_text())
    audit=json.loads((DATA/'runs/m1b/audit.json').read_text())
    def rangefmt(s, decimals=0):
        if s is None:
            return '—'
        def fmt(value):
            return f'{value:,.1f}'.removesuffix('.0') if decimals==0 else f'{value:,.{decimals}f}'
        return f"{fmt(s['median'])} [{fmt(s['min'])}–{fmt(s['max'])}]"
    def rate(s):
        return '—' if s is None else f"{s['mean']:.3f} ± {s['sd']:.3f}"
    lines=['# MaleCNS M1b: saved-spike diagnosis', '',
           'M1b only: **zero simulations**. All 480 saved M1 trials are inspected (16 conditions, 30 each), '
           'including A′. Each one-second recording is checked against its saved spike hash and MN9 counts. '
           'A200 and B0 are identical-drive/seed repeats, not 60 independent observations. '
           'No change to the female pipeline, either frozen substrate, site, scores, or primary-readout choice.', '',
           'Sources: [M1 report](malecns_phase0.md), [M1b summary/provenance](../data/malecns/m1b_diagnosis.json), '
           '[analysis code](../sim/malecns/diagnose_m1.py). Full per-trial ledger, source hashes, 50-ms spike bins, '
           'regional counts, and selected partner IDs are retained locally at '
           '`data/malecns/runs/m1b/full_diagnosis.json`, with its hash in the versioned summary.', '',
           '## Network activity per condition', '',
           'Median [minimum–maximum] across 30 trials. Neurons fired means distinct neuron IDs with at least '
           'one spike in [0, 1 s); Poisson-source events are not network spikes.', '',
           '| Condition: sugar/bitter Hz | Network spikes | Neurons fired | High-count trials / 30 |',
           '|---|---:|---:|---:|']
    for row in d['conditions']:
        lines.append(f"| {row['condition']} | {rangefmt(row['spikes'])} | {rangefmt(row['neurons'])} | {row['runaway_n']} |")
    lines+=['', '## Quiet / runaway split', '',
            '**Descriptive analyst rule, not a biological threshold or gate:** quiet <500,000 network spikes '
            'in one second; runaway/high-count ≥500,000. “Quiet” is relative and does not mean silent. '
            'One shared threshold is applied without looking at MN9 to assign groups; this is a post-hoc '
            'screen, not proof of two discrete dynamical states. The threshold does not affect density or '
            'either proposed rescaling. Rates below are mean ± population SD, Hz, within the indicated group.', '',
            '| Condition | Group | n | MN9 R, contra | MN9 L, ipsi |', '|---|---|---:|---:|---:|']
    for g in d['groups']:
        lines.append(f"| {g['condition']} | {g['group']} | {g['n']} | {rate(g['R_hz'])} | {rate(g['L_hz'])} |")
    lines+=['','Sensitivity: high-count trial counts at alternative descriptive cutoffs (no gate recalculation):','',
            '| Cutoff (spikes) | A25/0 | B200/25 | C0/25 |','|---|---:|---:|---:|']
    for cutoff, counts in d['split']['sensitivity'].items():
        lines.append(f"| {int(cutoff):,} | {counts['A_s25_b0']} | {counts['B_s200_b25']} | {counts['C_s0_b25']} |")
    lines+=['', '## Onset and anatomical distribution in high-count trials', '',
            'Time to 1,000 means the timestamp of the 1,000th sorted whole-network spike, measured from '
            'stimulus onset; it is not necessarily the onset of the later high-activity episode.', '',
            '**Source limitation:** the frozen v1.0 body annotations contain no `region` column. '
            'We instead use the documented `superclass` anatomy in '
            '[Berg et al., Methods: Cell annotations / Superclass](https://doi.org/10.1016/j.cell.2026.08.015). '
            '`cb_*`, `ol_*` and visual projection/centrifugal classes are brain; `vnc_*` are VNC; '
            'ascending/descending classes are crossing; ENS remains unclassified. '
            'This is a neuron-class proxy, not anatomical localization of each spike or synapse. '
            'Crossing neurons are not assigned to a single region. Exact mapping and population sizes are '
            'in the [M1b record](../data/malecns/m1b_diagnosis.json).', '',
            'First window = [0, 50 ms); last window = [500, 1,000 ms). The following four-part cells give '
            'mean distinct neurons per trial as **brain / VNC / crossing / unclassified**. '
            'All high-count conditions are shown, not only the three highlighted gate failures.', '',
            '| Condition | n | Time to 1,000, ms: median [min–max] | First 50 ms: neurons | Last 500 ms: neurons |',
            '|---|---:|---:|---|---|']
    for r in d['runaway_by_condition']:
        def neurons(w):
            return ' / '.join(f"{r['windows'][w][k]['neurons']['mean']:.1f}" for k in ('brain','VNC','crossing','unclassified'))
        lines.append(f"| {r['condition']} | {r['n']} | {rangefmt(r['first_1000_ms'],1)} | {neurons('early')} | {neurons('late')} |")
    lines+=['', 'For the three highlighted conditions, pooled spike shares within each window '
            '(not neuron fractions; unclassified is retained in the denominator):', '',
            '| Condition | Window | Brain | VNC | Crossing | Unclassified |', '|---|---|---:|---:|---:|---:|']
    for r in d['groups']:
        if r['group']!='runaway':
            continue
        for w in ('early','late'):
            shares=r[w+'_pooled_spike_share']
            lines.append(f"| {r['condition']} | {w} | "+' | '.join(f'{100*shares[k]:.2f}%' for k in ('brain','VNC','crossing','unclassified'))+' |')
    lines+=['', 'In the 72 high-count trials of these three highlighted conditions, an additional '
            '20-bin (50 ms per bin) audit finds **no individual-trial bin with a VNC majority of spikes**. '
            'Maximum pooled VNC shares across the 20 bins are '+
            ', '.join(f"{name}: {100*share:.2f}%" for name,share in audit['selected_conditions_max_pooled_vnc_share_any_50ms_bin'].items())+'. '
            'The two requested endpoint windows are brain-dominated by both spikes and recruited-neuron counts. '
            '**VNC is briefly the largest category (but not a majority)** in three individual A25 bins: '
            'trial 3 at 50–100 ms (561/1,202 spikes, 46.67%), trial 9 at 200–250 ms '
            '(137/285, 48.07%), and trial 16 at 50–100 ms (215/487, 44.15%). '
            'Thus transient VNC plurality is observed, not sustained VNC-dominated late activity. '
            'This does not test VNC causality or exclude a VNC contribution.', '',
            '## Synaptic in-degree and the two proposed scaling rules', '',
            'In-degree here is **unsigned incoming synapse count**, `sum(Connectivity)` per postsynaptic '
            'neuron, not distinct-partner count or signed excitation minus inhibition. All-roster statistics '
            'include isolated and zero-input neurons. Female is the frozen v783 substrate; male is frozen '
            'whole CNS. For each MN9 we rank presynaptic partners by synapses **onto that MN9**, with numeric '
            'body ID breaking ties, then measure each selected partner’s **entire incoming** synapse count.', '',
            '| Population | Female n | Male n | Female mean / median | Male mean / median | Male/female mean ratio | Median ratio |',
            '|---|---:|---:|---:|---:|---:|---:|']
    f=full['female_density']; m=full['male_density']
    for label,fs,ms in [('All neurons',f['all'],m['all'])]+[(s+' MN9 partners (available up to 200)',f['neighborhoods'][s]['partner_indegree'],m['neighborhoods'][s]['partner_indegree']) for s in ('contra','ipsi')]:
        lines.append(f"| {label} | {fs['n']} | {ms['n']} | {fs['mean']:.3f} / {fs['median']:.1f} | {ms['mean']:.3f} / {ms['median']:.1f} | {ms['mean']/fs['mean']:.6f} | {ms['median']/fs['median']:.6f} |")
    lines+=['', '**Exact 200-per-MN9 specification cannot be met:** male R16949 has 137 partners total '
            '(male L has 278; female contra/ipsi have 227/241). Its displayed statistics use all 137, '
            'explicitly not 200. No zero padding or invented partners. Therefore the requested exact '
            '`r_mn9` remains undefined pending the owner’s decision.', '',
            '| MN9 relative side | Female incoming synapses | Male incoming synapses |', '|---|---:|---:|']
    for s in ('contra','ipsi'):
        lines.append(f"| {s} | {f['neighborhoods'][s]['incoming_synapses']:,} | {m['neighborhoods'][s]['incoming_synapses']:,} |")
    p=d['proposed_candidates']; alt=p['alternative_needs_owner_approval']
    lines+=['', f"Use of **means** (not medians) gives `r_all = {p['r_all']:.9f}`, hence "
            f"`0.275 / r_all = {p['all_w_syn_mV']:.9f} mV`.", '',
            'One possible definition for owner confirmation is **min(200, available) partners per MN9**, '
            'then the ratio of equally weighted side means: '
            '`(male_contra_mean + male_ipsi_mean) / (female_contra_mean + female_ipsi_mean)`. '
            'Shared partners count once in each neighborhood; this is not a pooled 337-versus-400 mean. '
            f"That alternative gives `{alt['ratio']:.9f}` and `{alt['w_syn_mV']:.9f} mV`. "
            'It has not been adopted or simulated. The mean-versus-median and bilateral aggregation choices '
            'are explicit design definitions to confirm, not values chosen after candidate gate outcomes.', '',
            'Changing `w_syn` also changes the existing external Poisson kick `w_syn * f_poi`; '
            '`f_poi` and that formula would remain unchanged. This is not a recurrent-edge-only rescaling. '
            'Source: [unchanged network builder](../sim/network.py).', '',
            '## Tastekin comparison', '',
            '[Tastekin Figure S17B, condition 1](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc1.pdf) '
            'shows LB3 activation at 200 Hz as an MN9 boxplot, n=30. No exact numerical mean or median '
            'is printed next to that condition; visual inspection places its median at approximately '
            '**105 Hz** (graph estimate, not an extracted numerical result). Our M1 means are '
            '**34.367 Hz R / 129.800 Hz L**. The caption does not identify the MN9 side or equate '
            'its LB3 pool with our one-sided typed17; this is not an established matched-condition replication.', '',
            'Supplement: 28-page publisher PDF, Figure S17 on PDF page 18, legend on page 27; '
            '16,121,775 bytes; SHA256 `099586a04f8ff0f02bf0fd9bcf8cedfa7531cffced664720e43d6800011d71a7`. '
            'Downloaded to ignored `data/malecns/downloads/Tastekin_Cell_2026_supplement_mmc1.pdf`. '
            'The [main paper](https://doi.org/10.1016/j.cell.2026.08.016) describes robust firing but '
            'does not provide an exact LB3-only rate in its modelling passage.', '',
            '## What the failure is', '',
            'The unscaled male model recruits a broad brain-and-VNC population after gustatory drive, '
            'but not the entire network: typically about 18,000 of 166,700 neurons fire, and late activity '
            'is predominantly in brain-class neurons. Sugar25 has a wide spread of network spike counts; '
            'its high-count trials have **lower**, not higher, mean MN9 rates than its low-count trials. '
            'All sugar200/bitter25 trials are high-count despite their variable L-MN9 response, and bitter25 '
            'alone can drive L even in the one low-count trial. The failure is therefore not merely rare '
            'network runaways inflating MN9 averages: network activity and MN9 selection/suppression are '
            'distinct outcomes under this design. Higher unsigned density and strongly asymmetric direct '
            'MN9 input are measured structural differences, not proven causes; saved spikes alone do not '
            'establish which feedback circuit or parameter caused the failed gates. Density rescaling '
            'remains a pre-declared test, not an already justified cure.', '',
            '## Verification', '',
            'All 480 trial counts/seeds, condition medians/ranges, window/bin totals, and 737 selected '
            'partner rows were cross-checked; incoming degrees were reconstructed independently using '
            'grouped sums. Onset and regional counts were independently rechecked from raw spikes for '
            'the 72 highlighted high-count trials. The [audit summary](../data/malecns/m1b_audit.json) '
            'references the full local bin ledger at `data/malecns/runs/m1b/audit.json`. '
            'Thirty male-only unit tests (including five diagnosis '
            'tests), 315 existing Python tests, 67 Node tests and release validation passed. '
            'These software checks do not change any M1 gate verdict.', '',
            '## Checkpoint', '',
            'The [pre-declared M1c stop rule](malecns_phase0.md#m1b--m1c-decision-boundary-declared-before-rescaled-runs) '
            'is recorded before any rescaled run. M1c has not started. Confirm the density definitions '
            '(especially the 137-partner exception) and candidates, or stop; no third weight will be tried.', '']
    return '\n'.join(lines)


if __name__=='__main__':
    print(generate())
