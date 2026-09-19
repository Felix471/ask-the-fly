# SPDX-License-Identifier: MIT
"""Independent raw-event and summary audit; no Brian2 import or network run."""
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns import male_v1_adapter as adapter
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

RESULT = DATA / 'male_v1_phase1_results.json'
AUDIT = DATA / 'male_v1_phase1_audit.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def equal(actual, expected, message):
    require(actual == expected, message)


def audit_trial(path, condition, trial, p, cells, slots, roster=None):
    row = adapter.read(path)
    for key, value in dict(condition=condition['id'],trial=trial,seed=20260910+trial).items():
        equal(row[key], value, f'{path}: {key}')
    equal(row['spikes'], file_record(path.with_suffix('.npz')), 'Trial archive hash')
    require(np.isfinite(row['trial_wall_s']) and row['trial_wall_s'] >= 0, 'Trial wall time')
    require(np.isfinite(row['worker_peak_rss_kib']) and row['worker_peak_rss_kib'] > 0, 'Trial RSS')
    duration, dt = p['trial']['duration_ms']/1000, p['model']['dt_ms']/1000
    with np.load(path.with_suffix('.npz'), allow_pickle=False) as z:
        equal(sorted(z.files), sorted(['body_id','time_s','poisson_index','poisson_time_s']), 'NPZ keys')
        body, times, pi, pt = (z[k] for k in ('body_id','time_s','poisson_index','poisson_time_s'))
        require(body.ndim == times.ndim == pi.ndim == pt.ndim == 1 and len(body) == len(times)
                and len(pi) == len(pt), 'Event dimensions')
        require(np.issubdtype(body.dtype,np.integer) and np.issubdtype(pi.dtype,np.integer), 'Event ID dtype')
        for ts in (times,pt):
            require(np.isfinite(ts).all() and (ts >= 0).all() and (ts < duration).all()
                    and (np.diff(ts) >= 0).all(), 'Invalid event times')
        require(((pi >= 0) & (pi < len(slots))).all(), 'Poisson index outside layout')
        if roster is not None:
            require(set(body) <= roster, 'Unknown network body')
        rates = [condition[c+'_hz'] for c in ('sugar','bitter','water','ir94e') for _ in cells['sets'][c]['ids']]
        ticks, indices = np.nonzero(np.random.RandomState(20260910+trial).random_sample(
            (round(duration/dt),len(slots))) < np.asarray(rates)*dt)
        np.testing.assert_array_equal(pi, indices, err_msg='Declared Poisson indices')
        np.testing.assert_array_equal(pt, ticks*dt, err_msg='Declared Poisson times')
        unique, counts = np.unique(body, return_counts=True)
        count_by_body = dict(zip(unique, counts))
        rebuilt = dict(whole_network_spikes=len(body),neurons_fired=len(unique),
                       source_spike_counts=[int(count_by_body.get(b,0)) for b in slots])
        for side, b in [('L',p['readout']['primary']),('R',p['readout']['secondary'])]:
            ts = times[body == b]
            rebuilt[side+'_hz'] = len(ts)/duration
            rebuilt[side+'_latency_ms'] = float(ts[0]*1000) if len(ts) else None
        for name, bodies in p['readout']['extra_readouts'].items():
            hz = []
            for b in bodies:
                ts = times[body == b]
                hz.append(len(ts)/duration)
                rebuilt[f'{name}_{b}_hz'] = hz[-1]
                rebuilt[f'{name}_{b}_latency_ms'] = float(ts[0]*1000) if len(ts) else None
            rebuilt[name+'_hz'] = float(np.mean(hz))
            ts = times[np.isin(body,bodies)]
            rebuilt[name+'_latency_ms'] = float(ts[0]*1000) if len(ts) else None
        for key, value in rebuilt.items():
            equal(row[key], value, f'{path}: {key}')
    expected_keys = set(rebuilt) | {'condition','trial','seed','trial_wall_s','worker_peak_rss_kib','spikes'}
    equal(set(row), expected_keys, 'Trial field inventory')
    return dict(row, **rebuilt)


def independent_summary(groups, p):
    """Do not call runner event, summary or derived-table functions."""
    summaries = []
    for group in groups:
        row = dict(group['condition'])
        trials = group['rows']
        keys = ['L','R']
        for name, bodies in p['readout']['extra_readouts'].items():
            keys += [f'{name}_{b}' for b in bodies] + [name]
        for key in keys:
            values = np.array([t[key+'_hz'] for t in trials])
            latencies = [t[key+'_latency_ms'] for t in trials if t[key+'_latency_ms'] is not None]
            row.update({key+'_mean':float(np.mean(values)),key+'_sd':float(np.std(values,ddof=0)),
                        key+'_firing_trials':int(np.count_nonzero(values > 0)),
                        key+'_latency_median_ms':float(np.median(latencies)) if latencies else None})
        for key in ('whole_network_spikes','neurons_fired'):
            values = [t[key] for t in trials]
            row.update({key+'_median':float(np.median(values)),key+'_min':min(values),key+'_max':max(values)})
        summaries.append(row)
    tables = {}
    fields = ['L_mean','L_sd','R_mean','R_sd','mn11d_mean','mn11d_sd','mn11v_mean','mn11v_sd',
              'cem_mean','cem_sd','whole_network_spikes_median']
    for channel, other in [('water','ir94e'),('ir94e','water')]:
        selected = sorted((r for r in summaries if r[other+'_hz'] == 0),key=lambda r:(r['sugar_hz'],r[channel+'_hz']))
        table = [{k:r[k] for k in ['id','sugar_hz',channel+'_hz']+fields} for r in selected]
        tables[channel+'_alone'] = [r for r in table if r['sugar_hz'] == 0]
        tables[channel+'_x_sugar'] = table
    return dict(conditions=summaries,tables=tables)


def audit_run():
    p, cells, slots = adapter.load_configuration()
    compact = adapter.read(RESULT)
    adapter.check_file(compact['raw_ledger'])
    full_path = ROOT / compact['raw_ledger']['path']
    out = full_path.parent
    full = adapter.read(full_path)
    equal({k:v for k,v in full.items() if k != 'raw'},
          {k:v for k,v in compact.items() if k != 'raw_ledger'}, 'Compact/full ledger')
    meta = compact['metadata']
    for record in meta['sources']+[meta['plan']]:
        adapter.check_file(record)
    equal(meta['sources'], adapter.source_records(), 'Source inventory')
    plan = adapter.read(ROOT / meta['plan']['path'])
    for key, value in adapter.check().items():
        equal(plan[key],value,'Plan '+key)
    equal(plan['sources'],meta['sources'],'Plan sources')
    equal(plan['compile_only'],dict(network_builds=1,elapsed_simulated_seconds=0,spikes=0),'Compile-only plan')
    equal(plan['brian2_version'],meta['brian2'],'Brian2 version')
    start = adapter.read(out / 'run_meta_start.json')
    equal({k:meta[k] for k in start},start,'Start metadata')
    cs = adapter.conditions(p)
    equal([g['condition'] for g in full['raw']], cs, '35-condition ledger inventory')
    equal(sorted(x.name for x in out.iterdir() if x.is_dir()),sorted(c['id'] for c in cs),'Raw directories')
    roster = set(adapter.pd.read_csv(ROOT / p['completeness_file'], index_col=0).index)
    rebuilt = []
    for c, group in zip(cs,full['raw']):
        directory = out / c['id']
        equal(adapter.read(directory / 'condition_ledger.json'),group,'Condition ledger')
        equal(sorted(x.name for x in directory.iterdir()), sorted(['condition_ledger.json']+
              [f'trial_{t:02d}.{ext}' for t in range(30) for ext in ('json','npz')]),'Trial inventory')
        equal([r['trial'] for r in group['rows']],list(range(30)),'Trial order')
        rows = [audit_trial(directory / f'trial_{t:02d}.json',c,t,p,cells,slots,roster) for t in range(30)]
        equal(rows, group['rows'], 'Raw rows')
        rebuilt.append(dict(condition=c,rows=rows))
        print(f'Audited {len(rebuilt)*30}/1050 trials',flush=True)
    summary = independent_summary(rebuilt,p)
    equal(summary,{k:v for k,v in compact.items() if k not in ('metadata','raw_ledger')},'Every summary/derived-table field')
    equal(meta['total_trials'],1050,'Trial total')
    equal(meta['peak_worker_rss_gib'],max(t['worker_peak_rss_kib'] for g in rebuilt for t in g['rows'])/1024**2,'Peak RSS')
    result = dict(status='PASS',conditions=35,raw_trials=1050,readout_neuron_trials=13650,
                  poisson_unit_trials=113400,summary_fields='All fields and all four derived tables exactly recomputed',
                  sources=[file_record(RESULT),compact['raw_ledger'],file_record(out / 'run_meta_start.json')],
                  auditor=file_record(Path(__file__)),dependencies=[file_record(Path(adapter.__file__))])
    return result


if __name__ == '__main__':
    result = audit_run()
    write_json(AUDIT,result)
    print('Male-v1 Phase 1 audit PASS: 1050 trials, 13650 readout-neuron trials, 113400 Poisson-unit trials')
