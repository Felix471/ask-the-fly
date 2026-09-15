import unittest
from copy import deepcopy
from sim.malecns import phase0, split
from sim.malecns.adapter import load_configuration


class SplitTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for level in [25,50,100,120,200]:
            rows.append({'id':f'A_s{level}_b0' if level!=120 else 'AP_sugar_120',
                         'sugar_hz':level,'L_mean':level/10,'L_sd':1,
                         'whole_network_spikes':{'min':100,'max':299,'median':150}})
        return rows

    def test_protocol_only_intended_changes(self):
        p=split.expected_protocol(); base,_=load_configuration(verify=False)
        restored=deepcopy(p)
        restored.pop('split_provenance')
        for key in ['protocol_version','readout']:
            restored[key]=base[key]
        restored['model']['w_syn_mV']=base['model']['w_syn_mV']
        self.assertEqual(restored,base)
        self.assertEqual(p['split_provenance']['external_kick_mV'],68.75)
        self.assertAlmostEqual(p['model']['w_syn_mV'],0.14510408910416958)
        self.assertEqual(sum(c['n_trials'] for c in phase0.conditions()),480)

    def test_all_pass(self):
        self.assertTrue(split.shape_gate(self.rows())['S'])

    def test_coverage(self):
        r=self.rows(); r[0]['L_mean']=0
        self.assertTrue(split.shape_gate(r)['S1'])
        r[1]['L_mean']=0
        self.assertFalse(split.shape_gate(r)['S1'])

    def test_pooled_sd_boundary(self):
        r=self.rows(); r[1]['L_mean']=r[0]['L_mean']-1
        self.assertTrue(split.shape_gate(r)['S2'])
        r[1]['L_mean']-=0.00001
        self.assertFalse(split.shape_gate(r)['S2'])

    def test_strict_ratio_and_zero_minimum(self):
        r=self.rows(); r[-1]['whole_network_spikes']['max']=300
        self.assertFalse(split.shape_gate(r)['S3'])
        r[-1]['whole_network_spikes']['min']=0
        self.assertFalse(split.shape_gate(r)['S3'])

    def test_protocol_rejects_tied_or_changed_drive(self):
        p=split.expected_protocol(); p['split_provenance']['external_kick_mV']=36
        with self.assertRaises(ValueError):
            split.validate_protocol(p)


if __name__=='__main__':
    unittest.main()
