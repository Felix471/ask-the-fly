# SPDX-License-Identifier: MIT
"""Shared M1i declaration validation, isolated layouts and compile-only planning."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from sim.malecns import phase0, split
from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.fbm_substrate import DECL_HASH, verify as verify_substrate, check_file
from sim.malecns.fbm_output_retention import verify as verify_retention

CHANNELS_B = ['fbm_sugar_labellar', 'fbm_sugar_pharyngeal', 'fbm_sugar_tarsal', 'bitter']


def protocol_path(run):
    if run not in ('a', 'b'):
        raise ValueError('Only the two declared M1i runs exist')
    return DATA / ('stim_protocol_malecns_fbm.json' if run == 'a' else 'stim_protocol_malecns_fbm_replication.json')


def declared_json(path):
    """Immutable declaration baseline, independent of mutable working-tree files."""
    relative = path.relative_to(ROOT).as_posix()
    return json.loads(subprocess.check_output(['git', 'show', f'{DECL_HASH}:{relative}'], cwd=ROOT))


def expected_protocol(run):
    p = declared_json(protocol_path(run))
    base = declared_json(DATA / 'stim_protocol_malecns.json')
    model = deepcopy(base['model'])
    model['w_syn_mV'] = .65 * .275
    if p['model'] != model or p['trial'] != base['trial'] or p['seeds'] != list(range(20260910, 20260940)):
        raise ValueError('Declaration dynamics/seeds do not match the M1i design')
    if run == 'a':
        if p['conditions'] != phase0.conditions() or p['shape_gate'] != split.expected_protocol()['split_provenance']['shape_gate']:
            raise ValueError('Declaration differs from unchanged A-D/S design')
    return p


def validate_protocol(run, protocol):
    if protocol != expected_protocol(run):
        raise ValueError('M1i protocol differs from frozen declaration')
    return protocol


def load_configuration(run):
    p = validate_protocol(run, json.loads(protocol_path(run).read_text(encoding='utf-8')))
    path = ROOT / p['cells_file']
    cells = json.loads(path.read_text(encoding='utf-8'))
    if cells != declared_json(path):
        raise ValueError('M1i cell file differs from declaration')
    channels = phase0.CHANNELS if run == 'a' else CHANNELS_B
    ids = [body for name in channels for body in cells['sets'][name]['ids']]
    if len(ids) != (91 if run == 'a' else 242) or len(set(ids)) != len(ids):
        raise ValueError('Physical layout count/overlap differs')
    if any(cells['sets'][name]['ids'] != sorted(cells['sets'][name]['ids']) for name in channels):
        raise ValueError('Physical layout order differs')
    roster = pd.read_csv(DATA / 'derived/neuron_index.csv', usecols=['bodyId'])
    if not set(ids).issubset(set(roster.bodyId)):
        raise ValueError('Input missing from roster')
    return p, cells, channels


def check(run):
    verify_substrate()
    verify_retention()
    p, cells, channels = load_configuration(run)
    conditions = p['conditions']
    if sum(c['n_trials'] for c in conditions) != (480 if run == 'a' else 95):
        raise ValueError('Trial total differs')
    if run == 'b' and any(c['seeds'] != list(range(20260910, 20260910 + c['n_trials'])) for c in conditions):
        raise ValueError('Replication seeds differ')
    return {'stage': 'M1i', 'run': run, 'declaration_commit': DECL_HASH,
            'poisson_units': sum(len(cells['sets'][c]['ids']) for c in channels),
            'channel_order': channels, 'conditions': conditions, 'seeds': p['seeds'],
            'total_trials': p['total_trials'], 'duration_ms': p['trial']['duration_ms'],
            'dt_ms': p['model']['dt_ms'], 'w_syn_mV': p['model']['w_syn_mV'],
            'execution': 'No automatic retry/resume; separate b checkpoint before a. No trials in --check or --plan.'}


def build(run, kc=False):
    if sys.platform != 'linux':
        raise RuntimeError('Network construction requires WSL flybrain')
    from brian2 import SpikeMonitor, second
    from sim.network import build_network
    p, cells, channels = load_configuration(run)
    if kc:
        if run != 'b':
            raise ValueError('KC check exists only in run b')
        p = deepcopy(p)
        condition = next(c for c in p['conditions'] if c['id'] == 'fbm_sugar_kc')
        p['connectivity_file'] = condition['connectivity_file']
        p['completeness_file'] = 'data/malecns/derived/fbm_kc/completeness.csv'
    model = build_network(p, cells, channels)
    monitor = SpikeMonitor(model.poisson, name='male_m1i_input_monitor')
    model.net.add(monitor)
    model.net.store('m1_init')
    model.net.run(0 * second)
    if float(model.net.t / second) != 0 or len(model.monitor.i) or len(monitor.i):
        raise ValueError('Compile-only build advanced time or produced spikes')
    return model, p, cells, monitor


def source_records(run):
    names = ['sim/network.py', 'sim/malecns/adapter.py', 'sim/malecns/phase0.py',
             'sim/malecns/split.py', 'sim/malecns/rescale.py', 'sim/malecns/substrate.py',
             'sim/malecns/fbm_adapter.py', 'sim/malecns/fbm_substrate.py',
             'sim/malecns/fbm_output_retention.py', 'sim/malecns/fbm_replication.py',
             'sim/malecns/fbm_phase0.py', 'data/malecns/substrate_record_fbm.json',
             'data/malecns/m1i_output_retention.json', 'data/malecns/cells.json',
             'data/malecns/cells_fbm.json']
    return [file_record(ROOT / name) for name in names] + [file_record(protocol_path(r)) for r in ('a', 'b')]


def memory_plan(host_free_kib):
    peak = json.loads((DATA / 'phase0_results.json').read_text(encoding='utf-8'))['metadata']['peak_worker_rss_gib']
    memory = phase0.choose_workers(phase0.mem_available_gib(), host_free_kib / 1024**2, peak, os.cpu_count())
    memory['measured_m1_peak_gib'] = memory.pop('measured_m0_peak_gib')
    memory['rule'] = memory['rule'].replace('M0 peak', 'M1 peak')
    return memory


def plan_path(run):
    return DATA / f'fbm_{"phase0" if run == "a" else "replication"}_plan.json'


def make_plan(run, host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--plan requires WSL flybrain')
    target = plan_path(run)
    if target.exists():
        raise FileExistsError(target)
    plan = check(run)
    plan['memory'] = memory_plan(host_free_kib)
    model, _, _, _ = build(run)
    plan.update(planned_utc=datetime.now(timezone.utc).isoformat(), sources=source_records(run),
                compile_only={'network_builds': 1, 'elapsed_simulated_seconds': 0, 'spikes': len(model.monitor.i)},
                brian2_version=__import__('brian2').__version__)
    write_json(target, plan)
    return plan


def check_plan(run, host_free_kib):
    check(run)
    plan = json.loads(plan_path(run).read_text(encoding='utf-8'))
    for source in plan['sources']:
        check_file(source)
    for key, value in check(run).items():
        if plan[key] != value:
            raise ValueError('Plan changed: ' + key)
    # Choose from fresh WSL AND host memory at launch, not stale planning RAM.
    return plan, memory_plan(host_free_kib)
