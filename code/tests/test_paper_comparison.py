import json
import unittest
from llm.run_labeling import ROOT
from experiments.paper_comparison import compare


class PaperComparisonTests(unittest.TestCase):
    def test_precision_decrease_and_absent_localization_baseline_are_explicit(self):
        reference=json.loads((ROOT/'docs/paper_reference_values.json').read_text())
        summary=[dict(entity_type='service',metric=metric,before_mean=.7,after_mean=.6)
                 for metric in ('micro_precision_score','AC@1')]
        rows=compare(summary,reference)
        self.assertEqual(rows[0]['paper_direction'],'decrease')
        self.assertTrue(rows[0]['same_direction'])
        self.assertIsNone(rows[1]['same_direction'])
        self.assertIsNone(rows[1]['paper_k0'])
