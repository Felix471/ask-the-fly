"""Data-only v1.2 safeguards; no Brian2 import or simulation."""
import unittest
from unittest.mock import patch
from copy import deepcopy
import json
import struct
import numpy as np
from sim.lookup_v1_2 import design, groups_for, state_for, verify_mn9
from sim.run_mn_readouts import published_grid_seed
from sim.lookup import _cells_sha256
from scripts.build_lookup_v1_2 import MN9_KEYS, verify_projection
from scripts.pack_replay_v1_2 import expand, unpack


class LookupV12Tests(unittest.TestCase):
    def test_states_at_threshold(self):
        for a, b, expected in [(5, 5, 'eats'), (4.999, 5, 'mouth_moves'),
                               (5, 4.999, 'proboscis_only'), (0, 0, 'no_response')]:
            self.assertEqual(state_for(a, b), expected)

    def test_invalid_rates(self):
        for value in [-1, float('inf'), float('nan')]:
            with self.assertRaises(ValueError):
                state_for(value, 5)

    def test_frozen_design(self):
        spec, protocol = design()
        self.assertEqual(spec['state_rule']['mn9']['id'], '720575940660219265')
        self.assertEqual([len(v) for v in groups_for(spec, protocol).values()], [1, 1, 2, 2])
        self.assertEqual(spec['trials_per_cell'] * spec['grid_cells'], 12000)

    def test_published_batch_seeds(self):
        self.assertEqual(published_grid_seed(40, 0), 20260910)
        self.assertEqual(published_grid_seed(399, 29), 20299939)

    def test_mn9_mismatch_stops(self):
        condition = {'global_index': 0, 'rates': {}}
        old = {'hz': {}, **{k: 0 for k in ['mn9_mean', 'mn9_std', 'mn9_left_mean',
                                          'mn9_left_std', 'mn9_right_mean', 'mn9_right_std']}}
        grouped = [{'readout': g, 'rate_hz': 0} for g in ['MN9_L', 'MN9_R'] for _ in range(30)]
        with patch('sim.lookup_v1_2.load_json', return_value={'cells': [old]}):
            verify_mn9(grouped, condition)
            grouped[0]['rate_hz'] = 1
            with self.assertRaisesRegex(ValueError, 'STOP'):
                verify_mn9(grouped, condition)

    def test_cell_and_literal_mn9_identity(self):
        old = {'cells': [{k: 0.0 for k in MN9_KEYS} for _ in range(400)]}
        old['cells_sha256'] = _cells_sha256(old['cells'])
        new = deepcopy(old)
        for cell in new['cells']:
            cell.update(mn11d_mean=0.0, state='no_response')
        before = json.dumps(old, indent=2).encode()
        after = json.dumps(new, indent=2).encode()
        self.assertEqual(verify_projection(old, new, before, after)['literal_mn9_fields_byte_identical'], 2400)
        with self.assertRaisesRegex(ValueError, 'literal'):
            verify_projection(old, new, before, after.replace(b'"mn9_mean": 0.0', b'"mn9_mean": 0.000'))
        new['cells'][0]['mn9_mean'] = 1
        with self.assertRaisesRegex(ValueError, 'projection'):
            verify_projection(old, new, before, json.dumps(new).encode())


def replay_fixture():
    condition = {'cond_id': 'test', 'global_index': 0, 'rates': {k: 0 for k in ['sugar', 'bitter', 'water', 'ir94e']}}
    protocol = {'trial': {'seed_rule': 'base_seed=20260910'}, 'readout': {'left': 1, 'right': 2}}
    index = {'root_ids': [str(i) for i in range(1, 7)]}
    neurons = [{'Body_ID': str(i), 'Type': t, 'Root_Side': side, 'Target_Muscle': t.removeprefix('MN')}
               for i, t, side in [(3, 'MN11D', 'L'), (4, 'MN11D', 'R'), (5, 'MN11V', 'L'), (6, 'MN11V', 'R')]]
    raw = {'flywire_id': np.array([1, 2, 3, 3, 5], dtype=np.int64),
           't_ms': np.array([10., 20., 30.04, 40.06, 50.]), 'seed': np.int64(20960910),
           'condition_index': np.int64(0), 'rates': np.zeros(4)}
    header = {'schema_version': 'replay_v2', 'cell_id': 'test', 'variant': 'baseline',
              'hz': condition['rates'], 'seed': 20960910, 'idx_dtype': 'u16', 'n_spikes': 5,
              'mn9_left_ms': [10.0], 'mn9_right_ms': [20.0], 'mn9_left_count': 1, 'mn9_right_count': 1}
    encoded = json.dumps(header, separators=(',', ':')).encode()
    body = (raw['flywire_id'] - 1).astype('<u2').tobytes() + np.round(raw['t_ms'] * 10).astype('<u2').tobytes()
    return b'AFR1' + struct.pack('<I', len(encoded)) + encoded + body, raw, condition, neurons, index, protocol


class ReplayV12Tests(unittest.TestCase):
    def test_add_rows_preserve_body_and_old_header(self):
        args = replay_fixture()
        original, original_bytes, original_body = unpack(args[0])
        packed, rows, digest = expand(*args)
        updated, updated_bytes, updated_body = unpack(packed)
        self.assertEqual(original_body, updated_body)
        self.assertIn(original_bytes[1:-1].replace(b'replay_v2', b'replay_v3'), updated_bytes)
        self.assertEqual(updated['mn9_left_ms'], original['mn9_left_ms'])
        self.assertEqual(rows['MN11D']['two_cell_mean_hz'], 1)
        self.assertEqual(rows['MN11D']['cells'][0]['spike_ms'], [30.0, 40.1])
        self.assertEqual(rows['MN11D']['cells'][1]['spike_ms'], [])
        self.assertIsNone(rows['MN11V']['cells'][1]['first_ms'])
        self.assertEqual(len(digest), 64)

    def test_raw_body_mismatch_stops(self):
        args = list(replay_fixture())
        args[1]['t_ms'][0] = 11
        with self.assertRaisesRegex(ValueError, 'STOP'):
            expand(*args)

    def test_seed_mismatch_stops(self):
        args = list(replay_fixture())
        args[1]['seed'] = np.int64(1)
        with self.assertRaisesRegex(ValueError, 'seed'):
            expand(*args)

    def test_mn9_header_mismatch_stops(self):
        args = list(replay_fixture())
        args[0] = args[0].replace(b'"mn9_left_count":1', b'"mn9_left_count":2')
        with self.assertRaisesRegex(ValueError, 'MN9'):
            expand(*args)


if __name__ == '__main__':
    unittest.main()
