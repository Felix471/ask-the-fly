# SPDX-License-Identifier: MIT
"""Male-v1 Phase 2: 400 canonical cells x 30 trials; no retry or resume."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from sim.grid import expand_grid_conditions, load_grid_levels
from sim.malecns import male_v1_adapter as adapter
from sim.malecns import male_v1_phase1 as phase1
from sim.malecns.male_v1_phase1 import event_readouts, init_worker
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

OUT = DATA / 'runs/male_v1/grid'
RESULT = DATA / 'male_v1_grid_results.json'
PLAN = DATA / 'male_v1_grid_plan.json'
SEED_RULE = ("20260910 + 1000 * (cell_index % 40) + trial, trial 0..29, cell_index in the "
             "female grid's cell order")

# Pre-declared verbatim in docs/male_fly_v2.md; implemented separately in A2.
COMPARISON_RULES = [('R1',
  'Dish set: the 174 dishes of data/dishes.json (sha256 recorded in the comparison file), each mapped '
  'to its canonical grid cell with sim.grid.resolve_levels; water medium maps to the 60 Hz cell as in '
  'the female table.'),
 ('R2',
  'Scores and states: the female score is mn9_left_mean of data/lookup_table_v1_2.json (equal to the '
  "site's mn9_mean) and the female state is that table's state field; the male score is the 30-trial "
  'mean L10331 rate rounded to 3 decimals as stored in data/lookup_table_male.json, and the male state '
  'follows the frozen male state rule (L10331 mean and the three-cell MN11D mean at the 5.0 Hz '
  'threshold, applied to unrounded means).'),
 ('R3',
  'Distributions: counts of the four states over the 174 dishes and over the 400 cells for each fly; '
  'the number of dishes with score below 5.0 Hz for each fly; the 4x4 cross-table of female state by '
  'male state over the dishes.'),
 ('R4',
  "Pairwise outcome: for every unordered pair of distinct dishes (15,051 pairs) each fly's outcome is "
  'the first dish, the second dish, or tie, with tie when the absolute score difference is below 1e-9 '
  '(the site rule) and otherwise the higher score winning. The flies agree on a pair when their '
  'outcomes are equal. Agreement rate = agreeing pairs / 15,051. Also reported: the 3x3 cross-table of '
  'female outcome by male outcome, the agreement rate over pairs where neither fly ties, and the number '
  'of pairs where both flies tie.'),
 ('R5',
  'Pair-level attribution: for a disagreeing pair, the male outcome is recomputed from the male table '
  'with the water level of both dishes set to none and every other level unchanged; if that outcome '
  'equals the female outcome the disagreement is removed by water. Likewise with ir94e set to none, and '
  'with both set to none. Reported: disagreements removed by water alone, by ir94e alone, by either, '
  'only by both together, and by neither. The female table is never modified.'),
 ('R6',
  'Dish-level attribution: for dish d, lower(d) is the number of other dishes x for which the female '
  'outcome of the pair is d and the male outcome is not d. lower_water(d) and lower_ir94e(d) are the '
  'same counts with the male outcome recomputed as in R5. Reported: the number of dishes with lower(d) '
  '> 0; the number with lower_water(d) < lower(d) (partly due to water) and with lower_water(d) = 0 < '
  'lower(d) (fully due to water); the same two counts for ir94e; the sums of lower, lower_water and '
  'lower_ir94e over all dishes; and a per-dish table of all 174 dishes with levels, female score, rank '
  'and state, male score, rank and state, lower, lower_water and lower_ir94e. Rank is 1 plus the number '
  'of dishes with a strictly higher score within the same fly.'),
 ('R7',
  'Sign of each channel over dishes: for every dish whose water level is not none, the sign of (score '
  'of the dish) minus (score of the same dish with water set to none), for each fly, counted as lower, '
  'equal or higher; the same for ir94e. Counterfactual cells always exist because the grid is '
  'complete.'),
 ('R8',
  "Replay rule: the whole-network replay of a cell is trial 0 of that cell's 30 grid trials (seed "
  '20260910 + 1000 * (global_index % 40)); no extra trial is simulated. The packed site replay records '
  "the same body ids and times, and its MN9 spike counts equal trial 0's rates.")]
REPLAY_RULE = 'R8 ' + COMPARISON_RULES[-1][1]


def seeds_for(global_index):
    return [20260910 + 1000 * (global_index % 40) + trial for trial in range(30)]


def conditions(p):
    """Validate the frozen coordinates and return cells in female seed order."""
    levels = load_grid_levels()
    expected_grid = dict(levels=levels['levels'], n_unique_cells=400,
                         grid_levels_record=file_record(ROOT / 'data/grid_levels.json'),
                         seed_rule=SEED_RULE)
    for key, value in expected_grid.items():
        if p['grid'].get(key) != value:
            raise ValueError('Frozen grid differs: ' + key)
    expanded = expand_grid_conditions(levels)
    female = adapter.read(ROOT / 'data/lookup_table_v1_2.json')['cells']
    if len(expanded) != 400 or [c['rates'] for c in expanded] != [c['hz'] for c in female]:
        raise ValueError('Grid inventory or female Hz order differs')
    return [dict(cond_id=c['cond_id'], global_index=c['global_index'], levels=c['levels'],
                 alias_levels=c['alias_levels'], hz=c['rates'], n_trials=30,
                 **{ch + '_hz': c['rates'][ch] for ch in adapter.CHANNELS}) for c in expanded]


def check():
    p, _, slots = adapter.load_configuration()
    cs = conditions(p)
    return dict(stage='male-v1 Phase 2 grid', declaration_commit=adapter.FREEZE,
                poisson_units=len(slots), channel_order=list(adapter.CHANNELS),
                conditions=cs, seeds=[seeds_for(c['global_index']) for c in cs],
                seed_rule=SEED_RULE, total_trials=12000, duration_ms=p['trial']['duration_ms'],
                dt_ms=p['model']['dt_ms'], w_syn_mV=p['model']['w_syn_mV'], readouts=p['readout'],
                execution='No retry/resume. No trials in --check or --plan.')


def grid_source_records():
    p = adapter.read(adapter.PROTOCOL)
    paths = ['sim/network.py', 'sim/malecns/phase0.py', 'sim/malecns/substrate.py',
             'sim/malecns/male_v1_adapter.py', 'sim/malecns/male_v1_phase1.py',
             'sim/malecns/male_v1_grid.py', 'sim/grid.py', 'data/grid_levels.json',
             'data/lookup_table_v1_2.json', 'data/dishes.json',
             'data/malecns/male_v1_phase1_results.json', 'data/malecns/male_v1_phase1_audit.json',
             # The adapter's memory plan reads this reference even when Phase 1 is larger.
             'data/malecns/m1j_male_results.json',
             p['connectivity_file'], p['completeness_file'], p['substrate_record']['path']]
    return [file_record(ROOT / path) for path in paths] + [file_record(adapter.PROTOCOL), file_record(adapter.CELLS)]


def memory_plan(host_free_kib):
    memory = adapter.memory_plan(host_free_kib)
    phase1_peak = adapter.read(phase1.RESULT)['metadata']['peak_worker_rss_gib']
    if phase1_peak > memory['reference_peak_gib']:
        source = 'data/malecns/male_v1_phase1_results.json metadata.peak_worker_rss_gib'
        memory = adapter.phase0.choose_workers(memory['wsl_available_gib'], memory['host_free_gib'],
                                               phase1_peak, memory['cpus'])
        memory['reference_peak_gib'] = memory.pop('measured_m0_peak_gib')
        memory['peak_source'] = source
        memory['rule'] = memory['rule'].replace('M0 peak', 'reference peak')
    memory['peak_selection'] = 'Larger of M1j and male-v1 Phase 1 peak_worker_rss_gib (M1j on equality)'
    return memory


def make_plan(host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--plan requires WSL flybrain')
    if PLAN.exists():
        raise FileExistsError(PLAN)
    plan = check()
    sources = grid_source_records()
    plan['memory'] = memory_plan(host_free_kib)
    model, _, _, _ = adapter.build()
    for record in sources:
        adapter.check_file(record)
    plan.update(sources=sources, planned_utc=datetime.now(timezone.utc).isoformat(),
                compile_only=dict(network_builds=1, elapsed_simulated_seconds=0, spikes=len(model.monitor.i)),
                brian2_version=__import__('brian2').__version__,
                comparison_rules=[f'{rid} {text}' for rid, text in COMPARISON_RULES],
                replay_rule=REPLAY_RULE)
    write_json(PLAN, plan)
    return plan


def check_plan(host_free_kib):
    plan = adapter.read(PLAN)
    if plan['sources'] != grid_source_records():
        raise ValueError('Planned sources changed')
    expected = dict(check(), compile_only=dict(network_builds=1, elapsed_simulated_seconds=0, spikes=0),
                    brian2_version=__import__('brian2').__version__,
                    comparison_rules=[f'{rid} {text}' for rid, text in COMPARISON_RULES],
                    replay_rule=REPLAY_RULE)
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ValueError('Plan changed: ' + key)
    return plan, memory_plan(host_free_kib)


def run_condition(condition):
    """Use the unchanged Phase 1 worker, with this cell's grid seeds and ledger."""
    import resource
    from brian2 import ms, second, seed

    directory = OUT / condition['cond_id']
    directory.mkdir()
    model = phase1._MODEL
    rows = []
    for trial, trial_seed in enumerate(seeds_for(condition['global_index'])):
        started = time.perf_counter()
        model.net.restore('init')
        model.set_rates({ch: condition[ch + '_hz'] for ch in adapter.CHANNELS})
        seed(trial_seed)
        model.net.run(phase1._P['trial']['duration_ms'] * ms)
        body = phase1._BODY[np.asarray(model.monitor.i[:], dtype='int32')]
        times = np.asarray(model.monitor.t[:] / second, dtype=float)
        elapsed = time.perf_counter() - started
        archive = directory / f'trial_{trial:02d}.npz'
        with archive.open('xb') as stream:
            np.savez_compressed(stream, body_id=body, time_s=times,
                                poisson_index=np.asarray(phase1._MONITOR.i[:], dtype='int32'),
                                poisson_time_s=np.asarray(phase1._MONITOR.t[:] / second, dtype=float))
        row = dict(condition=condition['cond_id'], global_index=condition['global_index'],
                   trial=trial, seed=trial_seed, trial_wall_s=elapsed,
                   worker_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   spikes=file_record(archive), **event_readouts(body, times, phase1._P, phase1._SLOTS))
        write_json(archive.with_suffix('.json'), row)
        rows.append(row)
    ledger = dict(condition=condition, rows=rows, pid=os.getpid())
    write_json(directory / 'condition_ledger.json', ledger)
    return ledger


def summarize(results, p):
    """Reject noncanonical ledgers before computing Phase 1 readout statistics."""
    expected = conditions(p)
    if len(results) != 400 or [g['condition'] for g in results] != expected:
        raise ValueError('Incorrect cell inventory or order')
    readout_keys = [key for key in event_readouts(np.array([], dtype='int64'), np.array([]), p, [])
                    if key.endswith('_hz')]
    summary = []
    for condition, group in zip(expected, results):
        rows = group['rows']
        identities = [(r['condition'], r['global_index'], r['trial'], r['seed']) for r in rows]
        required = [(condition['cond_id'], condition['global_index'], t, seed)
                    for t, seed in enumerate(seeds_for(condition['global_index']))]
        if identities != required:
            raise ValueError('Incorrect cell/trial/seed ledger')
        if any({k for k in r if k.endswith('_hz')} != set(readout_keys) for r in rows):
            raise ValueError('Incorrect readout inventory')
        summary_row = dict(condition)
        for key in readout_keys:
            prefix = key[:-3]
            values = np.asarray([r[key] for r in rows], dtype=float)
            latencies = [r[prefix + '_latency_ms'] for r in rows if r[prefix + '_latency_ms'] is not None]
            summary_row[prefix + '_mean'] = float(values.mean())
            summary_row[prefix + '_sd'] = float(values.std(ddof=0))
            summary_row[prefix + '_firing_trials'] = int(np.count_nonzero(values > 0))
            summary_row[prefix + '_latency_median_ms'] = float(np.median(latencies)) if latencies else None
        for key in ('whole_network_spikes', 'neurons_fired'):
            values = [r[key] for r in rows]
            summary_row.update({key + '_median': float(np.median(values)),
                                key + '_min': min(values), key + '_max': max(values)})
        summary.append(summary_row)
    return dict(cells=summary)


def run(host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--run requires WSL flybrain')
    if OUT.exists() or RESULT.exists():
        raise FileExistsError('Phase 2 outputs exist; no retry, resume or overwrite')
    plan, memory = check_plan(host_free_kib)
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    metadata = dict(stage='male-v1 Phase 2 grid', started_utc=datetime.now(timezone.utc).isoformat(),
                    sources=plan['sources'], plan=file_record(PLAN), memory=memory,
                    python=sys.version, brian2=__import__('brian2').__version__, codegen='cython')
    write_json(OUT / 'run_meta_start.json', metadata)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'),
                             initializer=init_worker) as pool:
        futures = [pool.submit(run_condition, c) for c in plan['conditions']]
        for future in as_completed(futures):
            results.append(future.result())
            print(f'Completed {len(results)}/400 cells', flush=True)
    for record in plan['sources'] + [metadata['plan']]:
        adapter.check_file(record)
    results.sort(key=lambda group: group['condition']['global_index'])
    compact = summarize(results, adapter.read(adapter.PROTOCOL))
    metadata.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter() - started,
                    total_trials=12000,
                    peak_worker_rss_gib=max(r['worker_peak_rss_kib'] for g in results for r in g['rows']) / 1024**2)
    compact['metadata'] = metadata
    write_json(OUT / 'full_results.json', dict(compact, raw=results))
    compact['raw_ledger'] = file_record(OUT / 'full_results.json')
    write_json(RESULT, compact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('check', 'plan', 'run'):
        modes.add_argument('--' + name, action='store_true')
    parser.add_argument('--host-free-kib', type=int)
    args = parser.parse_args()
    if not args.check and (args.host_free_kib is None or args.host_free_kib <= 0):
        parser.error('--plan and --run require positive --host-free-kib measured on Windows')
    if args.check:
        print(json.dumps(check(), indent=2))
    elif args.plan:
        print(json.dumps(make_plan(args.host_free_kib), indent=2))
    else:
        run(args.host_free_kib)


if __name__ == '__main__':
    main()
