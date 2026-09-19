# SPDX-License-Identifier: MIT
"""Small synthetic anatomy inputs; never load research runs or simulate."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np

from scripts import cache_male_synapse_centroids as centroids
from scripts import export_neuropils_male as rois
from scripts import fetch_malecns_rois as fetch


class Centroids(unittest.TestCase):
    def test_post_priority_all_fallback_and_batch_medians(self):
        import pyarrow as pa
        rows = dict(body_post=[1, 1, 1, 9], body_pre=[2, 1, 2, 9],
                    x_post=[1, 3, 20, 99], y_post=[2, 4, 21, 99], z_post=[3, 5, 22, 99],
                    x_pre=[10, 1000, 30, 99], y_pre=[11, 1000, 31, 99], z_pre=[12, 1000, 32, 99])
        table = pa.table(rows)
        result, count = centroids.scan_batches(iter(table.to_batches(max_chunksize=2)), [1, 2])
        self.assertEqual(count, 4)
        self.assertEqual(result['1'], dict(x=3., y=4., z=5., n_post=3, n_all=4, used='post'))
        self.assertEqual(result['2'], dict(x=20., y=21., z=22., n_post=0, n_all=2, used='all'))
        with self.assertRaisesRegex(ValueError, 'no synaptic sites.*3'):
            centroids.scan_batches(iter(table.to_batches()), [3])


class Meshes(unittest.TestCase):
    def test_synthetic_fetch_export_roundtrip_and_tampering(self):
        names = [c[0] for components in fetch.GROUPS.values() for c in components]
        properties = dict(inline=dict(ids=list(map(str, range(1, len(names)+1))),
            properties=[dict(id='label', type='label', values=names)]))
        vertices = np.array([[8, 16, 0], [24, 16, 0], [24, 32, 8], [8, 32, 8]], dtype='<f4')
        mesh = struct.pack('<I', 4)+vertices.tobytes()+np.array([0, 1, 2, 0, 2, 3], dtype='<u4').tobytes()
        from urllib.parse import unquote
        def download(url):
            path = unquote(url.removeprefix(fetch.BASE))
            if path == 'info':
                return b'{"mesh":"mesh"}'
            if path == 'segment_properties/info':
                return json.dumps(properties).encode()
            if path.endswith(':0'):
                return json.dumps(dict(fragments=[path.removeprefix('mesh/')+':fragment'])).encode()
            return mesh
        frame = dict(axes=['x', 'y'], flip=[True, False], lo=[-4, 0], scale=.1, offset=[.1, .2], voxel_nm=[8, 8])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = fetch.fetch(root, download)
            payload = rois.build(root, frame)
            self.assertEqual(len(payload['groups']), 8)
            self.assertEqual(payload, rois.build(root, frame))
            for group in payload['groups']:
                self.assertEqual(len(group['polygon']), 4)
                self.assertEqual(group['label_at'], [.3, .57] if group['key'] == 'sez' else [.3, .5])
            def forbidden(url):
                self.fail(f'Attempted redownload: {url}')
            fetch.fetch(root, forbidden)
            fragment = manifest['meshes'][names[0]]['fragments'][0]
            path = fetch.local_path(root, 'mesh/'+fragment)
            self.assertIn('%3A', path.name)
            path.write_bytes(mesh+b'bad')
            with self.assertRaisesRegex(ValueError, 'hash/size'):
                rois.build(root, frame)

    def test_legacy_mesh_and_same_frame_projection(self):
        vertices = np.array([[8, 16, 0], [24, 16, 0], [24, 32, 8], [8, 32, 8]], dtype='<f4')
        blob = struct.pack('<I', 4) + vertices.tobytes() + np.array([0, 1, 2, 0, 2, 3], dtype='<u4').tobytes()
        np.testing.assert_array_equal(rois.mesh_vertices(blob), vertices)
        frame = dict(axes=['x', 'y'], flip=[True, False], lo=[-4, 0], scale=.1, offset=[.1, .2], voxel_nm=[8, 8])
        xy = rois.project_vertices(vertices, frame)
        np.testing.assert_allclose(xy, [[.4, .4], [.2, .4], [.2, .6], [.4, .6]])
        for bad in [blob[:3], blob[:-1], struct.pack('<I', 99)+blob[4:], blob[:-4]+struct.pack('<I', 8)]:
            with self.assertRaises(ValueError):
                rois.mesh_vertices(bad)

    def test_fetch_never_redownloads_and_checks_existing_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            def download(url):
                calls.append(url)
                return b'example'
            records = {}
            fetch.fetch_one(root, 'segment_properties/info', records, download)
            fetch.fetch_one(root, 'segment_properties/info', records, download)
            self.assertEqual(len(calls), 1)
            fetch.local_path(root, 'segment_properties/info').write_bytes(b'corrupted')
            with self.assertRaises(ValueError):
                fetch.fetch_one(root, 'segment_properties/info', records, download)
            with self.assertRaises(ValueError):
                fetch.fetch_one(root, '../escape', records, download)

    def test_exact_name_matching_does_not_guess(self):
        groups, missing = fetch.match_groups(['GNG', 'SAD', 'AMMC(L)', 'AMMC(R)', 'PRW', 'AL(L)', 'AL(R)', 'FB', 'EB', 'PB', 'NO'])
        self.assertEqual(groups['sez'], ['GNG', 'SAD', 'AMMC(L)', 'AMMC(R)', 'PRW'])
        self.assertIn('mb_l', missing)
        self.assertNotIn('mb_l', groups)
        self.assertEqual(groups['cx'], ['FB', 'EB', 'PB', 'NO'])


if __name__ == '__main__':
    unittest.main()
