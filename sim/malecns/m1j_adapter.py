# SPDX-License-Identifier: MIT
"""M1j frozen declarations, physical layouts and compile-only plans."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from sim.malecns import phase0
from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.fbm_substrate import check_file, verify as verify_substrate

DECL_HASH = '9d169c3cc97145dde46bfcd6608d23211e7256ac'
CHANNELS = ['sugar', 'bitter', 'water', 'ir94e']


def protocol_path(brain='male'):
    if brain not in ('male', 'female'):
        raise ValueError('Unknown brain')
    return DATA / 'stim_protocol_malecns_m1j.json' if brain == 'male' else ROOT / 'data/stim_protocol_m1j_female.json'


def declared_json(path):
    return json.loads(subprocess.check_output(
        ['git', 'show', f'{DECL_HASH}:{path.relative_to(ROOT).as_posix()}'], cwd=ROOT))


def expected_protocol(brain='male'):
    return declared_json(protocol_path(brain))


def validate_protocol(protocol, brain='male'):
    if protocol != expected_protocol(brain):
        raise ValueError('M1j protocol differs from frozen declaration')
    return protocol


def load_configuration(brain='male'):
    p = validate_protocol(json.loads(protocol_path(brain).read_text(encoding='utf-8')), brain)
    path = ROOT / p['cells_file']
    cells = json.loads(path.read_text(encoding='utf-8'))
    if cells != declared_json(path):
        raise ValueError('M1j cells differ from frozen declaration')
    # Only an in-memory copy changes: sugar aliases support phase0.source_rates;
    # the female water slice excludes roots already represented in sugar.
    cells = deepcopy(cells)
    cells['sets']['sugar'] = deepcopy(cells['sets']['sugar_bilateral'])
    for channel in CHANNELS:
        ids = cells['sets'][channel]['ids']
        if brain == 'female' and channel == 'water':
            ids = sorted(set(ids) - set(cells['sets']['sugar']['ids']))
            cells['sets'][channel]['ids'] = ids
        if ids != p['stimulation_layout']['channels'][channel]['ids'] or ids != sorted(ids):
            raise ValueError('Declared physical slot order differs')
    ids = [body for channel in CHANNELS for body in cells['sets'][channel]['ids']]
    if len(ids) != (108 if brain == 'male' else 128) or len(set(ids)) != len(ids):
        raise ValueError('Physical layout count or duplicate target')
    roster = pd.read_csv(ROOT / p['completeness_file'], index_col=0).index
    if not (set(ids) | {p['readout']['primary'], p['readout']['secondary']}).issubset(set(roster)):
        raise ValueError('Stimulus or readout missing from roster')
    return p, cells, CHANNELS.copy()


def check(brain='male'):
    from sim.malecns.m1j_retention import verify
    verify()
    if brain == 'male':
        verify_substrate()
    p, cells, channels = load_configuration(brain)
    return {'stage': 'M1j', 'brain': brain, 'declaration_commit': DECL_HASH,
            'poisson_units': sum(len(cells['sets'][c]['ids']) for c in channels),
            'channel_order': channels, 'conditions': p['conditions'], 'seeds': p['seeds'],
            'total_trials': p['total_trials'], 'duration_ms': p['trial']['duration_ms'],
            'dt_ms': p['model']['dt_ms'], 'w_syn_mV': p['model']['w_syn_mV'],
            'readouts': {'L': p['readout']['primary'], 'R': p['readout']['secondary']},
            'execution': 'No retry/resume. No trials in --check or --plan.'}


def build(brain='male'):
    if sys.platform != 'linux':
        raise RuntimeError('Network construction requires WSL flybrain')
    from brian2 import SpikeMonitor, second
    from sim.network import build_network
    p, cells, channels = load_configuration(brain)
    model = build_network(p, cells, channels)
    expected = p['stimulation_layout']['poisson_units']
    if len(model.target_indices) != expected or len(set(model.target_indices)) != expected:
        raise ValueError('Built physical targets differ from declaration')
    actual = [model.i2flyid[int(i)] for i in model.target_indices]
    if actual != [body for c in channels for body in cells['sets'][c]['ids']]:
        raise ValueError('Built physical target order differs')
    monitor = SpikeMonitor(model.poisson, name='m1j_input_monitor')
    model.net.add(monitor)
    model.net.store('m1_init')
    model.net.run(0 * second)
    if float(model.net.t / second) != 0 or len(model.monitor.i) or len(monitor.i):
        raise ValueError('Compile-only build advanced time or produced spikes')
    return model, p, cells, monitor


def plan_path(brain):
    return DATA / 'm1j_male_plan.json' if brain == 'male' else ROOT / 'data/m1j_female_plan.json'


def source_records(brain):
    p = expected_protocol(brain)
    names = ['sim/network.py', 'sim/malecns/phase0.py', 'sim/malecns/rescale.py',
             'sim/malecns/split.py', 'sim/malecns/substrate.py', 'sim/malecns/fbm_substrate.py',
             'sim/malecns/m1j_adapter.py', 'sim/malecns/m1j_phase0.py', 'sim/m1j_female.py',
             'sim/malecns/m1j_retention.py', 'sim/malecns/m0_recheck.py',
             'data/malecns/m1j_retention.json', p['cells_file'], p['connectivity_file'], p['completeness_file']]
    return [file_record(ROOT / n) for n in names] + [file_record(protocol_path(brain))]


def memory_plan(brain, host_free_kib):
    if host_free_kib <= 0:
        raise ValueError('Host free memory must be positive')
    if brain == 'male':
        peak = json.loads((DATA / 'phase0_results.json').read_text(encoding='utf-8'))['metadata']['peak_worker_rss_gib']
        source = 'data/malecns/phase0_results.json metadata.peak_worker_rss_gib'
    else:
        peak = json.loads((ROOT / 'data/lookup_v1_2_audit.json').read_text(encoding='utf-8'))['run']['peak_worker_rss_gib']
        source = 'data/lookup_v1_2_audit.json run.peak_worker_rss_gib'
    memory = phase0.choose_workers(phase0.mem_available_gib(), host_free_kib / 1024**2, peak, os.cpu_count())
    memory['reference_peak_gib'] = memory.pop('measured_m0_peak_gib')
    memory['peak_source'] = source
    memory['rule'] = memory['rule'].replace('M0 peak', 'reference peak')
    return memory


def require_m0():
    path = DATA / 'm0_recheck.json'
    if not path.exists() or json.loads(path.read_text(encoding='utf-8')).get('verdict') != 'IDENTICAL':
        raise ValueError('M0 recheck IDENTICAL verdict required before any M1j trial')
    return file_record(path)


def make_plan(brain, host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--plan requires WSL flybrain')
    target = plan_path(brain)
    if target.exists():
        raise FileExistsError(target)
    plan = check(brain)
    sources = source_records(brain)
    plan['memory'] = memory_plan(brain, host_free_kib)
    model, _, _, _ = build(brain)
    for source in sources:
        check_file(source)
    plan.update(planned_utc=datetime.now(timezone.utc).isoformat(), sources=sources,
                compile_only={'network_builds': 1, 'elapsed_simulated_seconds': 0, 'spikes': len(model.monitor.i)},
                brian2_version=__import__('brian2').__version__)
    write_json(target, plan)
    return plan


def check_plan(brain, host_free_kib):
    require_m0()
    plan = json.loads(plan_path(brain).read_text(encoding='utf-8'))
    if plan['sources'] != source_records(brain):
        raise ValueError('Planned sources changed')
    for key, value in check(brain).items():
        if plan[key] != value:
            raise ValueError('Plan changed: ' + key)
    return plan, memory_plan(brain, host_free_kib)
