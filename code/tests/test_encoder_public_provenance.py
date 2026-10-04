from pathlib import Path
import tempfile
import unittest
import zipfile
from experiments.encoder_public_recheck import inspect_public_inputs


class PublicEncoderProvenanceTests(unittest.TestCase):
    def test_downloaded_input_identity_and_downstream_models_are_distinguished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/'input.pkl'
            source.write_bytes(b'released input')
            with zipfile.ZipFile(root/'temp.zip','w') as archive:
                archive.writestr('temp_data/2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl',b'released input')
            with zipfile.ZipFile(root/'model.zip','w') as archive:
                archive.writestr('model/LasRCA/A/model.pkl',b'classifier')
                archive.writestr('model/fine-tune/A/model.pkl',b'classifier')
            result=inspect_public_inputs(source,root/'temp.zip',root/'model.zip')
            self.assertTrue(result['input_matches_download'])
            self.assertEqual(result['ts2vec_weight_entries'],[])
            source.write_bytes(b'new preprocessing result')
            with self.assertRaises(ValueError):inspect_public_inputs(source,root/'temp.zip',root/'model.zip')
