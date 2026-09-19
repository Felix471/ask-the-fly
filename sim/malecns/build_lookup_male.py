# SPDX-License-Identifier: MIT
"""Build the additive male lookup from a completed, source-checked grid ledger."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sim.lookup import LookupTable, _cells_sha256
from sim.lookup_v1_2 import state_for
from sim.malecns import male_v1_adapter as adapter, male_v1_grid as grid
from sim.malecns.audit_male_v1_phase1 import equal, require
from sim.malecns.substrate import ROOT, file_record, write_json

FEMALE = ROOT / 'data/lookup_table_v1_2.json'
OUTPUT = ROOT / 'data/lookup_table_male.json'
EXTRA_STATISTICS = dict(
    std_ddof=0, decimal_places=3,
    mn11d='Mean and population SD over 30 per-trial three-cell mean rates',
    mn11v='Mean and population SD over 30 per-trial two-cell mean rates',
    cem='Mean and population SD over 30 per-trial six-cell mean rates',
    mn9_r='Mean and population SD of the secondary R16949 rate; aliases of mn9_right_*.',
    state='Threshold applied to unrounded 30-trial means; rounding does not change any state')
FIELD_NOTE = ('mn9_mean and mn9_left_* are the primary L10331 (XLSX L); '
              'mn9_right_* and mn9_r_* are the secondary R16949 (XLSX R); the secondary does not decide')


def current_commit():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def checked_results(path):
    """Source and raw-ledger identity checks shared by the builder and packer."""
    result = adapter.read(path)
    equal(result['metadata']['total_trials'], 12000, 'Expected 12000 completed trials')
    for record in result['metadata']['sources']+[result['metadata']['plan'], result['raw_ledger']]:
        adapter.check_file(record)
    full = adapter.read(ROOT / result['raw_ledger']['path'])
    equal({k: v for k, v in full.items() if k != 'raw'},
          {k: v for k, v in result.items() if k != 'raw_ledger'}, 'Compact/raw ledger differs')
    return result, full


def lookup_cells(result, female, conditions):
    equal(len(result['cells']), 400, '400 results required')
    equal(len(female['cells']), 400, '400 female cells required')
    equal(len(conditions), 400, '400 canonical cells required')
    cells = []
    for row, old, condition in zip(result['cells'], female['cells'], conditions):
        for key, value in condition.items():
            equal(row[key], value, 'Result coordinate '+key)
        equal(row['levels'], {d: old[d] for d in adapter.CHANNELS}, 'Female levels/order')
        equal(row['hz'], old['hz'], 'Female Hz/order')
        cell = dict(row['levels'], hz=deepcopy(row['hz']))
        for target, source in [('mn9_mean', 'L_mean'), ('mn9_std', 'L_sd'),
                               ('mn9_left_mean', 'L_mean'), ('mn9_left_std', 'L_sd'),
                               ('mn9_right_mean', 'R_mean'), ('mn9_right_std', 'R_sd')]:
            cell[target] = round(float(row[source]), 3)
        cell['n_trials'] = 30
        for name in ('mn11d', 'mn11v', 'mn9_r', 'cem'):
            source = 'R' if name == 'mn9_r' else name
            for suffix in ('mean', 'sd'):
                cell[name+'_'+suffix] = round(float(row[source+'_'+suffix]), 3)
        cell['state'] = state_for(row['L_mean'], row['mn11d_mean'])
        equal(cell['state'], state_for(cell['mn9_mean'], cell['mn11d_mean']), 'Threshold rounding ambiguity')
        equal(list(cell), list(old)[:-1]+['cem_mean', 'cem_sd', 'state'], 'Female field order')
        cells.append(cell)
    return cells


def build(result_path=None, female_path=FEMALE, output=OUTPUT):
    if output.exists():
        raise FileExistsError(output)
    p, source_cells, _ = adapter.load_configuration()
    result_path = grid.RESULT if result_path is None else result_path
    result, full = checked_results(result_path)
    conditions = grid.conditions(p)
    equal([g['condition'] for g in full['raw']], conditions, 'Raw cell inventory')
    equal(grid.summarize(full['raw'], p)['cells'], result['cells'], 'Ledger summary')
    female = LookupTable.load(female_path).data
    equal(file_record(ROOT / 'data/grid_levels.json')['sha256'], female['grid_levels_sha256'], 'Grid hash')
    substrate = adapter.read(ROOT / p['substrate_record']['path'])
    minimum = min(r['synapses_per_edge'] for r in substrate['synapses_per_edge_histogram']
                  if r['threshold_action'] == 'kept before autapse removal')
    counts = {k: substrate['counts'][k] for k in ('neurons', 'edges', 'synapses')}
    counts.update(min_synapses=minimum, autapses_removed=substrate['counts']['autapses_removed'])
    cells = lookup_cells(result, female, conditions)
    table = dict(schema_version='lookup_male_v1', fly='male', generated_at=datetime.now(timezone.utc).isoformat(),
                 git_commit=current_commit(), protocol=file_record(adapter.PROTOCOL),
                 source_cells=file_record(adapter.CELLS), grid_levels_sha256=female['grid_levels_sha256'],
                 data_version=p['data_version'], substrate=counts,
                 model=f"Shiu 2024 LIF on MaleCNS v1.0, w_syn 0.17875 mV, Brian2 {result['metadata']['brian2']} cython, store/restore path",
                 readout=dict(neuron='MN9', aggregation='primary_only', primary=10331, primary_side='XLSX L',
                              secondary=16949, secondary_side='XLSX R', unit='Hz (spikes per 1000 ms trial)'),
                 n_trials_per_cell=30, **{k: deepcopy(female[k]) for k in ('dimensions', 'levels', 'level_notes')},
                 state_rule=deepcopy(p['state_rule']),
                 readouts_recorded=[deepcopy(row) for group in source_cells['readouts'].values() for row in group['source_rows']],
                 extra_statistics=deepcopy(EXTRA_STATISTICS), female_reference=file_record(female_path),
                 results=file_record(result_path), product_commitments=deepcopy(p['product_commitments']),
                 field_note=FIELD_NOTE, cells_sha256=_cells_sha256(cells), cells=cells)
    LookupTable(table)
    require(len(cells) == 400, 'Cell count')
    write_json(output, table)
    return table


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    table = build()
    print(f"Built {len(table['cells'])} male lookup cells: {table['cells_sha256']}")


if __name__ == '__main__':
    main()
