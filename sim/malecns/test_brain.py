import unittest
from copy import deepcopy
import pandas as pd
from sim.malecns import brain_substrate as substrate, brain_phase0 as runner, phase0
from sim.malecns.adapter import load_configuration


class BrainTests(unittest.TestCase):
    def test_cut_keeps_crossing_drops_vnc_ens(self):
        df=pd.DataFrame({'superclass':['cb_intrinsic','ol_intrinsic','ascending_neuron','descending_neuron','sensory_ascending','efferent_descending','vnc_motor','vnc_intrinsic','ENS']})
        self.assertEqual(substrate.brain_mask(df).tolist(),[True]*6+[False]*3)

    def test_exact_two_candidates_and_960_trials(self):
        self.assertEqual(runner.CANDIDATES,('unscaled','density'))
        self.assertEqual(2*sum(c['n_trials'] for c in phase0.conditions()),960)
        with self.assertRaises(ValueError):
            runner.protocol_path('third')

    def test_only_declared_protocol_fields_change(self):
        base,_=load_configuration(verify=False)
        for candidate in runner.CANDIDATES:
            p=runner.expected_protocol(candidate); restored=deepcopy(p)
            restored.pop('brain_provenance')
            for key in ['protocol_version','data_version','connectivity_file','completeness_file','readout']:
                restored[key]=base[key]
            restored['model']['w_syn_mV']=base['model']['w_syn_mV']
            self.assertEqual(restored,base)
            self.assertEqual(p['brain_provenance']['external_kick_mV'],68.75)
            self.assertEqual(p['readout']['primary'],10331)

    def test_density_formula_and_tamper_rejected(self):
        p=runner.expected_protocol('density')
        self.assertEqual(p['model']['w_syn_mV'],0.275/p['brain_provenance']['r_brain'])
        p['model']['f_poi']=249
        with self.assertRaises(ValueError):
            runner.validate('density',p)


if __name__=='__main__':
    unittest.main()
