import unittest
import numpy as np
from experiments.encoder_downstream import replace_embedding


class EncoderReplacementTests(unittest.TestCase):
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
