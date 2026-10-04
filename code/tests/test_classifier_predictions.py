import unittest
from experiments.classifier_predictions import matching_metrics
from experiments.evaluation_output import METRIC_FIELDS


class PredictionVerificationTests(unittest.TestCase):
    def test_rounding_tolerance_does_not_hide_changed_metrics(self):
        row=dict(entity_type='node',**{name:.123456 for name in METRIC_FIELDS})
        actual=dict(row,**{'AC@1':.1234564})
        matching_metrics([actual],[row])
        changed=dict(actual,**{'AC@1':.13})
        with self.assertRaises(ValueError):matching_metrics([changed],[row])
