"""Versioned v1.2 artifacts must preserve the frozen product and replay data."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import unittest
import numpy as np
from sim.lookup import LookupTable
from sim.lookup_v1_2 import RULE, state_for
from sim.run_mn_readouts import sha256
from scripts.build_lookup_v1_2 import verify_projection, STATES
from scripts.pack_replay_v1_2 import unpack
from tests.test_lookup_v1_2 import original_text_bytes

ROOT = Path(__file__).resolve().parents[1]


class LookupV12ProductsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_path = ROOT / 'data/lookup_table.json'
        cls.new_path = ROOT / 'data/lookup_table_v1_2.json'
        cls.old = json.loads(cls.old_path.read_bytes())
        cls.new = json.loads(cls.new_path.read_bytes())
        cls.audit = json.loads((ROOT / 'data/lookup_v1_2_audit.json').read_bytes())
        cls.pack = ROOT / 'data/replay_v1_2'
        cls.manifest = json.loads((cls.pack / 'manifest.json').read_bytes())

    def test_old_cell_and_mn9_field_identity(self):
        checks = verify_projection(self.old, self.new,
                                   original_text_bytes(self.old_path, self.new['source_lookup_sha256']),
                                   self.new_path.read_bytes())
        self.assertEqual(checks['literal_mn9_fields_byte_identical'], 2400)
        original_text_bytes(self.old_path, self.new['source_lookup_sha256'])
        self.assertEqual(self.new['protocol_sha256'], self.old['protocol_sha256'])

    def test_all_states_and_added_statistics(self):
        table = LookupTable.load(self.new_path)
        self.assertEqual(len(table.cells), 400)
        self.assertEqual(self.new['state_rule'], RULE)
        for cell in table.cells:
            self.assertEqual(cell['state'], state_for(cell['mn9_mean'], cell['mn11d_mean']))
            self.assertEqual(cell['mn9_r_mean'], cell['mn9_right_mean'])
            self.assertEqual(cell['mn9_r_sd'], cell['mn9_right_std'])
            for prefix in ['mn9_r', 'mn11d', 'mn11v']:
                for suffix in ['mean', 'sd']:
                    self.assertGreaterEqual(cell[prefix + '_' + suffix], 0)
            self.assertEqual(cell['n_trials'], 30)
        counts = Counter(c['state'] for c in table.cells)
        self.assertEqual({s: counts[s] for s in STATES}, self.audit['checkpoint']['cell_counts'])

    def test_complete_audit_and_hashes(self):
        run = self.audit['run']
        self.assertEqual(run['status'], 'complete')
        self.assertEqual(run['n_trials_completed'], 12000)
        self.assertEqual(run['bilateral_exact_spike_match_trials'], 12000)
        self.assertEqual(len(self.audit['trial_artifacts']), 400)
        self.assertEqual(self.audit['checkpoint']['lookup_v1_2_sha256'], sha256(self.new_path))
        self.assertEqual(self.audit['checkpoint']['individual_neuron_trials_reconstructed'], 72000)
        self.assertEqual(self.audit['checkpoint']['grouped_readout_trials_reconstructed'], 48000)

    def test_dish_counts_and_mouth_moves_list(self):
        dishes = json.loads((ROOT / 'data/dishes.json').read_bytes())
        table = LookupTable.load(self.new_path)
        states = {d['key']: table.get(**{k: d[k] for k in table.data['dimensions']})['state'] for d in dishes}
        self.assertEqual(len(states), 174)
        self.assertEqual(states, self.audit['checkpoint']['dish_states'])
        counts = Counter(states.values())
        self.assertEqual({s: counts[s] for s in STATES}, self.audit['checkpoint']['dish_counts'])
        reported = self.audit['checkpoint']['mouth_moves']
        actual = [c for c in table.cells if c['state'] == 'mouth_moves']
        self.assertEqual([c['hz'] for c in reported], [c['hz'] for c in actual])

    def test_replay_index_and_versions(self):
        self.assertEqual((self.pack / 'replay_neurons.json').read_bytes(),
                         original_text_bytes(ROOT / 'data/replay_neurons.json', self.manifest['index_sha256']))
        self.assertEqual(self.manifest['schema_version'], 'replay_manifest_v2')
        self.assertEqual(self.manifest['variants'], ['baseline'])
        self.assertEqual(len(self.manifest['cells']), 400)

    def test_all_replay_bodies_mn9_headers_and_mn11_rows(self):
        index = json.loads((self.pack / 'replay_neurons.json').read_bytes())
        root_ids = np.array(index['root_ids'], dtype=np.int64)
        mn11_ids = {t: {n['Body_ID'] for n in self.new['readouts_recorded'] if n['Type'] == t}
                    for t in ['MN11D', 'MN11V']}
        for cell_id, entry in self.manifest['cells'].items():
            with self.subTest(cell=cell_id):
                old_blob = (ROOT / 'site/data/replay' / entry['file']).read_bytes()
                new_blob = (self.pack / entry['file']).read_bytes()
                old, old_header, old_body = unpack(old_blob)
                new, new_header, new_body = unpack(new_blob)
                self.assertEqual(sha256(self.pack / entry['file']), entry['sha256'])
                self.assertEqual(old_body, new_body)
                self.assertIn(old_header[1:-1].replace(b'replay_v2', b'replay_v3'), new_header)
                self.assertEqual(new['schema_version'], 'replay_v3')
                projection = deepcopy(new)
                del projection['readout_rows']
                projection['schema_version'] = 'replay_v2'
                self.assertEqual(old, projection)
                n = new['n_spikes']
                dtype = '<u2' if new['idx_dtype'] == 'u16' else '<u4'
                width = np.dtype(dtype).itemsize
                ids = root_ids[np.frombuffer(new_body[:n*width], dtype=dtype)]
                times = np.frombuffer(new_body[n*width:], dtype='<u2') / 10
                for kind, group in new['readout_rows'].items():
                    self.assertEqual({r['root_id'] for r in group['cells']}, mn11_ids[kind])
                    for row in group['cells']:
                        expected = times[ids == int(row['root_id'])].tolist()
                        self.assertEqual(row['spike_ms'], expected)
                        self.assertEqual(row['count'], len(expected))
                        self.assertEqual(row['rate_hz'], len(expected))
                        self.assertEqual(row['first_ms'], min(expected) if expected else None)
                    self.assertEqual(group['two_cell_mean_hz'], sum(r['count'] for r in group['cells']) / 2)


if __name__ == '__main__':
    unittest.main()
