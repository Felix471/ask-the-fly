# SPDX-License-Identifier: MIT
import json
import unittest
from sim.malecns.mn9_mapping_capture import DATA, render


class MappingCaptureTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads((DATA/'mn9_mapping_capture.json').read_text())

    def test_complete_group(self):
        self.assertEqual(self.d['cross_matched_label'],'CB0701')
        self.assertEqual(self.d['male_body_ids'],[10331,16949])
        self.assertTrue(self.d['16949_in_mapping'])
        self.assertEqual(len(self.d['all_label_members']),4)

    def test_roi_counts_and_unknown(self):
        for n in self.d['bodies']:
            self.assertEqual(n['roiInfo']['GNG']['post']+n['roiInfo']['CentralBrain-unspecified']['post'],n['total_post'])
        rows={r['roi']:r for r in self.d['roi_capture']}
        self.assertIsNone(rows['CentralBrain-unspecified']['capture'])
        self.assertEqual(rows['GNG']['csv_line'],31)
        self.assertAlmostEqual(rows['GNG']['capture']['postsyn_traced_frac'],0.3536645229700866)

    def test_status_and_caveats_present(self):
        text=render()
        for s in ['RT Hard to trace','Roughly traced','35.3665%','32.2026%',
                  'not a one-to-one','not either MN9','not explicitly','no new conclusion']:
            self.assertIn(s,text)


if __name__=='__main__':
    unittest.main()
