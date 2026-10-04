import unittest
import json
import numpy as np
from experiments.encoder_downstream import replace_embedding, split_labels


class EncoderReplacementTests(unittest.TestCase):
    def test_numpy_labels_are_losslessly_json_serializable(self):
        labels=np.array([[[0., 1.], [1., 0.]]],dtype=np.float32)
        dataset={'data':{'test':{'y':labels,'y_marker':np.array(['case-1'])}}}
        exported=json.loads(json.dumps(split_labels(dataset)))
        np.testing.assert_array_equal(exported['test']['y'],labels)
        self.assertEqual(exported['test']['y_marker'],['case-1'])

    def test_only_target_entity_embeddings_change(self):
        source={'test':{'day':{'service':{'a':np.zeros((3,2))},'pod':{'b':np.ones((3,2))}}}}
        result=replace_embedding(source,{('test','day','a'):np.full((3,2),2.)},'service')
        np.testing.assert_array_equal(result['test']['day']['pod']['b'],source['test']['day']['pod']['b'])
        self.assertEqual(source['test']['day']['service']['a'].sum(),0)
        self.assertEqual(result['test']['day']['service']['a'].sum(),12)

    def test_missing_coverage_and_nonfinite_are_rejected(self):
        source={'test':{'day':{'service':{'a':np.zeros((3,2))}}}}
        for replacements in ({},{('test','day','a'):np.full((3,2),np.nan)}):
            with self.assertRaises(ValueError): replace_embedding(source,replacements,'service')
