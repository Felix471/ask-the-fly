# SPDX-License-Identifier: MIT
"""Frozen male-v1 configuration and compile-only Phase 1 planning."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
from sim.malecns import phase0
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

FREEZE = 'df508aa'
PROTOCOL = DATA / 'stim_protocol_male_v1.json'
CELLS = DATA / 'cells_male_v1.json'
PLAN = DATA / 'male_v1_phase1_plan.json'
CHANNELS = ('sugar', 'bitter', 'water', 'ir94e')
SEEDS = list(range(20260910, 20260940))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def declared(path):
    return json.loads(subprocess.check_output(['git', 'show', f'{FREEZE}:{path.relative_to(ROOT).as_posix()}'], cwd=ROOT))


def validate_protocol(p):
    if p != declared(PROTOCOL):
        raise ValueError('Protocol differs from frozen df508aa declaration')
    return p


def check_file(record):
    actual = file_record(ROOT / record['path'])
    if any(actual[k] != record[k] for k in ('path', 'bytes', 'sha256')):
        raise ValueError('Source changed: ' + record['path'])


def load_configuration():
    p = validate_protocol(read(PROTOCOL))
    cells = read(CELLS)
    if cells != declared(CELLS):
        raise ValueError('Cells differ from frozen df508aa declaration')
    if p['model']['w_syn_mV'] != .17875 or p['stimulus']['layout']['channel_order'] != list(CHANNELS):
        raise ValueError('Weight or channel order differs')
    slots = []
    for c in CHANNELS:
        ids = cells['sets'][c]['ids']
        if ids != sorted(ids) or len(ids) != p['stimulus']['channels'][c]['count']:
            raise ValueError('Physical channel layout differs')
        slots.extend(ids)
    if len(slots) != 108 or len(set(slots)) != 108:
        raise ValueError('Expected 108 unique physical targets')
    check_file(p['substrate_record'])
    record = read(ROOT / p['substrate_record']['path'])
    for name in ('connectivity.parquet', 'completeness.csv'):
        artifact = record['artifacts']['fbm/' + name]
        if artifact['path'] != p['connectivity_file' if name.endswith('parquet') else 'completeness_file']:
            raise ValueError('Substrate path differs')
        check_file(artifact)
    roster = set(pd.read_csv(ROOT / p['completeness_file'], index_col=0).index)
    readouts = {p['readout']['primary'], p['readout']['secondary']}
    for name, ids in p['readout']['extra_readouts'].items():
        if ids != cells['readouts'][name]['ids']:
            raise ValueError('Readout cells differ')
        readouts.update(ids)
    if not (set(slots) | readouts) <= roster:
        raise ValueError('Stimulus or readout missing from roster')
    return p, cells, slots


def conditions(p):
    block = p['phase1_characterization']
    result = [dict(c, id=f"s{c['sugar_hz']}_b0_w{c['water_hz']}_i{c['ir94e_hz']}",
                   n_trials=block['n_trials_per_condition']) for c in block['conditions']]
    if (len(result) != 35 or len({c['id'] for c in result}) != 35
            or any(c['bitter_hz'] != 0 or c['n_trials'] != 30 for c in result)):
        raise ValueError('Phase 1 inventory differs')
    return result


def source_rates(condition, cells):
    return [condition[c + '_hz'] for c in CHANNELS for _ in cells['sets'][c]['ids']]


def check():
    p, cells, slots = load_configuration()
    return dict(stage='male-v1 Phase 1', declaration_commit=FREEZE, poisson_units=len(slots),
                channel_order=list(CHANNELS), conditions=conditions(p), seeds=SEEDS,
                total_trials=1050, duration_ms=p['trial']['duration_ms'], dt_ms=p['model']['dt_ms'],
                w_syn_mV=p['model']['w_syn_mV'], readouts=p['readout'],
                execution='No retry/resume. No trials in --check or --plan.')


def build():
    if sys.platform != 'linux':
        raise RuntimeError('Network construction requires WSL flybrain')
    from brian2 import SpikeMonitor, second
    from sim.network import build_network
    p, cells, slots = load_configuration()
    model = build_network(p, cells, CHANNELS)
    actual = [model.i2flyid[int(i)] for i in model.target_indices]
    if actual != slots or len(set(actual)) != 108:
        raise ValueError('Built physical targets differ')
    monitor = SpikeMonitor(model.poisson, name='male_v1_input_monitor')
    model.net.add(monitor)
    model.net.store('init')
    model.net.run(0 * second)
    if float(model.net.t / second) != 0 or len(model.monitor.i) or len(monitor.i):
        raise ValueError('Compile-only build advanced time or produced spikes')
    return model, p, cells, monitor


def source_records():
    p = read(PROTOCOL)
    paths = ['sim/network.py', 'sim/malecns/phase0.py', 'sim/malecns/substrate.py',
             'sim/malecns/male_v1_adapter.py', 'sim/malecns/male_v1_phase1.py',
             'data/malecns/m1j_male_results.json', p['connectivity_file'], p['completeness_file'],
             p['substrate_record']['path'], 'data/lookup_table_v1_2.json', 'docs/phase1_characterization.md']
    return [file_record(ROOT / n) for n in paths] + [file_record(PROTOCOL), file_record(CELLS)]


def memory_plan(host_free_kib):
    if host_free_kib <= 0:
        raise ValueError('Host free memory must be positive')
    peak = read(DATA / 'm1j_male_results.json')['metadata']['peak_worker_rss_gib']
    memory = phase0.choose_workers(phase0.mem_available_gib(), host_free_kib / 1024**2, peak, os.cpu_count())
    memory['reference_peak_gib'] = memory.pop('measured_m0_peak_gib')
    memory['peak_source'] = 'data/malecns/m1j_male_results.json metadata.peak_worker_rss_gib'
    memory['rule'] = memory['rule'].replace('M0 peak', 'reference peak')
    return memory


def make_plan(host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--plan requires WSL flybrain')
    if PLAN.exists():
        raise FileExistsError(PLAN)
    plan = check()
    sources = source_records()
    plan['memory'] = memory_plan(host_free_kib)
    model, _, _, _ = build()
    for record in sources:
        check_file(record)
    plan.update(planned_utc=datetime.now(timezone.utc).isoformat(), sources=sources,
                compile_only=dict(network_builds=1, elapsed_simulated_seconds=0, spikes=len(model.monitor.i)),
                brian2_version=__import__('brian2').__version__)
    write_json(PLAN, plan)
    return plan


def check_plan(host_free_kib):
    plan = read(PLAN)
    if plan['sources'] != source_records():
        raise ValueError('Planned sources changed')
    for key, value in check().items():
        if plan[key] != value:
            raise ValueError('Plan changed: ' + key)
    if plan['compile_only'] != dict(network_builds=1, elapsed_simulated_seconds=0, spikes=0):
        raise ValueError('Invalid compile-only plan')
    if plan['brian2_version'] != __import__('brian2').__version__:
        raise ValueError('Brian2 version changed since plan')
    return plan, memory_plan(host_free_kib)
