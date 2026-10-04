import json
from pathlib import Path
import tempfile
import unittest
from experiments.round_followup import source_pairing


class RoundPairingTests(unittest.TestCase):
    def test_mixed_preprocessing_is_rejected_even_when_gt_and_seeds_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dataset=root/'dataset';dataset.mkdir()
            (dataset/'summary.json').write_text(json.dumps(dict(source_sha256='before',target_sha256='after')))
            (dataset/'input_signature.json').write_text(json.dumps(dict(checks_passed=True,before={'features':'equal'},after={'features':'equal'})))
            dirs=[root/'k0',root/'k1']
            for k,path in enumerate(dirs):
                path.mkdir();completed=[]
                for seed in range(405,410):
                    run=path/str(seed);(run/'metrics').mkdir(parents=True)
                    checkpoint=run/'checkpoint.pkl';checkpoint.write_bytes(b'saved')
                    (run/'metrics/training_summary.json').write_text(json.dumps(dict(
                        prepared_dataset_sha256='before' if k==0 else 'after',ground_truth_sha256='same',
                        trace_preprocessing={'clip':'stored-1-99'},completed_epochs=500)))
                    completed.append(dict(seed=seed,run=str(run),checkpoint=str(checkpoint)))
                (path/'sweep_status.json').write_text(json.dumps(dict(completed=completed)))
            self.assertTrue(source_pairing(*dirs,dataset)['all_pairing_checks_passed'])
            file=dirs[1]/'405/metrics/training_summary.json'
            data=json.loads(file.read_text());data['trace_preprocessing']['clip']='none'
            file.write_text(json.dumps(data))
            with self.assertRaises(ValueError):source_pairing(*dirs,dataset)
