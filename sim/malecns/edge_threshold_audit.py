"""Read-only edge-count histogram audit; no simulation or substrate changes."""
import json
import numpy as np
import pyarrow.parquet as pq
from sim.malecns.substrate import ROOT, DATA, file_record, write_json


def histogram(path):
    counts = {str(i): 0 for i in range(1, 5)} | {'>=5': 0}
    minimum = None
    total = 0
    for batch in pq.ParquetFile(path).iter_batches(columns=['Connectivity']):
        values = batch.column(0).to_numpy()
        if not np.isfinite(values).all() or (values < 1).any() or (values != np.floor(values)).any():
            raise ValueError('Expected positive integer synapse counts')
        if not len(values):
            continue
        minimum = int(values.min()) if minimum is None else min(minimum, int(values.min()))
        for i in range(1, 5):
            counts[str(i)] += int((values == i).sum())
        counts['>=5'] += int((values >= 5).sum())
        total += len(values)
    assert sum(counts.values()) == total
    return {'source': file_record(path), 'minimum': minimum, 'edges': total, 'counts': counts}


def main():
    female = json.loads((ROOT / 'data/stim_protocol.json').read_text())
    paths = {'female': ROOT / female['connectivity_file'],
             'male_whole': DATA / 'derived/connectivity.parquet',
             'male_brain': DATA / 'derived/brain/connectivity.parquet'}
    result = {'graphs': {name: histogram(path) for name, path in paths.items()},
              'methods_source': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/',
              'methods': 'Computational model: cleft-score cutoff 50 in the neurotransmitter-prediction procedure; no stated five-synapse edge cutoff. Published model uses v630; our audited frozen file is v783.',
              'decision': 'Female minimum is 1, not >=5; conditional third M1f candidate not triggered. No graph or protocol change.',
              'audit_code': file_record(ROOT / 'sim/malecns/edge_threshold_audit.py')}
    write_json(DATA / 'edge_threshold_audit.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
