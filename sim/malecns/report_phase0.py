# SPDX-License-Identifier: MIT
"""Generate the research-only M1 report from saved results and female references."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.phase0 import conditions, evaluate_gates
from scripts.phase0_report import parse_rows


def female_reference():
    source = ROOT/'results/phase0/full/summary.csv'
    groups = parse_rows(pd.read_csv(source))
    r1 = pd.read_csv(ROOT/'results/refreeze/sugar_r1/readout_summary.csv')
    rows = []
    for cond in conditions():
        row = dict(cond)
        if cond['gate']!='AP':
            freq = cond['sugar_hz'] if cond['gate']=='A' else cond['bitter_hz']
            match = next(r for f,r in groups[cond['gate']] if f==freq)
            row['female_source_condition'] = str(match.cond_id)
            row['female_sugar_set'] = 'frozen23'
            # Female Shiu L is XLSX R/contralateral; female Shiu R is XLSX L/ipsilateral.
            for side, alias in [('R','left'),('L','right')]:
                row[f'{side}_mean'] = float(match[f'mn9_{alias}_mean_hz'])
                row[f'{side}_sd'] = float(match[f'mn9_{alias}_std_hz'])
            row['n_trials'] = int(match.n_trials)
        else:
            cid = 'R1_new_120' if cond['sugar_set']=='sugar' else 'R1_Aprime_LB3c20_120'
            row['female_source_condition'] = cid
            row['female_sugar_set'] = 'typed33' if cond['sugar_set']=='sugar' else 'LB3c20'
            for side, alias in [('R','MN9_L'),('L','MN9_R')]:
                match = r1[(r1.condition_id==cid)&(r1.readout==alias)].iloc[0]
                row[f'{side}_mean'], row[f'{side}_sd'] = float(match.rate_mean_hz), float(match.rate_std_hz)
                row['n_trials'] = int(match.n_trials)
        rows.append(row)
    return rows


def pm(row, side):
    return f'{row[side+"_mean"]:.3f} ± {row[side+"_sd"]:.3f}'


def verdict(value):
    return 'PASS' if value else 'FAIL'


def generate():
    result = json.loads((DATA/'phase0_results.json').read_text(encoding='utf-8'))
    meta, rows, gates = result['metadata'], result['conditions'], result['gates']
    if evaluate_gates(rows)!=gates:
        raise ValueError('Stored gate results disagree with saved conditions')
    female = female_reference()
    fg = evaluate_gates(female)
    fm = {r['id']:r for r in female}
    byid = {r['id']:r for r in rows}
    memory = meta['memory_plan']
    source_record = json.loads((DATA/'substrate_record.json').read_text(encoding='utf-8'))
    lines = ['# MaleCNS Phase 0 report — M1 full', '', '## Run metadata', '',
             '| Field | Value |','|---|---|',
             f'| Run date | {meta["started_utc"]} |', f'| Simulation commit | `{meta["git_commit"]}` |',
             f'| Brian2 / codegen | {meta["brian2_version"]} / {meta["codegen_target"]} |',
             f'| Workers | {memory["workers"]}, selected from available RAM |',
             '| Trials | A–D: 420; A′: 60; total 480; 30 per condition |',
             '| Seeds | 20260910–20260939, reused across all conditions |',
             f'| Parallel walltime | {meta["walltime_s"]:.1f} s |',
             f'| Maximum observed worker peak RSS | {meta["peak_worker_rss_gib"]:.3f} GiB |',
             f'| Substrate | {source_record["counts"]["neurons"]:,} neurons; {source_record["counts"]["edges"]:,} edges; {source_record["counts"]["synapses"]:,} synapses |',
             '', f'The plan measured WSL available RAM {memory["wsl_available_gib"]:.2f} GiB and host free RAM '
             f'{memory["host_free_gib"]:.2f} GiB. It reserved {memory["reserve_gib"]:.2f} GiB (25% of the smaller figure; '
             f'minimum 8 GiB), budgeted {memory["worker_budget_gib"]:.1f} GiB per worker (over 1.5× M0 peak), '
             f'and chose **{memory["workers"]} workers**, not the female run’s 14. Available WSL RAM was checked again '
             f'at launch ({meta["launch_available_gib"]:.2f} GiB). RSS is the Linux Python-worker lifetime high-water mark, '
             'not summed simultaneous RSS or a guarantee of future workloads.', '',
             'Sources: [plan](../data/malecns/phase0_plan.json), [frozen substrate](../data/malecns/substrate_record.json), '
             '[model protocol](../data/malecns/stim_protocol_malecns.json), [result/seed ledger](../data/malecns/phase0_results.json).',
             '', '## Provenance and side convention', '',
             'Both sides are recorded and gated separately in every condition. **R16949 is contralateral to XLSX-L '
             'sugar; L10331 is ipsilateral.** R remains the M0 reporting reference, not a settled primary choice; '
             'the owner deferred that decision until after M1. No readout was switched because it fired more.', '',
             'Female comparison columns use the same relative/XLSX-side convention: contralateral is Shiu’s historical '
             '`left` (720575940660219265), ipsilateral is historical `right` (720575940618238523). '
             'A–D values are the original [female Phase 0 report](phase0_report.md): frozen23 sugar, n=30, '
             '**before the refractory correction**, not a fresh female rerun. Male uses typed17 and the corrected '
             'shared implementation. Sets, layouts and substrate differ; these columns are not paired trials or a controlled sex comparison.', '',
             'The [adapter](../sim/malecns/adapter.py) calls the unchanged Shiu network builder and model parameters. '
             'M1 retains all 91 physical input slots from M0; inactive cells keep the ordinary refractory period. '
             'A′ zeros only the five LB3b input slots, preserving the twelve shared LB3c slots and random-stream layout. '
             'All results below are mean ± population SD, Hz, n=30 unless indicated.', '',
             '## Results', '',
             '| Gate; sugar/bitter Hz | Male contra R16949 | Male ipsi L10331 | Female contra (Shiu L) | Female ipsi (Shiu R) |',
             '|---|---:|---:|---:|---:|']
    for r in rows:
        if r['gate']=='AP':
            continue
        f = fm[r['id']]
        lines.append(f'| {r["gate"]}; {r["sugar_hz"]}/{r["bitter_hz"]} | {pm(r,"R")} | {pm(r,"L")} | {pm(f,"R")} | {pm(f,"L")} |')
    lines += ['', '## Hard gates', '',
              'The original [female gate predicates](../scripts/phase0_report.py) are applied independently to both sides; '
              'none is relaxed. Female ipsilateral verdicts below are recalculated from the original reported means/SDs '
              'using those same predicates, not an original frozen primary-readout decision.', '',
              '| Check | Male contra R | Male ipsi L | Female contra | Female ipsi |',
              '|---|---|---|---|---|']
    for key, label in [('A','A: sugar rises'),('B','B: bitter suppresses'),('C','C: bitter-alone limit'),
                       ('D','D: historical completeness'),('D_literal_zero','D: literal zero (additional)'),
                       ('C_literal_zero','C: literal zero (additional)'),('overall','Overall historical A–D')]:
        lines.append('| '+label+' | '+' | '.join(verdict(g[key]) for g in (gates['R'],gates['L'],fg['R'],fg['L']))+' |')
    lines += ['', 'A requires strictly rising successive sugar means (adjacent zeros allowed), and sugar200 > baseline '
              '+ 5×baseline SD + 5 Hz. B requires every successive bitter mean to be non-increasing and bitter200 '
              '< 0.5×bitter0. C requires each bitter-alone mean ≤ baseline + 2×baseline SD + 1 Hz. '
              '**Historical D checks a baseline condition with at least 30 trials, not zero firing**; therefore literal '
              'zero mean and SD are reported separately rather than silently changing that gate. All conditions here '
              'also require exactly 30 complete trials.', '', '## Soft indicators', '',
              '| Indicator | Male contra R | Male ipsi L | Female contra | Female ipsi |',
              '|---|---:|---:|---:|---:|']
    sugar_ratios, suppressions = [], []
    for lookup, side, gg in [(byid,'R',gates['R']),(byid,'L',gates['L']),(fm,'R',fg['R']),(fm,'L',fg['L'])]:
        denominator = lookup['A_s200_b0'][side+'_mean']
        sugar_ratios.append(f'{lookup["A_s100_b0"][side+"_mean"]/denominator:.3f}' if denominator else 'undefined')
        x = gg['bitter200_suppression_fraction']
        suppressions.append(f'{100*x:.2f}%' if x is not None else 'undefined')
    lines += ['| Sugar100 / sugar200 | '+' | '.join(sugar_ratios)+' |',
              '| Bitter200 suppression vs bitter0 | '+' | '.join(suppressions)+' |', '',
              'The original approximately-80%-of-maximum sugar comparison and ≥70% suppression reference remain '
              'soft indicators, not substitutes for monotonicity or the hard gates.', '', '## Appendix A′ — 120 Hz', '',
              'Male compares sugar17 (LB3b5 ∪ LB3c12, XLSX L) against LB3c12 alone, 30 fresh trials each. '
              'Female columns here switch explicitly to the [R1 typed-set comparison](salt_and_refreeze.md#adapted-a-prime-lb3c-only-l-subset-20-cells): '
              'sugar33 versus LB3c20, n=30, same 120 Hz level. This is the class-matched reference, not frozen23 '
              'and not the original 21-versus-23 A′, which did not test 120 Hz.', '',
              '| Set / comparison | Male contra R | Male ipsi L | Female contra (Shiu L) | Female ipsi (Shiu R) |',
              '|---|---:|---:|---:|---:|']
    for cid,label in [('AP_sugar_120','Typed sugar: male17 / female33'),('AP_sugar_lb3c_120','LB3c-only: male12 / female20')]:
        r,f = byid[cid],fm[cid]
        lines.append(f'| {label} | {pm(r,"R")} | {pm(r,"L")} | {pm(f,"R")} | {pm(f,"L")} |')
    trials = pd.read_csv(ROOT/'results/refreeze/sugar_r1/group_trials.csv')
    diffs = []
    for alias in ['MN9_L','MN9_R']:
        a = trials[(trials.condition_id=='R1_new_120')&(trials.readout==alias)].sort_values('trial')
        b = trials[(trials.condition_id=='R1_Aprime_LB3c20_120')&(trials.readout==alias)].sort_values('trial')
        if len(a)!=30 or len(b)!=30 or a.seed.tolist()!=b.seed.tolist():
            raise ValueError('Female A-prime pairing missing')
        d = b.rate_hz.to_numpy()-a.rate_hz.to_numpy()
        diffs.append(f'{np.mean(d):+.3f} ± {np.std(d,ddof=0):.3f}')
    male_d = [f'{result["a_prime"][s]["mean_hz"]:+.3f} ± {result["a_prime"][s]["sd_hz"]:.3f}' for s in ['R','L']]
    lines += ['| Paired subset-minus-union difference | '+' | '.join(male_d+diffs)+' |', '',
              'Differences are trial-wise paired differences, not differences of independent SDs. The historical '
              'female 21-versus-23 mean difference was <0.5 Hz for its primary MN9 across 25/50/100/200 Hz; '
              'it is not the same experiment as either typed-set A′.', '', '## Laterality and decision boundary', '',
              f'At sugar200, male contra/ipsi means are {byid["A_s200_b0"]["R_mean"]:.3f}/'
              f'{byid["A_s200_b0"]["L_mean"]:.3f} Hz; the female frozen23 reference is '
              f'{fm["A_s200_b0"]["R_mean"]:.3f}/{fm["A_s200_b0"]["L_mean"]:.3f} Hz. '
              'The direction of the dominant response is compared under the same side convention; possible causes '
              'are Root_Side convention, reconstruction or a real difference, unresolved. '
              '[OQ-11](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).', '',
              'The primary male readout remains deferred to the owner. M1 is inside Shiu’s model and is not calibrated '
              'against behaviour. No female rerun, parameter tuning, product changes or M2 replication was performed.', '',
              '## Equivalence and verification', '',
              'The M1 audit checks saved full-network and Poisson events, all condition/trial/seed counts, rates, latencies, '
              'summary statistics and bilateral gate decisions. The first five A200/B0 and baseline trials are compared '
              'against the existing M0 recordings, not simulated again as an extra equivalence experiment. '
              'M0 overlaps the M1 seeds and is not pooled as n=35. A200 and B0 intentionally share identical '
              'drives/layout/seeds; their duplicate observations are not n=60.', '',
              'Verification passed for 480 raw trials / 960 MN9-neuron trials, 1,395 M0 neuron-train comparisons, '
              '2,910 shared Poisson-train comparisons and 30 identical A200/B0 whole-network pairs. '
              '[Audit record](../data/malecns/phase0_audit.json). Software checks: 25 male-only tests, '
              '315 existing Python tests, 67 Node tests and release validation passed; this does not turn '
              'failed scientific gates into passes.', '',
              'Brian2 emitted a `rates` namespace-name warning and explicitly used its internal Poisson rates variable. '
              'No warning was suppressed or source edited during the run; recorded input events are checked by the audit.', '',
              '## Backend cross-check', '', 'No male PyTorch/CUDA cross-check was authorised or run; Brian2 is the simulation backend.', '',
              '## Files', '',
              '- [Male result and provenance ledger](../data/malecns/phase0_results.json)',
              '- [Frozen M0 substrate](../data/malecns/substrate_record.json)',
              '- [M1 plan](../data/malecns/phase0_plan.json)',
              '- [Runner](../sim/malecns/phase0.py)',
              '- [Report generator](../sim/malecns/report_phase0.py)',
              '- Raw, gitignored spikes and input events: `data/malecns/runs/m1/`.',
              '- Female A–D source: `results/phase0/full/summary.csv`.',
              '- [Frozen female comparison values and source hashes](../data/malecns/phase0_female_reference.json).',
              '- Female typed A′ sources: `results/refreeze/sugar_r1/readout_summary.csv` and `group_trials.csv`.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    target = ROOT/'docs/malecns_phase0.md'
    if target.exists():
        raise FileExistsError('Report already exists; do not overwrite a checkpoint')
    reference = {'side_mapping':'Female Shiu left = contralateral/XLSX R; Shiu right = ipsilateral/XLSX L.',
                 'rows':female_reference(), 'sources':[file_record(ROOT/p) for p in
                 ['results/phase0/full/summary.csv','results/refreeze/sugar_r1/readout_summary.csv',
                  'results/refreeze/sugar_r1/group_trials.csv','docs/phase0_report.md','docs/salt_and_refreeze.md']]}
    write_json(DATA/'phase0_female_reference.json',reference)
    target.write_text(generate(),encoding='utf-8',newline='\n')
    print(f'wrote {target}')
