import unittest
from experiments.retraining_comparison import compare_records


class ComparisonTests(unittest.TestCase):
    def test_pairing_population_std_and_zero_baseline(self):
        before = [dict(seed=s,entity_type='node',ground_truth_sha256='same',**{'AC@1':v}) for s,v in [(405,0),(406,.2)]]
        after = [dict(seed=s,entity_type='node',ground_truth_sha256='same',**{'AC@1':v}) for s,v in [(406,.4),(405,.1)]]
        rows, summary = compare_records(before,after)
        self.assertIsNone(rows[0]['relative_percent'])
        self.assertAlmostEqual(summary[0]['before_std'],.1)
        self.assertAlmostEqual(summary[0]['delta_percentage_points'],15)

    def test_missing_seed_or_changed_ground_truth_rejected(self):
        before = [dict(seed=405,entity_type='node',ground_truth_sha256='a',**{'AC@1':.1})]
        with self.assertRaises(ValueError):
            compare_records(before,[])
        with self.assertRaises(ValueError):
            compare_records(before,[dict(before[0],ground_truth_sha256='b')])
