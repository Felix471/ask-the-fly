"""Independently reconstruct M1i saved events and summaries; never simulate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns import fbm_adapter, phase0, split
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

EXECUTION_COMMIT = '18698a39a7a3c6faa13a19e153c054b26f2ede62'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def equal(actual, expected, context):
    """Exact recursive comparison, with the first mismatching field named."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            raise ValueError(f'{context}: field set mismatch')
        for key in expected:
            equal(actual[key], expected[key], f'{context}.{key}')
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError(f'{context}: list length mismatch')
        for i, (a, b) in enumerate(zip(actual, expected)):
            equal(a, b, f'{context}[{i}]')
    elif actual != expected:
        raise ValueError(f'{context}: {actual!r} != {expected!r}')


def require(value, context):
    if not value:
        raise ValueError(context)


def stats(values):
    return dict(min=float(np.min(values)), median=float(np.median(values)), max=float(np.max(values)))


def moments(values):
    return dict(mean=float(np.mean(values)), sd=float(np.std(values, ddof=0)))


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
        for side, body_id in [('L', 10331), ('R', 16949)]:
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


def summarize(groups, replication):
    """Independent summary implementation; only declared gate evaluators are reused."""
    conditions = []
    byid = {g['condition']['id']: g['rows'] for g in groups}
    for group in groups:
        rows = group['rows']
        item = dict(group['condition'])
        for side in ('L', 'R'):
            values = [r[side + '_hz'] for r in rows]
            ms = moments(values)
            latency = [r[side + '_latency_ms'] for r in rows if r[side + '_latency_ms'] is not None]
            item[side + '_latency_median_ms'] = float(np.median(latency)) if latency else None
            if replication:
                item[side + '_hz'] = dict(ms, positive_trials=sum(v > 0 for v in values))
            else:
                item.update({side + '_mean': ms['mean'], side + '_sd': ms['sd'], side + '_firing_trials': len(latency)})
        item['whole_network_spikes'] = stats([r['whole_network_spikes'] for r in rows])
        if replication:
            values = [r['bilateral_mean_hz'] for r in rows]
            item['bilateral_mean_hz'] = dict(moments(values), positive_trials=sum(v > 0 for v in values))
            item['bilateral_bin_hz'] = stats([v for r in rows for v in r['bilateral_bin_hz']])
        else:
            item['neurons_fired'] = stats([r['neurons_fired'] for r in rows])
        conditions.append(item)
    if replication:
        sugar = next(c for c in conditions if c['id'] == 'fbm_sugar')['bilateral_mean_hz']
        criteria = dict(fbm_sugar=30 <= sugar['mean'] <= 90 and sugar['positive_trials'] == 30)
        for cid in ('fbm_bitter', 'fbm_both'):
            criteria[cid] = all(r['L_hz'] == 0 and r['R_hz'] == 0 for r in byid[cid])
        paired = {}
        for key in ('L_hz', 'R_hz', 'bilateral_mean_hz'):
            differences = [kc[key] - base[key] for kc, base in zip(byid['fbm_sugar_kc'], byid['fbm_sugar'][:5])]
            paired[key] = dict(differences=differences, **moments(differences))
        return dict(conditions=conditions, replication_criteria=criteria,
                    kc_paired_difference=dict(definition='KC minus unscaled, seeds 20260910-20260914', criterion=None, metrics=paired))
    ap = {}
    for side in ('L', 'R'):
        differences = [sub[side + '_hz'] - union[side + '_hz'] for sub, union in
                       zip(byid['AP_sugar_lb3c_120'], byid['AP_sugar_120'])]
        ms = moments(differences)
        ap[side] = dict(difference_definition='LB3c12 minus sugar17, paired by seed', mean_hz=ms['mean'], sd_hz=ms['sd'],
                        lower_trials=sum(v < 0 for v in differences), equal_trials=sum(v == 0 for v in differences),
                        higher_trials=sum(v > 0 for v in differences))
    gates, shape = phase0.evaluate_gates(conditions), split.shape_gate(conditions)
    return dict(conditions=conditions, gates=gates, a_prime=ap, shape_gate=shape,
                overall_primary=gates['L']['overall'] and shape['S'])


def audit_run(run):
    compact_path = DATA / f'm1i_{run}_results.json'
    compact = read(compact_path)
    out = DATA / f'runs/m1i/{run}'
    full_path = out / 'full_results.json'
    equal(file_record(full_path), compact['raw_ledger'], f'{run}.raw_ledger')
    full = read(full_path)
    equal({k: v for k, v in full.items() if k != 'raw'},
          {k: v for k, v in compact.items() if k != 'raw_ledger'}, f'{run}.compact')
    protocol, cells, channels = fbm_adapter.load_configuration(run)
    meta = compact['metadata']
    start = read(out / 'run_meta_start.json')
    equal({k: meta[k] for k in start}, start, f'{run}.run_meta_start')
    equal(file_record(ROOT / meta['plan']['path']), meta['plan'], f'{run}.plan')
    plan = read(ROOT / meta['plan']['path'])
    equal(plan['conditions'], protocol['conditions'], f'{run}.plan.conditions')
    equal(plan['sources'], meta['sources'], f'{run}.sources')
    for record in meta['sources']:
        equal(file_record(ROOT / record['path']), record, record['path'])
        blob = subprocess.check_output(['git', 'show', f"{EXECUTION_COMMIT}:{record['path']}"], cwd=ROOT)
        # Git stores LF for some files whose executed Windows checkout has CRLF.
        # The exact executed bytes were checked above; only this commit-text
        # comparison normalizes line endings, without changing the hash guard.
        equal(blob.replace(b'\r\n', b'\n'), (ROOT / record['path']).read_bytes().replace(b'\r\n', b'\n'),
              f"{record['path']} at execution commit (LF/CRLF normalized)")
    slots = [b for channel in channels for b in cells['sets'][channel]['ids']]
    originals = {g['condition']['id']: g for g in full['raw']}
    equal(sorted(originals), sorted(c['id'] for c in protocol['conditions']), f'{run}.conditions')
    equal(len(full['raw']), len(originals), f'{run}.unique conditions')
    rebuilt, evidence = [], []
    inputs, networks, unit_hashes = {}, {}, {}
    for condition in protocol['conditions']:
        cid = condition['id']
        group = originals[cid]
        equal(group['condition'], condition, f'{run}.{cid}.declaration')
        n = condition['n_trials']
        if run == 'b':
            equal(condition['seeds'], protocol['seeds'][:n], f'{cid}.seeds')
            rates = [condition['rates_hz'][channel] for channel in channels for _ in cells['sets'][channel]['ids']]
        else:
            selected = set(cells['sets'][condition['sugar_set']]['ids'])
            rates = [condition['sugar_hz'] if channel == 'sugar' and b in selected else
                     condition['bitter_hz'] if channel == 'bitter' else 0
                     for channel in channels for b in cells['sets'][channel]['ids']]
        equal(sorted(p.name for p in (out / cid).glob('trial_*.json')), [f'trial_{t:02d}.json' for t in range(n)], f'{cid}.JSON inventory')
        equal(sorted(p.name for p in (out / cid).glob('trial_*.npz')), [f'trial_{t:02d}.npz' for t in range(n)], f'{cid}.NPZ inventory')
        ledger_rows = sorted(group['rows'], key=lambda r: r['trial'])
        equal([r['trial'] for r in ledger_rows], list(range(n)), f'{cid}.trials')
        rows = []
        for trial in range(n):
            path = out / cid / f'trial_{trial:02d}.json'
            row, detail = audit_trial(path, condition, trial, protocol, slots, rates, run == 'b')
            # Run a adds neurons_fired to the full ledger after saving the trial JSON.
            expected = row if run == 'a' else {k: v for k, v in row.items() if k != 'neurons_fired'}
            equal(ledger_rows[trial], expected, f'{cid}[{trial}].full ledger')
            key = (cid, trial)
            inputs[key] = detail.pop('input_hash')
            networks[key] = detail.pop('network_hash')
            unit_hashes[key] = detail.pop('unit_hashes')
            evidence.append(dict(condition=cid, trial=trial, seed=row['seed'], **detail))
            rows.append(row)
        rebuilt.append(dict(condition=condition, rows=rows))
        print(f'M1i {run}: audited {len(evidence)} trials', flush=True)
    summary = summarize(rebuilt, run == 'b')
    equal(summary, {k: v for k, v in compact.items() if k not in ('metadata', 'raw_ledger')}, f'{run}.summary')
    equal(meta['total_trials'], len(evidence), f'{run}.total_trials')
    peak = max(r['worker_peak_rss_kib'] for g in rebuilt for r in g['rows']) / 1024**2
    equal(meta['peak_worker_rss_gib'], peak, f'{run}.peak RSS')
    pair_counts = {}
    if run == 'b':
        for trial in range(5):
            equal(inputs['fbm_sugar', trial], inputs['fbm_sugar_kc', trial], f'KC input pair {trial}')
        pair_counts = dict(kc_identical_input_pairs=5, kc_identical_unit_trains=5 * len(slots))
    else:
        for trial in range(30):
            equal(networks['A_s200_b0', trial], networks['B_s200_b0', trial], f'A200/B0 network pair {trial}')
            for body in cells['sets']['sugar_lb3c']['ids']:
                slot = slots.index(body)
                equal(unit_hashes['AP_sugar_120', trial][slot], unit_hashes['AP_sugar_lb3c_120', trial][slot], 'AP shared input train')
        pair_counts = dict(A200_B0_identical_network_pairs=30, AP_identical_shared_unit_trains=360)
    return dict(status='PASS', raw_trials=len(evidence), MN9_neuron_trials=2 * len(evidence),
                poisson_unit_trials=len(slots) * len(evidence), bilateral_bin_rows=20 * len(evidence) if run == 'b' else 0,
                conditions=len(rebuilt), sources=[file_record(compact_path), compact['raw_ledger'], file_record(out / 'run_meta_start.json')],
                simulation_commit_in_run_meta=start.get('git_commit'), source_text_verified_at_commit=EXECUTION_COMMIT,
                commit_comparison='LF/CRLF normalized text; executed working-file hashes separately checked exactly against metadata.',
                observed_worker_pids=len({g['pid'] for g in full['raw']}),
                poisson_check='Every event index/time exactly reconstructed from declared MT19937 seed, rates, dt and full physical layout; not a network simulation.',
                **pair_counts, input_trials=evidence)


def audit_runs():
    runs = {run: audit_run(run) for run in ('b', 'a')}
    result = dict(status='PASS', runs=runs, raw_trials=sum(r['raw_trials'] for r in runs.values()),
                  MN9_neuron_trials=sum(r['MN9_neuron_trials'] for r in runs.values()), auditor=file_record(Path(__file__)))
    write_json(DATA / 'm1i_runs_audit.json', result)
    print(f"M1i audit PASS: {result['raw_trials']} trials / {result['MN9_neuron_trials']} MN9-neuron trials")
    return result


if __name__ == '__main__':
    audit_runs()
