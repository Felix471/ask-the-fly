"""Synthetic M0 tests; never load or run Brian2."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from sim.malecns.substrate import make_roster, signed_batch, select_cells, derived_protocol, sha256


class SubstrateTests(unittest.TestCase):
    def test_hash_works_on_wsl_python310_without_file_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture'
            path.write_bytes(b'abc')
            with patch('hashlib.file_digest', None, create=True):
                self.assertEqual(sha256(path), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

    def roster(self):
        annotations = pd.DataFrame({'bodyId': [30, 10, 20, 40, 50, 60, 70],
                                    'superclass': ['cb_intrinsic'] * 6 + [None],
                                    'status': ['Traced', 'Anchor', 'Traced', 'Traced', 'Traced', 'Traced', 'Traced']})
        nt = pd.DataFrame({'body': [10, 20, 30, 40, 50, 70],
                           'consensus_nt': ['gaba', 'glutamate', 'acetylcholine', 'unclear', 'histamine', 'gaba']})
        return make_roster(annotations, nt)

    def test_roster_filter_sort_and_signs(self):
        r = self.roster()
        self.assertEqual(r.bodyId.tolist(), [10, 20, 30, 40, 50, 60])
        self.assertEqual(r['index'].tolist(), list(range(6)))
        self.assertEqual(r.sign.tolist(), [-1, -1, 1, 1, 1, 1])
        self.assertEqual(r.default_positive.tolist(), [False, False, False, True, False, True])
        self.assertEqual(r.consensus_nt.tolist()[-1], 'missing')

    def test_both_endpoints_and_signed_weights(self):
        d = pd.DataFrame({'body_pre': [10, 40, 60, 70, 10], 'body_post': [20, 30, 10, 20, 70],
                          'weight': [2, 4, 1, 99, 88]})
        out = signed_batch(d, self.roster())
        self.assertEqual(out['Connectivity'].tolist(), [2, 4, 1])
        self.assertEqual(out['Excitatory x Connectivity'].tolist(), [-2, 4, 1])
        self.assertEqual(out['Presynaptic_Index'].tolist(), [0, 3, 5])
        self.assertEqual(out['Postsynaptic_Index'].tolist(), [1, 2, 0])

    def test_bad_weight_rejected(self):
        for value in [0, -1, 1.5, np.nan]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                signed_batch(pd.DataFrame({'body_pre': [10], 'body_post': [20], 'weight': [value]}), self.roster())

    def test_duplicate_ids_rejected(self):
        a = pd.DataFrame({'bodyId': [1, 1], 'superclass': ['cb', 'cb']})
        with self.assertRaises(ValueError):
            make_roster(a, pd.DataFrame({'body': [1], 'consensus_nt': ['gaba']}))

    def test_unrecognised_label_is_not_silently_defaulted(self):
        with self.assertRaises(ValueError):
            make_roster(pd.DataFrame({'bodyId': [1], 'superclass': ['cb']}),
                        pd.DataFrame({'body': [1], 'consensus_nt': ['typo']}))

    def test_source_side_and_type_selection(self):
        rows = [{'Connectome': 'maleCNS', 'Subtype': t, 'Root_Side': side, 'Body_ID': str(i),
                 'Type': 'LB3' if t.startswith('LB3') else 'LB1'}
                for i, (t, side) in enumerate([('LB3b', 'L'), ('LB3c', 'L'), ('LB3b', 'R'),
                                               ('LB1a', 'R'), ('LB3a', 'L'), ('LB1e', 'R')], 1)]
        rows += [dict(rows[0], Connectome='FAFB', Body_ID='99')]
        sets = select_cells(rows)
        self.assertEqual(sets['sugar']['ids'], [1, 2])
        self.assertEqual(sets['sugar_lb3c']['ids'], [2])
        self.assertEqual(sets['bitter']['ids'], [4])
        self.assertEqual(sets['water']['ids'], [5])
        self.assertEqual(sets['ir94e']['ids'], [6])

    def test_protocol_inherits_model_without_mutation(self):
        from pathlib import Path
        import json
        base = json.loads(Path('data/stim_protocol.json').read_text(encoding='utf-8'))
        before = deepcopy(base)
        sets = {k: {'ids': list(range(n))} for k, n in [('sugar', 17), ('bitter', 38),
                ('water', 17), ('ir94e', 19), ('sugar_lb3c', 12)]}
        p = derived_protocol(base, sets)
        self.assertEqual(base, before)
        self.assertEqual(p['model'], base['model'])
        self.assertEqual(p['trial'], base['trial'])
        self.assertEqual(p['phase1_characterization'], base['phase1_characterization'])
        self.assertEqual(p['readout']['primary'], 16949)
        self.assertEqual(p['readout']['secondary'], 10331)
        self.assertNotIn('left', p['readout'])
        self.assertEqual(p['stimulus']['channels']['sugar']['count'], 17)
        self.assertNotIn('A_prime_sugar_bench21', p['phase0_conditions'])
        self.assertEqual(p['phase0_conditions']['A_prime_sugar_lb3c']['sugar_hz'], [120])


if __name__ == '__main__':
    unittest.main()
