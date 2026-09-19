"""M1j raw-audit corruption guards and report reproducibility; no simulation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from sim.malecns import audit_m1j as audit, report_m1j as report
from sim.malecns.substrate import ROOT, DATA, file_record


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'trial_00.json'
        self.p=dict(seeds=[20260910],trial=dict(duration_ms=1000),model=dict(dt_ms=.1),
                    readout=dict(primary=720575940660219265,secondary=720575940618238523))
        self.slots=[self.p['readout']['primary'],self.p['readout']['secondary']]
        np.savez(self.path.with_suffix('.npz'),body_id=np.array([self.slots[0],self.slots[1]],dtype=np.int64),
                 time_s=np.array([.05,.1]),poisson_index=np.array([],dtype=np.int32),poisson_time_s=np.array([]))
        self.row=dict(condition='synthetic',trial=0,seed=20260910,whole_network_spikes=2,source_spike_counts=[1,1],
                      L_hz=1.,R_hz=1.,L_latency_ms=50.,R_latency_ms=100.,spikes=file_record(self.path.with_suffix('.npz')))
        self.save(self.row)

    def save(self,row):
        self.path.write_text(json.dumps(row),encoding='utf-8')

    def check(self,rates=None):
        return audit.audit_trial(self.path,dict(id='synthetic'),0,self.p,self.slots,rates or [0,0])

    def test_female_ids_and_counts(self):
        row, evidence=self.check()
        self.assertEqual(row['neurons_fired'],2)
        self.assertEqual(evidence['poisson_event_counts'],[0,0])

    def test_corrupted_trial_fields_rejected(self):
        for key,value in [('L_hz',2.),('R_hz',0.),('L_latency_ms',51.),('R_latency_ms',101.),
                          ('whole_network_spikes',3),('source_spike_counts',[2,0]),('seed',0)]:
            with self.subTest(key=key):
                row=deepcopy(self.row); row[key]=value; self.save(row)
                with self.assertRaisesRegex(ValueError,key): self.check()

    def test_wrong_declared_inputs_rejected(self):
        with self.assertRaises(AssertionError): self.check([120,0])

    def test_corrupted_archive_hash_rejected(self):
        with self.path.with_suffix('.npz').open('ab') as stream: stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError,'spikes'): self.check()

    def test_wrong_readout_mapping_rejected(self):
        self.p['readout']['primary']=10331
        with self.assertRaisesRegex(ValueError,'L_hz'): self.check()


class ReportTests(unittest.TestCase):
    def test_audit_structure(self):
        a=audit.read(DATA/'m1j_runs_audit.json')
        self.assertEqual((a['raw_trials'],a['MN9_neuron_trials'],a['poisson_unit_trials']),(960,1920,113280))
        self.assertEqual(a['m0']['verdict'],'IDENTICAL')
        self.assertEqual((a['m0']['raw_trials'],a['m0']['neurons_compared'],a['m0']['spikes_compared']),(10,88346,5792465))
        self.assertEqual(a['m0']['poisson_unit_trials_compared'],0)
        for brain,units,shared in [('male',108,23),('female',128,32)]:
            r=a['runs'][brain]
            self.assertEqual((r['status'],r['raw_trials'],r['conditions']),('PASS',480,16))
            self.assertEqual(r['poisson_unit_trials'],480*units)
            self.assertEqual(r['AP_identical_shared_unit_trains'],30*shared)
            self.assertEqual(r['AP_silent_non_subset_unit_trials'],30*(units-shared))
            self.assertEqual(r['A200_B0_identical_network_pairs'],30)
            self.assertEqual(len(r['input_trials']),480)
            for t in r['input_trials']:
                self.assertEqual(t['seed'],20260910+t['trial'])
                self.assertEqual(len(t['poisson_event_counts']),units)
                self.assertEqual(sum(t['poisson_event_counts']),t['poisson_events'])
                self.assertTrue(all(count==0 for count,rate in zip(t['poisson_event_counts'],t['declared_rates_hz']) if rate==0))

    def test_report_regeneration(self):
        for path,marker,block in [(report.DOCUMENT,report.MARKER,report.generate()),
                                  (report.LEDGER_DOCUMENT,report.LEDGER,report.ledger())]:
            text=path.read_text(encoding='utf-8')
            tail=marker+text.split(marker,1)[1]
            self.assertTrue(tail.startswith(block))
            self.assertTrue(not tail[len(block):] or tail[len(block):].startswith('\n## '))

    def test_ledger_preserves_all_eight_rows(self):
        text=report.LEDGER_DOCUMENT.read_text(encoding='utf-8')
        old=text.split('## Male line closing ledger — eight variants (2026-09-18)',1)[1].split('\n## ',1)[0]
        oldrows=[x for x in old.splitlines() if x.startswith('| [M1')]
        newrows=[x for x in report.ledger().splitlines() if x.startswith('| [M1')]
        self.assertEqual(newrows[:8],oldrows)
        self.assertEqual(len(newrows),9)

    def test_corrupted_report_rejected_and_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            p=Path(d)/'report.md'
            bad=report.generate().replace('REJECTED','ADOPTED',1)
            p.write_text(bad,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'regeneration'): report.check_or_append(p)
            self.assertEqual(p.read_text(encoding='utf-8'),bad)

    def test_append_idempotence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            p=Path(d)/'report.md'; p.write_text('History\n',encoding='utf-8')
            prefix=p.read_bytes()
            report.check_or_append(p); before=p.read_bytes()
            report.check_or_append(p)
            self.assertEqual(p.read_bytes(),before)
            self.assertTrue(before.startswith(prefix))

    def test_secondary_shape_is_descriptive(self):
        a=audit.read(DATA/'m1j_runs_audit.json')
        self.assertFalse(a['runs']['male']['secondary_shape_gate']['S'])
        self.assertTrue(a['runs']['female']['secondary_shape_gate']['S'])
        for brain in ('male','female'):
            r=audit.read(audit.result_path(brain))
            self.assertEqual(audit.right_shape(r['conditions']),a['runs'][brain]['secondary_shape_gate'])


if __name__=='__main__':
    unittest.main()
