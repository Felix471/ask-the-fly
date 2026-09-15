"""Re-record the frozen 400-cell grid with six MN readouts; never edit published data."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time
import numpy as np

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from sim.run_mn_readouts import published_grid_seed, sha256, load_json
from scripts.mn_readouts_from_replays import neuron_metrics, aggregate_metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/grid/v1_2'
SPEC = ROOT / 'data/lookup_v1_2_recording.json'
RULE = {
    'mn9': {'id': '720575940660219265', 'side': 'left', 'statistic': '30-trial mean Hz'},
    'mn11': {'type': 'MN11D', 'statistic': '30-trial mean of per-trial two-cell mean Hz'},
    'threshold_hz': 5.0, 'active': 'mean >= 5.0', 'silent': 'mean < 5.0',
    'states': {'active_active': 'eats', 'silent_active': 'mouth_moves',
               'active_silent': 'proboscis_only', 'silent_silent': 'no_response'},
    'not_deciding': ['MN9 right', 'MN11V'],
    'ties': 'Not a state; existing MN9 tie handling unchanged.',
    'meaning': 'Owner-designed threshold categories of model outputs; wording approval and site integration deferred to Step2.',
}


def state_for(mn9, mn11d):
    if not np.isfinite([mn9, mn11d]).all() or min(mn9, mn11d) < 0:
        raise ValueError('Invalid rates')
    return RULE['states'][('active' if mn9 >= 5 else 'silent') + '_' + ('active' if mn11d >= 5 else 'silent')]


def groups_for(spec, protocol):
    return {'MN9_L': [str(protocol['readout']['left'])], 'MN9_R': [str(protocol['readout']['right'])],
            **{t: [n['Body_ID'] for n in spec['readout_neurons'] if n['Type'] == t] for t in ['MN11D', 'MN11V']}}


def design():
    protocol = load_json(ROOT / 'data/stim_protocol.json')
    old = load_json(ROOT / 'data/lookup_table.json')
    assert sha256(ROOT / 'data/stim_protocol.json') == old['protocol_sha256']
    assert sha256(ROOT / 'data/cells.json') == old['source_cells_sha256']
    assert sha256(ROOT / 'data/grid_levels.json') == old['grid_levels_sha256']
    inventory = load_json(ROOT / 'data/mn_readout_ids.json')
    neurons = [n for n in inventory['neurons'] if n['Type'] in ['MN9', 'MN11D', 'MN11V']]
    assert len(neurons) == 6 and all(n['in_v783'] for n in neurons)
    spec = {'base_protocol': 'data/stim_protocol.json', 'base_protocol_sha256': old['protocol_sha256'],
            'source_lookup_sha256': sha256(ROOT / 'data/lookup_table.json'),
            'seed_scheme': '20260910 +1000*(canonical_grid_index%40)+trial; published v1 batch40, not current v2',
            'trials_per_cell': 30, 'grid_cells': 400, 'readout_neurons': neurons,
            'std_ddof': 0, 'state_rule': RULE, 'output': 'data/lookup_table_v1_2.json',
            'replay_output': 'data/replay_v1_2', 'site_changes': 'None; Step2 separately gated.'}
    assert [len(x) for x in groups_for(spec, protocol).values()] == [1, 1, 2, 2]
    return spec, protocol


def verify_mn9(grouped, condition):
    old = load_json(ROOT / 'data/lookup_table.json')['cells'][condition['global_index']]
    if old['hz'] != condition['rates']:
        raise ValueError('Grid ordering differs')
    for group, prefix in [('MN9_L', 'mn9_left'), ('MN9_R', 'mn9_right')]:
        values = [r['rate_hz'] for r in grouped if r['readout'] == group]
        if len(values) != 30:
            raise ValueError('Incomplete MN9 trial set')
        for suffix, number in [('mean', np.mean(values)), ('std', np.std(values, ddof=0))]:
            actual = round(float(number), 3)
            if actual != old[prefix + '_' + suffix]:
                raise ValueError('STOP: frozen MN9 field mismatch '+prefix+'_'+suffix)
            if group == 'MN9_L' and actual != old['mn9_' + suffix]:
                raise ValueError('STOP: frozen aggregated MN9 mismatch')


def _run_cell(condition, spec, protocol, output_dir, identity):
    # Brian2 is loaded only inside authorised WSL simulation workers.
    import pandas as pd
    import resource
    from sim.network import build_network, load_cells

    cell_id = condition["cond_id"]
    out = Path(output_dir)
    ledger_path = out / f"{cell_id}.json"
    spikes_path = out / f"{cell_id}.npz"
    original_path = ROOT / "results/grid/full" / f"{cell_id}.parquet"
    expected = {**identity, "cell_id": cell_id, "global_index": condition["global_index"],
                "input_hz": condition["rates"],
                "seeds": [published_grid_seed(condition["global_index"], t) for t in range(30)],
                "original_grid_parquet_sha256": sha256(original_path)}
    if ledger_path.exists() or spikes_path.exists():
        if not ledger_path.exists() or not spikes_path.exists():
            raise ValueError(f"{cell_id}: incomplete output; refusing to overwrite it")
        saved = load_json(ledger_path)
        if saved.get("identity") != expected or saved.get("completed_trials") != list(range(30)) or saved.get("spikes_sha256") != sha256(spikes_path):
            raise ValueError(f"{cell_id}: stored result identity/completion/hash mismatch")
        print(f"reuse verified {cell_id}", flush=True)
        return saved
    original = pd.read_parquet(original_path, columns=["flywire_id", "trial", "t"])
    if not original.empty and (set(original["trial"].unique()) - set(range(30))):
        raise ValueError("original grid has unexpected trial indices")
    references = {(int(root_id), int(trial)): np.sort(frame["t"].to_numpy())
                  for (root_id, trial), frame in original[original["flywire_id"].isin(
                      [int(protocol["readout"][side]) for side in ("left", "right")])].groupby(["flywire_id", "trial"])}
    del original
    network = build_network(protocol, load_cells(), list(EXPECTED_DIMENSIONS))
    readouts = spec["readout_neurons"]
    root_ids = [n["Body_ID"] for n in readouts]
    groups = groups_for(spec, protocol)
    individual, grouped, raw_ids, raw_times, raw_trials = [], [], [], [], []
    started = time.perf_counter()
    for trial, seed in enumerate(expected["seeds"]):
        spikes = network.run_trial(condition["rates"], seed, 1000.0)
        for side in ("left", "right"):
            root_id = int(protocol["readout"][side])
            observed = np.sort(spikes.get(root_id, np.array([], dtype=float)))
            previous = references.get((root_id, trial), np.array([], dtype=float))
            if not np.array_equal(observed, previous):
                raise ValueError(f"STOP: {cell_id} trial {trial} seed {seed}: {side} MN9 spikes differ from original grid")
        pieces = [(int(root_id), np.asarray(spikes.get(int(root_id), []), dtype=float) * 1000) for root_id in root_ids]
        ids = np.concatenate([np.full(len(ts), rid, dtype=np.int64) for rid, ts in pieces])
        times = np.concatenate([ts for _, ts in pieces])
        metrics = neuron_metrics(ids, times, root_ids, 1000.0)
        prefix = {"cell_id": cell_id, "global_index": condition["global_index"], "trial": trial, "seed": seed}
        individual.extend({**prefix, **n, **metrics[n["Body_ID"]]} for n in readouts)
        grouped.extend({**prefix, "readout": name, **aggregate_metrics([metrics[r] for r in members])}
                       for name, members in groups.items())
        raw_ids.append(ids)
        raw_times.append(times)
        raw_trials.append(np.full(len(times), trial, dtype=np.int64))
    verify_mn9(grouped, condition)
    np.savez_compressed(spikes_path, flywire_id=np.concatenate(raw_ids), t_ms=np.concatenate(raw_times),
                        trial=np.concatenate(raw_trials), seeds=np.array(expected["seeds"], dtype=np.int64))
    saved = {"identity": expected, "completed_trials": list(range(30)),
             "mn9_bilateral_exact_spike_match_trials": 30, "spikes_sha256": sha256(spikes_path),
             "individual": individual, "grouped": grouped, "elapsed_s": time.perf_counter() - started,
             "peak_worker_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2}
    ledger_path.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"complete {cell_id}: 30/30 trials; bilateral MN9 exact spike match", flush=True)
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--workers', type=int, default=14)
    args = parser.parse_args()
    spec, protocol = design()
    if args.freeze:
        with SPEC.open('x', encoding='utf-8') as f:
            json.dump(spec, f, indent=2); f.write('\n')
        print('Frozen:400x30, six neurons, four-state rule, no simulation')
        return
    if not args.run or platform.system() != 'Linux' or 'microsoft' not in platform.release().lower():
        raise RuntimeError('Explicit --run in WSL required')
    if load_json(SPEC) != spec or not 1 <= args.workers <= 16:
        raise ValueError('Frozen design or worker bound differs')
    from joblib import Parallel, delayed
    import brian2
    conditions = expand_grid_conditions(load_grid_levels())
    assert len(conditions) == 400
    if any(not (ROOT / 'results/grid/full' / (c['cond_id']+'.parquet')).exists() for c in conditions):
        raise ValueError('Original trial references missing')
    files = [SPEC, Path(__file__), ROOT/'sim/network.py', ROOT/'sim/run_mn_readouts.py', ROOT/'scripts/mn_readouts_from_replays.py',
             ROOT/'data/stim_protocol.json', ROOT/'data/cells.json', ROOT/'data/grid_levels.json', ROOT/'data/mn_readout_ids.json',
             ROOT/'data/lookup_table.json', ROOT/protocol['connectivity_file'], ROOT/protocol['completeness_file']]
    identity = {'source_sha256': {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
                'seed_scheme': 'published_grid_v1_batch40', 'brian2_version': brian2.__version__,
                'duration_ms': 1000, 'channels': list(EXPECTED_DIMENSIONS)}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=True)
    available_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                             if line.startswith('MemAvailable:')))
    memory = {'wsl_available_gib': available_kib / 1024**2,
              'host_available_gib_preflight': 82859012 / 1024**2,
              'reserve_gib': 15, 'budget_gib_per_worker': 3, 'workers': args.workers,
              'reason': '14 female workers use a conservative 42 GiB budget, leaving at least 15 GiB headroom.'}
    if min(memory['wsl_available_gib'], memory['host_available_gib_preflight']) < 15 + 3 * args.workers:
        raise RuntimeError('Insufficient free RAM for the recorded headroom; no simulations started')
    print(json.dumps({'starting': identity, 'git_commit': commit, 'memory_plan': memory}), flush=True)
    started = time.perf_counter()
    results = Parallel(n_jobs=args.workers, backend='loky')(
        delayed(_run_cell)(c, spec, protocol, OUT, identity) for c in conditions)
    if any(sha256(p) != identity['source_sha256'][p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError('Source changed during run')
    meta = {**identity, 'git_commit': commit, 'completed_at': datetime.now(timezone.utc).isoformat(),
            'elapsed_s': time.perf_counter()-started, 'n_cells': 400, 'n_trials_completed': 12000,
            'n_readout_neurons': 6, 'n_proc': args.workers, 'status': 'complete', 'memory_plan': memory,
            'peak_worker_rss_gib': max(r['peak_worker_rss_gib'] for r in results),
            'bilateral_exact_spike_match_trials': sum(r['mn9_bilateral_exact_spike_match_trials'] for r in results)}
    with (OUT/'run_meta.json').open('x', encoding='utf-8') as f:
        json.dump(meta, f, indent=2); f.write('\n')
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == '__main__':
    main()
