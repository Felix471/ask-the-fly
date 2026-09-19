# SPDX-License-Identifier: MIT
"""File-only export checks: no raw trial access and no simulation."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts import export_male_site as shipping
from scripts import export_neurons_male as neurons

ROOT = Path(__file__).resolve().parents[1]


class MaleShipping(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in ('data/lookup_table_male.json', 'data/dishes.json'):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / rel).read_bytes())
        self.write('data/malecns/male_female_comparison.json', {'n_distinct_male_cells': 55})
        table = shipping.read(self.root / 'data/lookup_table_male.json')
        cells = {}
        for row in table['cells']:
            levels = {d: row[d] for d in table['dimensions']}
            cid = shipping.grid_cell_id(levels)
            path = self.root / f'data/replay_male/{cid}.bin'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'AFR1' + cid.encode())
            cells[cid] = dict(levels=levels, n_spikes=0, mn9_left_count=0)
        self.write('data/replay_male/manifest.json', dict(schema_version='replay_manifest_v1',
                   fly='male', git_commit='a' * 40, n_cells=400, cells=cells))
        self.commit = patch.object(shipping, 'current_commit', return_value='a' * 40)
        self.commit.start()
        self.addCleanup(self.commit.stop)

    def write(self, rel, obj):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj), encoding='utf-8')

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_export_preserves_sources_and_check_writes_nothing(self):
        before = self.snapshot()
        manifest = shipping.export(self.root)
        self.assertEqual(manifest['n_cells'], 55)
        after = self.snapshot()
        for path, content in before.items():
            self.assertEqual(after[path], content)
        self.assertEqual(shipping.check_export(self.root), [])
        self.assertEqual(after, self.snapshot())
        for cid in manifest['cells']:
            self.assertEqual(after[f'site/data/replay_male/{cid}.bin'], before[f'data/replay_male/{cid}.bin'])

    def test_refuses_overwrite_and_force_cleans_only_site_orphans(self):
        shipping.export(self.root)
        with self.assertRaises(FileExistsError):
            shipping.export(self.root)
        orphan = self.root / 'site/data/replay_male/orphan.bin'
        orphan.write_bytes(b'orphan')
        self.assertTrue(any('orphan' in p for p in shipping.check_export(self.root)))
        shipping.export(self.root, force=True)
        self.assertFalse(orphan.exists())
        self.assertEqual(len(list((self.root / 'data/replay_male').glob('*.bin'))), 400)

    def test_wrong_comparison_refused_before_any_site_write(self):
        self.write('data/malecns/male_female_comparison.json', {'n_distinct_male_cells': 54})
        with self.assertRaisesRegex(ValueError, 'occupied cell count'):
            shipping.export(self.root)
        self.assertFalse((self.root / 'site').exists())

    def test_manifest_metadata_and_payload_corruption_rejected(self):
        manifest = shipping.export(self.root)
        cid = next(iter(manifest['cells']))
        path = self.root / f'site/data/replay_male/{cid}.bin'
        original = path.read_bytes()
        path.write_bytes(b'BAD!' + original[4:])
        self.assertTrue(any('sha256' in p for p in shipping.check_export(self.root)))
        path.write_bytes(original)
        manifest['cells'][cid]['mn9_left_count'] += 1
        self.write('site/data/replay_male/manifest.json', manifest)
        self.assertTrue(any('research manifest' in p for p in shipping.check_export(self.root)))


class MalePositions(unittest.TestCase):
    def test_position_precedence_and_no_group_median_fallback(self):
        table = pd.DataFrame(dict(somaLocation=['[1 2 3]', '', '', ''],
            tosomaLocation=['[9 9 9]', '[3 4 5]', '', ''],
            superclass=['a', 'a', 'a', 'unpositioned'], **{'class': ['x'] * 4}))
        xyz, sources = neurons.positions(table)
        np.testing.assert_array_equal(xyz[:2], [[1, 2, 3], [3, 4, 5]])
        self.assertTrue(np.isnan(xyz[2:]).all())
        self.assertEqual(sources.tolist(), ['soma', 'tosoma', 'placeholder', 'placeholder'])
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            neurons.position('[1 2]')

    def test_axes_are_inferred_and_brain_scale_excludes_vnc(self):
        # ML is z (L larger), DV is x (ventral smaller), AP is y.
        xyz = np.array([[10, 0, 9], [11, 1, 11], [10, 1, -9], [11, 0, -11],
                        [-100, 0, 9], [-101, 1, -9]], dtype=float)
        table = pd.DataFrame(dict(somaSide=['L', 'L', 'R', 'R', 'L', 'R'],
                                  somaNeuromere=['', '', '', '', 'T1', 'T2']))
        xy, frame, vnc = neurons.project(table, xyz, np.array(['soma'] * 6), np.arange(6))
        self.assertEqual(frame['axes'], ['z', 'x'])
        self.assertEqual(frame['flip'], [True, True])
        self.assertLess(xy[0, 0], xy[2, 0])
        self.assertLess(xy[1, 1], xy[0, 1])
        self.assertTrue(((xy[vnc, 1] >= .96) & (xy[vnc, 1] <= 1)).all())
        self.assertEqual(frame['span'], 22)
        self.assertAlmostEqual(abs(xy[1, 1]-xy[0, 1]), abs(xy[1, 0]-xy[0, 0])/2)

    def test_deterministic_layout_keeps_missing_readout_outside_replay_prefix(self):
        cells = shipping.read(ROOT / 'data/malecns/cells_male_v1.json')
        ids = [b for group in cells['readouts'].values() for b in group['ids']]
        table = pd.DataFrame([
            dict(bodyId=b, somaLocation=f'[{10+i%3} {i%2} {10 if i%2 else -10}]',
                 tosomaLocation='', somaSide='L' if i%2 else 'R', somaNeuromere='',
                 superclass='brain', **{'class': 'motor'}) for i, b in enumerate(ids)] + [
            dict(bodyId=b, somaLocation=f'[-{100+i} {i%2} {10 if i%2 else -10}]',
                 tosomaLocation='', somaSide='L' if i%2 else 'R', somaNeuromere='T1',
                 superclass='vnc', **{'class': 'motor'}) for i, b in enumerate([9991, 9992])]
        ).set_index('bodyId')
        index = dict(root_ids=list(map(str, ids[:-1])), flags=[0] * (len(ids)-1),
                     n_neurons=len(ids)-1, flag_bits={'mn9_left': 16})
        # Both an indexed neuron and the appended readout need placeholders.
        table.loc[[ids[0], ids[-1]], 'somaLocation'] = ''
        table.loc[ids[0], 'somaNeuromere'] = 'T1'
        # An unpositioned brain candidate is ineligible for the background.
        table.loc[9993] = dict(somaLocation='', tosomaLocation='', somaSide='L',
                              somaNeuromere='', superclass='brain', **{'class': 'motor'})
        a = neurons.build(index, table, cells, 'a' * 40, background=0)
        b = neurons.build(index, table, cells, 'a' * 40, background=0)
        self.assertEqual(json.dumps(a), json.dumps(b))
        self.assertEqual(a['n_indexed'], 12)
        self.assertEqual(a['n'], 13)
        self.assertEqual(a['non_replay_readouts'], [str(ids[-1])])
        self.assertEqual(list(base64.b64decode(a['flags_b64'])[:12]), index['flags'])
        entries = [c for group in a['named'] for c in group['cells']]
        self.assertEqual(len(entries), 13)
        self.assertEqual(next(c for c in entries if c['root_id'] == str(ids[-1]))['index'], 12)
        self.assertEqual(a['position_sources'], dict(soma=11, tosoma=0, placeholder=1))
        self.assertEqual(a['placeholder_indexed'], 1)
        self.assertEqual(a['position_sources_all']['placeholder'], 2)
        xy = np.frombuffer(base64.b64decode(a['xy_b64']), dtype='<u2').reshape(-1, 2) / 65535
        for i in (0, 12):
            self.assertTrue(.15 <= xy[i, 0] <= .85)
            self.assertTrue(.90 - 1/65535 <= xy[i, 1] <= .95 + 1/65535)
        with self.assertRaisesRegex(ValueError, 'background sample'):
            neurons.build(index, table, cells, 'a' * 40, background=1)

    def test_placeholder_spread_is_stable_per_id_and_nonanatomical(self):
        ids = list(range(1, 10001))
        xy = neurons.placeholder_xy(ids)
        np.testing.assert_array_equal(xy[[500, 0]], neurons.placeholder_xy([501, 1]))
        self.assertTrue(((xy[:, 0] >= .15) & (xy[:, 0] <= .85)).all())
        self.assertTrue(((xy[:, 1] >= .90) & (xy[:, 1] <= .95)).all())
        self.assertAlmostEqual(float(xy[:, 0].mean()), .5, delta=.003)
        self.assertAlmostEqual(float(xy[:, 0].std()), .08, delta=.003)


if __name__ == '__main__':
    unittest.main()
