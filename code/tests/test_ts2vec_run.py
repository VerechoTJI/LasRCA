import unittest
import numpy as np
from experiments.ts2vec_run import validate_training_data


class TS2VecRunTests(unittest.TestCase):
    def test_rejects_infinity_and_wrong_dimensions(self):
        for data in [np.zeros((2,3)),np.full((2,3,4),np.inf)]:
            with self.assertRaises(ValueError):
                validate_training_data(data)

    def test_nan_masking_supported_but_wholly_missing_rejected(self):
        x = np.ones((2,3,4))
        x[0,0,0] = np.nan
        self.assertEqual(validate_training_data(x)['nan_count'],1)
        with self.assertRaises(ValueError):
            validate_training_data(np.full((2,3,4),np.nan))
