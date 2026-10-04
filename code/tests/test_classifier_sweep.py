import json
from pathlib import Path
import tempfile
import unittest
from experiments.classifier_sweep import run


class ClassifierSweepTests(unittest.TestCase):
    def test_existing_seed_cannot_resume_with_changed_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            prepared=root/'input.pkl'
            prepared.write_bytes(b'changed input')
            metrics=root/'run/metrics'
            metrics.mkdir(parents=True)
            (metrics/'training_summary.json').write_text(json.dumps(dict(seed=405,prepared_dataset_sha256='wrong',completed_epochs=500)))
            with self.assertRaisesRegex(ValueError,'input/epoch mismatch'):
                run(root,prepared,0,[405])
