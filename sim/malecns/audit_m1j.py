"""Independent M1j event/summary audit. No network construction or simulation."""
import hashlib
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns.audit_fbm import read, equal, require, summarize as prior_summary
from sim.malecns import split
from sim.malecns.substrate import ROOT, DATA, file_record, write_json


def result_path(brain):
    return DATA / 'm1j_male_results.json' if brain == 'male' else ROOT / 'data/m1j_female_results.json'


def configuration(brain):
    path = DATA / 'stim_protocol_malecns_m1j.json' if brain == 'male' else ROOT / 'data/stim_protocol_m1j_female.json'
    p = read(path)
    cells = read(ROOT / p['cells_file'])
    channels = p['stimulation_layout']['channels']
    slots = [body for c in ('sugar', 'bitter', 'water', 'ir94e') for body in channels[c]['ids']]
    equal(len(slots), 108 if brain == 'male' else 128, 'Physical layout')
    equal(len(set(slots)), len(slots), 'Unique physical targets')
    return p, cells, channels, slots


def right_shape(conditions):
    return split.shape_gate([dict(r, L_mean=r['R_mean'], L_sd=r['R_sd']) for r in conditions])


def audit_trial(path, condition, trial, protocol, slots, rates, replication=False):
    """Read the standalone JSON, then derive all scientific fields from its NPZ."""
    row = read(path)
    seed = protocol['seeds'][trial]
    for key, value in dict(condition=condition['id'], trial=trial, seed=seed).items():
        equal(row[key], value, f'{path.name}.{key}')
    spike_path = path.with_suffix('.npz')
    equal(file_record(spike_path), row['spikes'], f'{path}.spikes')
    duration = protocol['trial']['duration_ms'] / 1000
    dt = protocol['model']['dt_ms'] / 1000
    with np.load(spike_path, allow_pickle=False) as z:
        equal(sorted(z.files), sorted(['body_id', 'time_s', 'poisson_index', 'poisson_time_s']), 'NPZ keys')
        body, t, pi, pt = (z[k] for k in ('body_id', 'time_s', 'poisson_index', 'poisson_time_s'))
        require(body.ndim == t.ndim == pi.ndim == pt.ndim == 1 and len(body) == len(t) and len(pi) == len(pt), 'Event dimensions')
        require(np.issubdtype(body.dtype, np.integer) and np.issubdtype(pi.dtype, np.integer), 'Event IDs must be integers')
        for times in (t, pt):
            require(np.isfinite(times).all() and (times >= 0).all() and (times < duration).all()
                    and (np.diff(times) >= 0).all(), 'Invalid event times')
        require(((pi >= 0) & (pi < len(slots))).all(), 'Poisson slot outside declared layout')
        # Brian2's seeded PoissonGroup draws one MT19937 uniform per slot per dt.
        # This is random-input reconstruction only: no network/Brian2 execution.
        ticks, expected_index = np.nonzero(np.random.RandomState(seed).random_sample(
            (round(duration / dt), len(slots))) < np.asarray(rates) * dt)
        np.testing.assert_array_equal(pi, expected_index, err_msg=f'{path}: declared input indices')
        np.testing.assert_array_equal(pt, ticks * dt, err_msg=f'{path}: declared input times')
        counts = np.bincount(pi, minlength=len(slots))
        ids, frequencies = np.unique(body, return_counts=True)
        lookup = dict(zip(ids, frequencies))
        rebuilt = dict(whole_network_spikes=len(t), source_spike_counts=[int(lookup.get(b, 0)) for b in slots])
        for side, body_id in [('L', protocol['readout']['primary']), ('R', protocol['readout']['secondary'])]:
            selected = t[body == body_id]
            rebuilt[side + '_hz'] = len(selected) / duration
            rebuilt[side + '_latency_ms'] = float(selected[0] * 1000) if len(selected) else None
        if replication:
            selected = t[(body == 10331) | (body == 16949)]
            rebuilt['bilateral_mean_hz'] = len(selected) / (2 * duration)
            rebuilt['bilateral_bin_hz'] = (np.histogram(selected, np.linspace(0, duration, 21))[0] / (2 * .05)).tolist()
        for key, value in rebuilt.items():
            equal(row[key], value, f'{path}.{key}')
        rebuilt['neurons_fired'] = len(ids)
        evidence = dict(poisson_event_counts=counts.tolist(), declared_rates_hz=rates,
                        poisson_units=len(slots), poisson_events=len(pt),
                        input_hash=hashlib.sha256(pi.tobytes() + pt.tobytes()).hexdigest(),
                        unit_hashes=[hashlib.sha256(pt[pi == i].tobytes()).hexdigest() for i in range(len(slots))],
                        network_hash=hashlib.sha256(body.tobytes() + t.tobytes()).hexdigest())
    return dict(row, **rebuilt), evidence



def audit_run(brain):
    compact = read(result_path(brain))
    full_path = ROOT / compact['raw_ledger']['path']
    equal(file_record(full_path), compact['raw_ledger'], brain + '.ledger hash')
    full = read(full_path)
    equal({k:v for k,v in full.items() if k != 'raw'},
          {k:v for k,v in compact.items() if k != 'raw_ledger'}, brain + '.compact')
    out = full_path.parent
    p, cells, channels, slots = configuration(brain)
    meta = compact['metadata']
    start = read(out / 'run_meta_start.json')
    equal({k:meta[k] for k in start}, start, brain + '.start')
    for record in meta['sources'] + [meta['plan'], meta['m0_recheck']]:
        equal(file_record(ROOT / record['path']), record, record['path'])
    plan = read(ROOT / meta['plan']['path'])
    equal(plan['conditions'], p['conditions'], brain + '.conditions')
    equal(plan['sources'], meta['sources'], brain + '.sources')
    equal(meta['readouts'], {'L':p['readout']['primary'], 'R':p['readout']['secondary']}, brain + '.readouts')
    groups = {g['condition']['id']:g for g in full['raw']}
    equal(len(groups), len(full['raw']), 'Unique conditions')
    equal(sorted(groups), sorted(c['id'] for c in p['conditions']), 'Condition inventory')
    rebuilt, evidence, networks, units = [], [], {}, {}
    for c in p['conditions']:
        cid = c['id']
        g = groups[cid]
        equal(g['condition'], c, cid + '.declaration')
        equal(read(out / cid / 'condition_ledger.json'), g, cid + '.condition ledger')
        selected = set(cells['sets'][c['sugar_set']]['ids'])
        rates = [c['sugar_hz'] if channel == 'sugar' and b in selected else c['bitter_hz'] if channel == 'bitter' else 0
                 for channel in ('sugar','bitter','water','ir94e') for b in channels[channel]['ids']]
        n = c['n_trials']
        for extension in ('json', 'npz'):
            equal(sorted(x.name for x in (out / cid).glob('trial_*.' + extension)),
                  [f'trial_{i:02d}.{extension}' for i in range(n)], cid + '.inventory')
        equal([r['trial'] for r in g['rows']], list(range(n)), cid + '.trial order')
        rows = []
        for trial in range(n):
            row, detail = audit_trial(out / cid / f'trial_{trial:02d}.json', c, trial, p, slots, rates)
            equal(row, g['rows'][trial], cid + '.row')
            networks[cid,trial] = detail.pop('network_hash')
            units[cid,trial] = detail.pop('unit_hashes')
            detail.pop('input_hash')
            evidence.append(dict(condition=cid, trial=trial, seed=row['seed'], **detail))
            rows.append(row)
        rebuilt.append(dict(condition=c, rows=rows))
        print(f'{brain}: audited {len(evidence)} trials', flush=True)
    summary = prior_summary(rebuilt, False)
    for v in summary['a_prime'].values():
        v['difference_definition'] = 'Bilateral LB3c subset minus bilateral LB3b union LB3c, paired by seed'
    equal(summary, {k:v for k,v in compact.items() if k not in ('metadata','raw_ledger')}, brain + '.summary')
    equal(meta['total_trials'], len(evidence), brain + '.total trials')
    equal(meta['peak_worker_rss_gib'], max(r['worker_peak_rss_kib'] for g in rebuilt for r in g['rows']) / 1024**2, brain + '.peak RSS')
    subset = cells['sets']['sugar_lb3c_bilateral']['ids']
    silent_hash = hashlib.sha256(np.array([], dtype=float).tobytes()).hexdigest()
    for trial in range(30):
        equal(networks['A_s200_b0',trial], networks['B_s200_b0',trial], 'A200/B0 whole network')
        for slot, body in enumerate(slots):
            if body in subset:
                equal(units['AP_sugar_120',trial][slot], units['AP_sugar_lb3c_120',trial][slot], 'AP shared train')
            else:
                equal(units['AP_sugar_lb3c_120',trial][slot], silent_hash, 'AP non-subset silence')
    return dict(status='PASS', raw_trials=len(evidence), MN9_neuron_trials=2*len(evidence),
                poisson_unit_trials=len(slots)*len(evidence), conditions=len(rebuilt),
                sources=[file_record(result_path(brain)), compact['raw_ledger'], file_record(out / 'run_meta_start.json')],
                observed_worker_pids=len({g['pid'] for g in full['raw']}),
                A200_B0_identical_network_pairs=30, AP_paired_trials=30,
                AP_identical_shared_unit_trains=30*len(subset), AP_silent_non_subset_unit_trials=30*(len(slots)-len(subset)),
                secondary_shape_gate=right_shape(summary['conditions']), input_trials=evidence)


def audit_m0():
    record = read(DATA / 'm0_recheck.json')
    equal(len(record['trials']), 10, 'M0 trials')
    equal([(r['condition'],r['trial']) for r in record['trials']],
          [(c,t) for c in ('baseline','sugar200') for t in range(5)], 'M0 inventory')
    cells = read(DATA / 'cells.json')
    slots = [b for c in ('sugar','bitter','water','ir94e') for b in cells['sets'][c]['ids']]
    equal(len(slots), 91, 'M0 layout')
    total_neurons = total_spikes = 0
    expected_inputs = []
    keys = ('condition','trial','seed','sugar_hz','MN9_R_primary_hz','MN9_L_secondary_hz',
            'MN9_R_latency_ms','MN9_L_latency_ms','whole_network_spikes','driven_sugar_mean_hz')
    for trial in record['trials']:
        paths = [ROOT / trial[k]['path'] for k in ('original','recheck')]
        rows = [read(p.with_suffix('.json')) for p in paths]
        for path, row, key in zip(paths,rows,('original','recheck')):
            equal(file_record(path), trial[key], 'M0 archive hash')
            equal(row['spikes'], trial[key], 'M0 row archive')
        equal({k:rows[0][k] for k in keys}, {k:rows[1][k] for k in keys}, 'M0 row comparison')
        with np.load(paths[0],allow_pickle=False) as a, np.load(paths[1],allow_pickle=False) as b:
            equal(sorted(a.files), sorted(b.files), 'M0 every neuron key')
            for key in a.files:
                np.testing.assert_array_equal(a[key], b[key], err_msg='M0 neuron ' + key)
            count = sum(len(a[k]) for k in a.files)
            expected = dict(identical=True, key_sets_identical=True, neurons_compared=len(a.files), spikes_compared=count,
                            original_neurons=len(a.files), recheck_neurons=len(b.files), original_spikes=count, recheck_spikes=count,
                            first_differing_key=None,differing_arrays=0,missing_keys=[],extra_keys=[],condition=trial['condition'],
                            trial=trial['trial'],row_differences=[],original=trial['original'],recheck=trial['recheck'],archive_records_match=True)
            equal(expected, trial, 'M0 trial comparison')
            for row in rows:
                equal(row['seed'],20260910+trial['trial'],'M0 seed')
                equal(row['whole_network_spikes'],count,'M0 spikes')
                for side, body in [('R',16949),('L',10331)]:
                    t = a[str(body)] if str(body) in a.files else []
                    equal(row[f'MN9_{side}_' + ('primary' if side=='R' else 'secondary') + '_hz'],float(len(t)),'M0 rate')
                    equal(row[f'MN9_{side}_latency_ms'],float(t[0]*1000) if len(t) else None,'M0 latency')
                source_counts = [len(a[str(body)]) if str(body) in a.files else 0 for body in cells['sets']['sugar']['ids']]
                equal(row['driven_sugar_mean_hz'],float(np.mean(source_counts)) if row['sugar_hz'] else None,'M0 driven sugar')
            total_neurons += len(a.files)
            total_spikes += count
        rates = np.array([rows[0]['sugar_hz'] if body in cells['sets']['sugar']['ids'] else 0 for body in slots])
        ticks, indices = np.nonzero(np.random.RandomState(rows[0]['seed']).random_sample((10000,91)) < rates*.0001)
        expected_inputs.append(dict(condition=trial['condition'],trial=trial['trial'],seed=rows[0]['seed'],
                                    reconstructed_events=len(indices),saved_input_comparison='UNAVAILABLE: no Poisson arrays in M0 archives'))
    for key,value in [('neurons_compared',total_neurons),('spikes_compared',total_spikes),('verdict','IDENTICAL')]:
        equal(record[key], value, 'M0.'+key)
    benchmark = read(DATA / 'benchmark_m0.json')
    stored = {r['path']:r for r in benchmark['sources']}
    for s in record['sources']:
        equal(s['stored_m0'],stored[s['path']],'M0 stored source')
        equal(file_record(ROOT / s['path']),s['current'],'M0 current source')
        equal(s['differs'],s['stored_m0']!=s['current'],'M0 source difference')
    for s in record['execution']['sources']+[record['comparison_source']]:
        equal(file_record(ROOT / s['path']),s,'M0 launch source')
    return dict(status='PASS',verdict='IDENTICAL',raw_trials=10,neurons_compared=total_neurons,spikes_compared=total_spikes,
                poisson_unit_trials_reconstructed=910,poisson_unit_trials_compared=0,
                limitation='M0 saved neuron arrays only; reconstructed 91-unit input events cannot be compared with unsaved Poisson trains.',
                inputs=expected_inputs,source=file_record(DATA / 'm0_recheck.json'))


def audit_runs():
    m0 = audit_m0()
    runs = {brain:audit_run(brain) for brain in ('male','female')}
    result = dict(status='PASS',m0=m0,runs=runs,raw_trials=960,MN9_neuron_trials=1920,
                  poisson_unit_trials=113280,auditor=file_record(Path(__file__)),
                  dependencies=[file_record(ROOT / p) for p in ('sim/malecns/audit_fbm.py','sim/malecns/phase0.py','sim/malecns/split.py')])
    write_json(DATA / 'm1j_runs_audit.json',result)
    print('M1j audit PASS: 960 trials / 1920 MN9 trials; M0 10 exact comparisons; M0 saved Poisson trains unavailable')
    return result


if __name__ == '__main__':
    audit_runs()
