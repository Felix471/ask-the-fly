# SPDX-License-Identifier: MIT
"""Keep M1's full trial ledger local and freeze a small versioned summary."""
import json

from sim.malecns.substrate import DATA, file_record, write_json


def freeze():
    source = (DATA/'phase0_results.json').resolve()
    raw_target = (DATA/'runs/m1/full_results.json').resolve()
    if not source.is_relative_to(DATA.resolve()) or not raw_target.is_relative_to((DATA/'runs/m1').resolve()):
        raise ValueError('M1 ledger paths must stay inside the male data directory')
    result = json.loads(source.read_text(encoding='utf-8'))
    if 'raw' not in result or result['metadata']['total_trials']!=480:
        raise ValueError('Expected completed, unpackaged 480-trial M1 result')
    if raw_target.exists():
        raise FileExistsError('Full raw ledger already archived; never overwrite it')
    original = file_record(source)
    source.rename(raw_target)  # Preserve the complete original; no data deletion.
    archived = file_record(raw_target)
    if archived['sha256']!=original['sha256'] or archived['bytes']!=original['bytes']:
        raise ValueError('Archived ledger differs from original')
    summary = {k:v for k,v in result.items() if k!='raw'}
    summary['raw_ledger'] = archived
    summary['packaging'] = 'All original per-trial records preserved in the gitignored full ledger; this file contains the versioned summary.'
    write_json(source,summary)
    print(f'Preserved raw ledger ({archived["bytes"]:,} bytes); versioned summary {source.stat().st_size:,} bytes')


if __name__=='__main__':
    freeze()
