import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
from sim.malecns.edge_threshold_audit import histogram


class EdgeThresholdTests(unittest.TestCase):
    def test_bins_include_strong_edges_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'edges.parquet'
            pq.write_table(pa.table({'Connectivity': [1, 1, 2, 3, 4, 5, 300]}), path)
            with patch('sim.malecns.edge_threshold_audit.file_record', return_value={}):
                result = histogram(path)
            self.assertEqual(result['minimum'], 1)
            self.assertEqual(result['edges'], 7)
            self.assertEqual(result['counts'], {'1': 2, '2': 1, '3': 1, '4': 1, '>=5': 2})

    def test_invalid_counts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'edges.parquet'
            for values in [[0], [-1], [1.5], [float('nan')]]:
                pq.write_table(pa.table({'Connectivity': values}), path)
                with self.assertRaises(ValueError):
                    histogram(path)


if __name__ == '__main__':
    unittest.main()
