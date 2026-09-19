# SPDX-License-Identifier: MIT
"""Independent audit of grid events and every Phase 2 output; no Brian2."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from scripts.mn_readouts_from_replays import neuron_metrics, aggregate_metrics, validate_spikes, read_replay_header
from scripts.run_replay import FLAG_BITS
from sim.grid import EXPECTED_DIMENSIONS as DIMS, expand_grid_conditions, load_grid_levels, resolve_levels
from sim.malecns import male_v1_adapter as adapter, male_v1_grid as grid
from sim.malecns.audit_male_v1_phase1 import equal, require, independent_summary as phase1_summary
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

AUDIT = DATA / 'male_v1_grid_audit.json'
LOOKUP = ROOT / 'data/lookup_table_male.json'
COMPARISON = DATA / 'male_female_comparison.json'
INDEX = ROOT / 'data/replay_neurons_male.json'
REPLAYS = ROOT / 'data/replay_male'
STATES = ('eats', 'mouth_moves', 'proboscis_only', 'no_response')


def cells_digest(cells):
    return hashlib.sha256(json.dumps(cells, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode('utf-8')).hexdigest()


def audit_trial(path, condition, trial, p, cells, slots, roster=None):
    row = adapter.read(path)
    seed = 20260910+1000*(condition['global_index'] % 40)+trial
    identity = dict(condition=condition['cond_id'], global_index=condition['global_index'], trial=trial, seed=seed)
    for key, value in identity.items():
        equal(row[key], value, 'Trial '+key)
    equal(row['spikes'], file_record(path.with_suffix('.npz')), 'Trial archive hash/path')
    require(np.isfinite(row['trial_wall_s']) and row['trial_wall_s'] >= 0, 'Trial wall time')
    require(np.isfinite(row['worker_peak_rss_kib']) and row['worker_peak_rss_kib'] > 0, 'Trial RSS')
    duration, dt = p['trial']['duration_ms']/1000, p['model']['dt_ms']/1000
    with np.load(path.with_suffix('.npz'), allow_pickle=False) as z:
        equal(set(z.files), {'body_id', 'time_s', 'poisson_index', 'poisson_time_s'}, 'NPZ inventory')
        body, ts, pi, pt = [z[k] for k in ('body_id', 'time_s', 'poisson_index', 'poisson_time_s')]
    validate_spikes(body, ts, duration)
    validate_spikes(pi, pt, duration)
    require((np.diff(ts) >= 0).all() and (np.diff(pt) >= 0).all(), 'Unsorted events')
    require((body > 0).all() and (pi < len(slots)).all(), 'Event IDs outside layout')
    if roster is not None:
        require(set(body) <= roster, 'Unknown network body')
    rates = [condition[d+'_hz'] for d in DIMS for _ in cells['sets'][d]['ids']]
    ticks, expected_pi = np.nonzero(np.random.RandomState(seed).random_sample(
        (round(duration/dt), len(slots))) < np.asarray(rates)*dt)
    np.testing.assert_array_equal(pi, expected_pi, err_msg='Declared Poisson indices')
    np.testing.assert_array_equal(pt, ticks*dt, err_msg='Declared Poisson times')
    groups = dict(L=[p['readout']['primary']], R=[p['readout']['secondary']], **p['readout']['extra_readouts'])
    ids = list(dict.fromkeys(slots+[b for members in groups.values() for b in members]))
    metrics = neuron_metrics(body, ts*1000, ids, duration*1000)
    rebuilt = dict(whole_network_spikes=len(body), neurons_fired=len(set(body)),
                   source_spike_counts=[metrics[str(b)]['spike_count'] for b in slots])
    for name, members in groups.items():
        for b in members:
            prefix = name if name in ('L', 'R') else f'{name}_{b}'
            rebuilt[prefix+'_hz'] = metrics[str(b)]['rate_hz']
            rebuilt[prefix+'_latency_ms'] = metrics[str(b)]['first_spike_ms']
        if name not in ('L', 'R'):
            metric = aggregate_metrics([metrics[str(b)] for b in members])
            rebuilt[name+'_hz'] = metric['rate_hz']
            rebuilt[name+'_latency_ms'] = metric['first_spike_ms']
    equal(set(row), set(rebuilt) | set(identity) | {'trial_wall_s', 'worker_peak_rss_kib', 'spikes'}, 'Trial field inventory')
    for key, value in rebuilt.items():
        equal(row[key], value, str(path)+': '+key)
    return dict(row, **rebuilt)


def independent_summary(groups, p):
    # Reuse the Phase 1 independent statistics, projecting only its summary rows.
    projected = [dict(condition=dict(g['condition'], id=g['condition']['cond_id']), rows=g['rows']) for g in groups]
    rows = phase1_summary(projected, p)['conditions']
    for row in rows:
        del row['id']
    return dict(cells=rows)


def audit_lookup_cells(table, groups, female):
    equal(len(table['cells']), len(groups), 'Lookup cell count')
    equal(len(female['cells']), len(groups), 'Female cell count')
    rebuilt = []
    for group, old, actual in zip(groups, female['cells'], table['cells']):
        c, trials = group['condition'], group['rows']
        equal(c['levels'], {d: old[d] for d in DIMS}, 'Lookup canonical levels')
        equal(c['hz'], old['hz'], 'Lookup canonical Hz')
        equal(len(trials), 30, 'Lookup n=30')
        result = {d: c['levels'][d] for d in DIMS}
        result['hz'] = c['hz']
        means = {}
        for source, destinations in [('L', ('mn9', 'mn9_left')), ('R', ('mn9_right', 'mn9_r')),
                                      ('mn11d', ('mn11d',)), ('mn11v', ('mn11v',)), ('cem', ('cem',))]:
            values = np.asarray([r[source+'_hz'] for r in trials])
            means[source] = float(np.mean(values))
            for target in destinations:
                result[target+'_mean'] = round(means[source], 3)
                result[target+('_std' if target in ('mn9', 'mn9_left', 'mn9_right') else '_sd')] = round(float(np.std(values, ddof=0)), 3)
        result['n_trials'] = 30
        active9, active11 = means['L'] >= 5, means['mn11d'] >= 5
        result['state'] = ('eats' if active11 else 'proboscis_only') if active9 else ('mouth_moves' if active11 else 'no_response')
        equal((active9, active11), (result['mn9_mean'] >= 5, result['mn11d_mean'] >= 5), 'State rounding')
        order = list(old)[:-1]+['cem_mean', 'cem_sd', 'state']
        equal(list(actual), order, 'Lookup field order')
        expected = {key: result[key] for key in order}
        equal(actual, expected, 'Lookup values '+c['cond_id'])
        rebuilt.append(expected)
    equal(table['cells_sha256'], cells_digest(rebuilt), 'Lookup cells hash')
    return rebuilt


def audit_lookup_header(table, p, cells, female, result_path, metadata, female_path):
    substrate = adapter.read(ROOT / p['substrate_record']['path'])
    retained = [r['synapses_per_edge'] for r in substrate['synapses_per_edge_histogram']
                if r['threshold_action'] == 'kept before autapse removal']
    expected = dict(schema_version='lookup_male_v1', fly='male',
                    protocol=file_record(adapter.PROTOCOL), source_cells=file_record(adapter.CELLS),
                    grid_levels_sha256=file_record(ROOT / 'data/grid_levels.json')['sha256'], data_version=p['data_version'],
                    substrate=dict(neurons=substrate['counts']['neurons'], edges=substrate['counts']['edges'],
                                   synapses=substrate['counts']['synapses'], min_synapses=min(retained),
                                   autapses_removed=substrate['counts']['autapses_removed']),
                    model=f"Shiu 2024 LIF on MaleCNS v1.0, w_syn 0.17875 mV, Brian2 {metadata['brian2']} cython, store/restore path",
                    readout=dict(neuron='MN9', aggregation='primary_only', primary=10331, primary_side='XLSX L',
                                 secondary=16949, secondary_side='XLSX R', unit='Hz (spikes per 1000 ms trial)'),
                    n_trials_per_cell=30, **{k: female[k] for k in ('dimensions', 'levels', 'level_notes')},
                    state_rule=p['state_rule'], readouts_recorded=[r for g in cells['readouts'].values() for r in g['source_rows']],
                    extra_statistics=dict(std_ddof=0, decimal_places=3,
                        mn11d='Mean and population SD over 30 per-trial three-cell mean rates',
                        mn11v='Mean and population SD over 30 per-trial two-cell mean rates',
                        cem='Mean and population SD over 30 per-trial six-cell mean rates',
                        mn9_r='Mean and population SD of the secondary R16949 rate; aliases of mn9_right_*.',
                        state='Threshold applied to unrounded 30-trial means; rounding does not change any state'),
                    female_reference=file_record(female_path), results=file_record(result_path),
                    product_commitments=p['product_commitments'],
                    field_note='mn9_mean and mn9_left_* are the primary L10331 (XLSX L); '
                               'mn9_right_* and mn9_r_* are the secondary R16949 (XLSX R); the secondary does not decide')
    equal(table['grid_levels_sha256'], female['grid_levels_sha256'], 'Female grid hash')
    equal(set(table), set(expected) | {'generated_at', 'git_commit', 'cells_sha256', 'cells'}, 'Lookup header inventory')
    for key, value in expected.items():
        equal(table[key], value, 'Lookup header '+key)
    require(datetime.fromisoformat(table['generated_at']).utcoffset() is not None, 'Lookup timestamp needs timezone')
    require(len(table['git_commit']) == 40 and all(c in '0123456789abcdef' for c in table['git_commit']), 'Lookup git commit')
    equal(list(table)[-1], 'cells', 'Header before cells')


def independent_comparison(female, male, dishes):
    """Straightforward loops, independent of the comparison module and its helpers."""
    def sign(a, b):
        return 0 if abs(a-b) < 1e-9 else 1 if a > b else -1

    def selected(table, dish, remove=()):
        levels = resolve_levels(table, {d: 'none' if d in remove else dish[d] for d in DIMS})
        matches = [r for r in table['cells'] if all(r[d] == levels[d] for d in DIMS)]
        equal(len(matches), 1, 'Comparison canonical cell')
        return matches[0]

    n = len(dishes)
    rows = {fly: [selected(table, d) for d in dishes] for fly, table in [('female', female), ('male', male)]}
    scores = {fly: [r['mn9_left_mean'] for r in rs] for fly, rs in rows.items()}
    cf = {fly: {key: [selected(table, d, channels)['mn9_left_mean'] for d in dishes]
                for key, channels in [('water', ('water',)), ('ir94e', ('ir94e',)), ('both', ('water', 'ir94e'))]}
          for fly, table in [('female', female), ('male', male)]}
    distributions = {}
    for fly, table in [('female', female), ('male', male)]:
        distributions[fly] = {}
        for name, rs in [('dishes', rows[fly]), ('cells', table['cells'])]:
            counts = dict.fromkeys(STATES, 0)
            for row in rs:
                counts[row['state']] += 1
            distributions[fly][name] = counts
    distributions['below_5hz_dishes'] = {fly: sum(s < 5 for s in scores[fly]) for fly in rows}
    distributions['cross_table'] = {s: dict.fromkeys(STATES, 0) for s in STATES}
    for d in range(n):
        distributions['cross_table'][rows['female'][d]['state']][rows['male'][d]['state']] += 1
    labels = {1: 'first', -1: 'second', 0: 'tie'}
    cross = {s: dict.fromkeys(labels.values(), 0) for s in labels.values()}
    attribution = dict.fromkeys(('disagreeing_pairs', 'removed_by_water', 'removed_by_ir94e',
                                 'removed_by_either', 'removed_only_by_both', 'removed_by_neither'), 0)
    lower = [[0, 0, 0] for _ in dishes]
    for a in range(n):
        for b in range(a+1, n):
            f = sign(scores['female'][a], scores['female'][b])
            m = sign(scores['male'][a], scores['male'][b])
            alternatives = {ch: sign(cf['male'][ch][a], cf['male'][ch][b]) for ch in ('water', 'ir94e', 'both')}
            cross[labels[f]][labels[m]] += 1
            if f != m:
                attribution['disagreeing_pairs'] += 1
                water, ir94e, both = [alternatives[ch] == f for ch in ('water', 'ir94e', 'both')]
                for name, yes in [('water', water), ('ir94e', ir94e), ('either', water or ir94e),
                                   ('neither', not water and not ir94e)]:
                    if yes:
                        attribution['removed_by_'+name] += 1
                if both and not water and not ir94e:
                    attribution['removed_only_by_both'] += 1
            if f:
                winner = a if f == 1 else b
                for k, counter in enumerate((m, alternatives['water'], alternatives['ir94e'])):
                    if counter != f:
                        lower[winner][k] += 1
    count = n*(n-1)//2
    agreeing = sum(cross[s][s] for s in labels.values())
    strict = sum(cross[s][t] for s in ('first', 'second') for t in ('first', 'second'))
    pairwise = dict(agreement_rate=agreeing/count if count else None, agreeing_pairs=agreeing, cross_table=cross,
                    strict_pairs=strict, strict_agreement_rate=(cross['first']['first']+cross['second']['second'])/strict if strict else None,
                    both_tie_pairs=cross['tie']['tie'])
    per_dish = []
    for d, dish in enumerate(dishes):
        row = dict(key=dish['key'], en=dish['display']['en'], zh=dish['display']['zh'], **{dim: dish[dim] for dim in DIMS})
        for fly in ('female', 'male'):
            row[fly+'_score'] = scores[fly][d]
            row[fly+'_rank'] = 1+sum(s > scores[fly][d] for s in scores[fly])
            row[fly+'_state'] = rows[fly][d]['state']
        row.update(zip(('lower', 'lower_water', 'lower_ir94e'), lower[d]))
        per_dish.append(row)
    totals = dict(dishes_lower=sum(r[0] > 0 for r in lower))
    for index, ch in [(1, 'water'), (2, 'ir94e')]:
        totals['dishes_partly_'+ch] = sum(r[index] < r[0] for r in lower)
        totals['dishes_fully_'+ch] = sum(r[index] == 0 and r[0] > 0 for r in lower)
    for index, key in enumerate(('lower', 'lower_water', 'lower_ir94e')):
        totals['sum_'+key] = sum(r[index] for r in lower)
    channel_sign = {}
    for ch in ('water', 'ir94e'):
        channel_sign[ch] = {}
        for fly in ('female', 'male'):
            counts = dict(lower=0, equal=0, higher=0, n_dishes=0)
            for d, dish in enumerate(dishes):
                if dish[ch] != 'none':
                    counts['n_dishes'] += 1
                    counts[{-1: 'lower', 0: 'equal', 1: 'higher'}[sign(scores[fly][d], cf[fly][ch][d])]] += 1
            channel_sign[ch][fly] = counts
    return dict(rules=[f'{rid} {text}' for rid, text in grid.COMPARISON_RULES],
                inputs=dict(female_cells_sha256=cells_digest(female['cells']), male_cells_sha256=cells_digest(male['cells'])),
                n_dishes=n, n_pairs=count,
                n_distinct_female_cells=len({tuple(r[d] for d in DIMS) for r in rows['female']}),
                n_distinct_male_cells=len({tuple(r[d] for d in DIMS) for r in rows['male']}),
                distributions=distributions, pairwise=pairwise, attribution_pairs=attribution,
                attribution_dishes=totals, channel_sign=channel_sign, dishes=per_dish)


def audit_comparison(actual, female, male, dishes, records=None):
    expected = independent_comparison(female, male, dishes)
    if records:
        expected['inputs'].update(records)
    equal(actual, expected, 'Every comparison field')
    return expected


def audit_memory(memory, m1j_peak, phase1_peak):
    """Reconstruct planned/run budgets from recorded measurements, not current RAM."""
    peak = max(m1j_peak, phase1_peak)
    available = min(memory['wsl_available_gib'], memory['host_free_gib'])
    reserve = max(8., available*.25)
    budget = math.ceil(peak*1.5*10)/10
    workers = min(16, max(1, memory['cpus']//2), math.floor((available-reserve)/budget))
    require(workers >= 1, 'Memory budget cannot launch a worker')
    name = 'male_v1_phase1' if phase1_peak > m1j_peak else 'm1j_male'
    expected = dict(workers=workers, wsl_available_gib=memory['wsl_available_gib'],
                    host_free_gib=memory['host_free_gib'], limiting_available_gib=available,
                    reserve_gib=reserve, worker_budget_gib=budget, reference_peak_gib=peak, cpus=memory['cpus'],
                    rule='min(16 conditions, logical_cpus//2, floor((min(WSL available, host free)-max(8GiB,25%))/ceil(1.5*reference peak to 0.1GiB)))',
                    peak_source=f'data/malecns/{name}_results.json metadata.peak_worker_rss_gib',
                    peak_selection='Larger of M1j and male-v1 Phase 1 peak_worker_rss_gib (M1j on equality)')
    equal(memory, expected, 'Memory plan arithmetic and reference')


def audit_bin(path, ids, condition, row, commit, protocol_hash, n_model_neurons):
    header = read_replay_header(path)
    payload = path.read_bytes()
    length = struct.unpack('<I', payload[4:8])[0]
    equal(header['idx_dtype'], 'u16' if len(ids) <= 65536 else 'u32', 'Replay index width')
    n = header['n_spikes']
    require(type(n) is int and n >= 0, 'Replay spike count')
    dtype = '<u2' if header['idx_dtype'] == 'u16' else '<u4'
    width = np.dtype(dtype).itemsize
    equal(len(payload), 8+length+n*(width+2), 'Replay payload length')
    indices = np.frombuffer(payload, dtype=dtype, count=n, offset=8+length)
    units = np.frombuffer(payload, dtype='<u2', count=n, offset=8+length+n*width)
    require((indices < len(ids)).all(), 'Replay index bounds')
    with np.load(ROOT / row['spikes']['path'], allow_pickle=False) as raw:
        body, ts = raw['body_id'], raw['time_s']
    np.testing.assert_array_equal(np.asarray(ids, dtype='int64')[indices], body, err_msg='Replay body mapping')
    np.testing.assert_array_equal(units, np.round(ts*10000).astype('<u2'), err_msg='Replay 0.1 ms times')
    left, right = [np.round(ts[body == b]*1000, 1).tolist() for b in (10331, 16949)]
    equal(len(left), row['L_hz'], 'Replay left trial-0 rate')
    equal(len(right), row['R_hz'], 'Replay right trial-0 rate')
    expected = dict(schema_version='replay_v2', fly='male', cell_id=condition['cond_id'], variant='baseline',
                    n_model_neurons=n_model_neurons, seed=20260910+1000*(condition['global_index'] % 40),
                    seed_rule=grid.REPLAY_RULE, trial=0, mn9_left_ms=left, mn9_right_ms=right,
                    mn9_left_count=len(left), mn9_right_count=len(right),
                    mn9_left_first_ms=left[0] if left else None, mn9_right_first_ms=right[0] if right else None,
                    n_spikes=len(body), n_neurons_active=len(set(body)), levels=condition['levels'], hz=condition['hz'],
                    git_commit=commit, protocol_sha256=protocol_hash, duration_ms=1000.0, t_unit_ms=0.1,
                    idx_dtype='u16' if len(ids) <= 65536 else 'u32',
                    note='recorded output of grid trial 0 of the male model; one of the 30 trials behind the score; not a live simulation')
    equal(header, expected, 'Replay header fields')
    return header


def audit_replays(groups, p, cells, index_path, output, commit, protocol_hash, n_model_neurons):
    index, manifest = adapter.read(index_path), adapter.read(output / 'manifest.json')
    flags = {}
    for ch in DIMS:
        for b in cells['sets'][ch]['ids']:
            flags[b] = flags.get(b, 0) | FLAG_BITS[ch]
    for b, bit in [(10331, FLAG_BITS['mn9_left']), (16949, FLAG_BITS['mn9_right'])]:
        flags[b] = flags.get(b, 0) | bit
    all_ids, total = set(flags), 0
    for group in groups:
        row = group['rows'][0]
        equal(row['trial'], 0, 'Replay trial index')
        equal(Path(row['spikes']['path']).name, 'trial_00.npz', 'Replay archive name')
        with np.load(ROOT / row['spikes']['path'], allow_pickle=False) as raw:
            all_ids.update(int(b) for b in raw['body_id'])
            total += len(raw['body_id'])
    ids = sorted(all_ids)
    expected_index = dict(schema_version='replay_neurons_v1', fly='male', id_space='MaleCNS v1.0 body id', git_commit=commit,
                          replay_run=dict(seed_rule=grid.REPLAY_RULE,
                              path=Path(groups[0]['rows'][0]['spikes']['path']).parent.parent.as_posix(),
                              n_cells_run=len(groups), n_spikes_total=total, trial='grid trial 0'),
                          flag_bits=FLAG_BITS, n_neurons=len(ids), root_ids=list(map(str, ids)),
                          flags=[flags.get(b, 0) for b in ids], readouts=p['readout']['extra_readouts'])
    equal(index, expected_index, 'Replay index fields')
    expected_manifest = dict(schema_version='replay_manifest_v1', fly='male', git_commit=commit, n_cells=len(groups), cells={})
    sizes = []
    for g, group in enumerate(groups):
        c, row = group['condition'], group['rows'][0]
        path = output / (c['cond_id']+'.bin')
        header = audit_bin(path, ids, c, row, commit, protocol_hash, n_model_neurons)
        expected_manifest['cells'][c['cond_id']] = dict(levels=c['levels'], n_spikes=header['n_spikes'],
                                                       mn9_left_count=header['mn9_left_count'])
        sizes.append(path.stat().st_size)
        if (g+1) % 40 == 0:
            print(f'Audited {g+1}/{len(groups)} replays', flush=True)
    equal(manifest, expected_manifest, 'Replay manifest')
    equal(sorted(p.name for p in output.iterdir()), sorted(['manifest.json']+[g['condition']['cond_id']+'.bin' for g in groups]), 'Replay file inventory')
    return dict(min_bytes=min(sizes), median_bytes=float(np.median(sizes)), max_bytes=max(sizes), total_bytes=sum(sizes),
                n_cells=len(groups), n_neurons=len(ids), index_bytes=index_path.stat().st_size,
                manifest_bytes=(output / 'manifest.json').stat().st_size)


def audit_run(result_path=None, lookup_path=LOOKUP, comparison_path=COMPARISON, index_path=INDEX, replay_dir=REPLAYS):
    p, cells, slots = adapter.load_configuration()
    result_path = grid.RESULT if result_path is None else result_path
    compact = adapter.read(result_path)
    adapter.check_file(compact['raw_ledger'])
    full_path = ROOT / compact['raw_ledger']['path']
    full, out = adapter.read(full_path), full_path.parent
    equal({k: v for k, v in full.items() if k != 'raw'},
          {k: v for k, v in compact.items() if k != 'raw_ledger'}, 'Compact/full ledger')
    meta = compact['metadata']
    records = list(meta['sources'])+[meta['plan']]
    for record in records:
        adapter.check_file(record)
    equal(meta['sources'], grid.grid_source_records(), 'Grid source inventory')
    plan = adapter.read(ROOT / meta['plan']['path'])
    for key, value in grid.check().items():
        equal(plan[key], value, 'Plan '+key)
    equal(plan['sources'], meta['sources'], 'Plan sources')
    equal(plan['compile_only'], dict(network_builds=1, elapsed_simulated_seconds=0, spikes=0), 'Compile-only plan')
    equal(plan['brian2_version'], meta['brian2'], 'Brian2 metadata')
    equal(plan['comparison_rules'], [f'{r} {t}' for r, t in grid.COMPARISON_RULES], 'Plan rules')
    equal(plan['replay_rule'], grid.REPLAY_RULE, 'Plan replay rule')
    start_path = out / 'run_meta_start.json'
    start = adapter.read(start_path)
    start_keys = {'stage', 'started_utc', 'sources', 'plan', 'memory', 'python', 'brian2', 'codegen'}
    equal(set(start), start_keys, 'Start inventory')
    equal({k: meta[k] for k in start}, start, 'Start metadata')
    equal(set(meta), start_keys | {'completed_utc', 'walltime_s', 'total_trials', 'peak_worker_rss_gib'}, 'Metadata fields')
    require(datetime.fromisoformat(meta['completed_utc']) >= datetime.fromisoformat(meta['started_utc']), 'Run timestamps')
    require(np.isfinite(meta['walltime_s']) and meta['walltime_s'] > 0, 'Run wall time')
    equal(meta['stage'], 'male-v1 Phase 2 grid', 'Run stage')
    equal(meta['codegen'], 'cython', 'Run codegen')
    require(type(meta['memory']['workers']) is int and meta['memory']['workers'] > 0, 'Run workers')
    m1j_peak = adapter.read(DATA / 'm1j_male_results.json')['metadata']['peak_worker_rss_gib']
    phase1_peak = adapter.read(DATA / 'male_v1_phase1_results.json')['metadata']['peak_worker_rss_gib']
    for memory in (plan['memory'], meta['memory']):
        audit_memory(memory, m1j_peak, phase1_peak)
    cs = grid.conditions(p)
    expanded = expand_grid_conditions(load_grid_levels())
    equal([c['levels'] for c in cs], [c['levels'] for c in expanded], 'Independent grid order')
    equal([g['condition'] for g in full['raw']], cs, '400-cell raw inventory')
    equal(sorted(x.name for x in out.iterdir()), sorted(['full_results.json', 'run_meta_start.json']+[c['cond_id'] for c in cs]), 'Raw directory inventory')
    roster = set(adapter.pd.read_csv(ROOT / p['completeness_file'], index_col=0).index)
    records += [file_record(result_path), compact['raw_ledger'], file_record(start_path)]
    rebuilt = []
    for c, group in zip(cs, full['raw']):
        directory = out / c['cond_id']
        ledger_path = directory / 'condition_ledger.json'
        equal(adapter.read(ledger_path), group, 'Condition ledger')
        equal(set(group), {'condition', 'rows', 'pid'}, 'Condition ledger fields')
        require(type(group['pid']) is int and group['pid'] > 0, 'Worker PID')
        equal(sorted(x.name for x in directory.iterdir()), sorted(['condition_ledger.json']+
              [f'trial_{t:02d}.{ext}' for t in range(30) for ext in ('json', 'npz')]), 'Trial inventory')
        equal([r['trial'] for r in group['rows']], list(range(30)), 'Trial order')
        rows = []
        records.append(file_record(ledger_path))
        for t in range(30):
            path = directory / f'trial_{t:02d}.json'
            row = audit_trial(path, c, t, p, cells, slots, roster)
            rows.append(row)
            records.extend([file_record(path), row['spikes']])
        equal(rows, group['rows'], 'Raw rows')
        rebuilt.append(dict(condition=c, rows=rows))
        if len(rebuilt) % 40 == 0:
            print(f'Audited {len(rebuilt)}/400 cells ({len(rebuilt)*30}/12000 trials)', flush=True)
    equal(independent_summary(rebuilt, p), {k: v for k, v in compact.items() if k not in ('metadata', 'raw_ledger')}, 'Every compact summary field')
    equal(meta['total_trials'], 12000, 'Total trials')
    equal(meta['peak_worker_rss_gib'], max(r['worker_peak_rss_kib'] for g in rebuilt for r in g['rows'])/1024**2, 'Peak RSS')
    female_path, dishes_path = ROOT / 'data/lookup_table_v1_2.json', ROOT / 'data/dishes.json'
    female, male, dishes = adapter.read(female_path), adapter.read(lookup_path), adapter.read(dishes_path)
    equal(len(dishes), 174, 'Dish count')
    equal(len({d['key'] for d in dishes}), 174, 'Distinct dish keys')
    equal(female['cells_sha256'], cells_digest(female['cells']), 'Female cells digest')
    audit_lookup_cells(male, rebuilt, female)
    audit_lookup_header(male, p, cells, female, result_path, meta, female_path)
    audit_comparison(adapter.read(comparison_path), female, male, dishes,
                     dict(female=file_record(female_path), male=file_record(lookup_path), dishes=file_record(dishes_path)))
    stats = audit_replays(rebuilt, p, cells, index_path, replay_dir, male['git_commit'],
                          file_record(adapter.PROTOCOL)['sha256'], male['substrate']['neurons'])
    paths = [female_path, dishes_path, lookup_path, comparison_path, index_path, replay_dir / 'manifest.json']
    paths += [replay_dir / (c['cond_id']+'.bin') for c in cs]
    records += [file_record(path) for path in paths]
    dependencies = [Path(adapter.__file__), Path(grid.__file__), ROOT / 'sim/malecns/audit_male_v1_phase1.py',
                    ROOT / 'scripts/mn_readouts_from_replays.py', ROOT / 'scripts/run_replay.py',
                    ROOT / 'sim/grid.py', ROOT / 'sim/malecns/substrate.py']
    return dict(status='PASS', raw_trials=12000, readout_neuron_trials=12000*13, poisson_unit_trials=12000*108,
                cells=400, dishes=174, pairs=15051, replays=400, replay_sizes=stats,
                sources=list({r['path']: r for r in records}.values()), auditor=file_record(Path(__file__)),
                dependencies=[file_record(path) for path in dependencies])


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    if AUDIT.exists():
        raise FileExistsError(AUDIT)
    result = audit_run()
    write_json(AUDIT, result)
    print('Male-v1 Phase 2 audit PASS: 12000 trials, 400 cells, 174 dishes, 15051 pairs, 400 replays')


if __name__ == '__main__':
    main()
