import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from experiments.prediction_evidence import save


class PredictionEvidenceTests(unittest.TestCase):
    def test_global_class_ids_and_ranking_preserve_source_arrays(self):
        meta=dict(ent_types=['node','pod'],ent_type_index={'node':[0,1],'pod':[1,2]},
                  ent_fault_type_index={'node':[0,1],'pod':[1,3]},ent_names=['n','p'])
        probs={'node':[[.5]],'pod':[[.2,.9]]}
        truth={'node':[[0]],'pod':[[0,1]]}
        with tempfile.TemporaryDirectory() as tmp:
            save(tmp,probs,truth,meta,seed=405,split='test')
            root=Path(tmp)/'seed_405_test'
            with np.load(root/'predictions.npz') as arrays:
                np.testing.assert_array_equal(arrays['entity_ranking'],[[1,0]])
                np.testing.assert_array_equal(arrays['pod_truth'],[[[0,1]]])
            import csv
            with (root/'entity_predictions.csv').open() as f: rows=list(csv.DictReader(f))
            self.assertEqual(json.loads(rows[0]['predicted_fault_ids']),[])
            self.assertEqual(json.loads(rows[1]['predicted_fault_ids']),[3])
            self.assertEqual(probs['node'],[[.5]])
