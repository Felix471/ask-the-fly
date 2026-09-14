# SPDX-License-Identifier: MIT
import unittest
import numpy as np
import pandas as pd
from sim.malecns.diagnose_m1 import density, region, stats, window_counts


class DiagnosisTests(unittest.TestCase):
    def test_region_crossing_is_not_forced(self):
        self.assertEqual(region('descending_neuron'),'crossing')
        self.assertEqual(region('sensory_ascending_tbc'),'crossing')
        self.assertEqual(region('vnc_intrinsic'),'VNC')
        self.assertEqual(region('ol_intrinsic'),'brain')
        self.assertEqual(region('ENS'),'unclassified')

    def test_empty_statistics_not_zero(self):
        self.assertIsNone(stats([]))
        self.assertEqual(stats([0,2])['sd'],1)

    def test_half_open_windows_unique_neurons(self):
        ids=np.array([10,10,20,20,30])
        times=np.array([0,.049,.05,.5,.999])
        labels=pd.Series(['brain','VNC','crossing'],index=[10,20,30])
        a=window_counts(ids,times,labels,0,.05)
        self.assertEqual(a['brain'],dict(spikes=2,neurons=1))
        self.assertEqual(a['VNC']['spikes'],0)
        b=window_counts(ids,times,labels,.5,1)
        self.assertEqual(b['VNC']['spikes'],1)
        self.assertEqual(b['crossing']['neurons'],1)

    def test_weighted_indegree_and_isolates(self):
        # 200 partners of each MN9. Every partner receives 3 synapses;
        # the isolate is included in all-neuron statistics.
        e=pd.DataFrame({'Presynaptic_Index':list(range(200))*2+[200]*200,
                        'Postsynaptic_Index':[200]*200+[201]*200+list(range(200)),
                        'Connectivity':[2]*400+[3]*200})
        d=density(e,np.arange(203),{'contra':200,'ipsi':201})
        self.assertEqual(d['all']['min'],0)
        self.assertEqual(d['all']['mean'],1400/203)
        self.assertEqual(d['mn9_available_pooled']['mean'],3)
        self.assertEqual(d['mn9_available_pooled']['n'],400)
        self.assertEqual(d['neighborhoods']['contra']['partners'][0]['body_id'],0)

    def test_short_neighborhood_is_explicit(self):
        e=pd.DataFrame({'Presynaptic_Index':[0,1], 'Postsynaptic_Index':[2,2], 'Connectivity':[3,7]})
        with self.assertRaisesRegex(ValueError,'Fewer than 200'):
            density(e,np.arange(3),{'contra':2})
        d=density(e,np.arange(3),{'contra':2},require_full=False)
        self.assertEqual(d['neighborhoods']['contra']['selected_partners'],2)


if __name__=='__main__':
    unittest.main()
