import unittest
from llm.export_evidence import summarize_usage,api_equivalent_cost


class LabelingEvidenceTests(unittest.TestCase):
    def test_usage_totals_and_missing_are_separate(self):
        requests=[dict(metadata=dict(returned_model='luna',usage=dict(input_tokens=4,output_tokens=3,total_tokens=7))),dict(metadata={})]
        result=summarize_usage(requests)
        self.assertEqual(result['total_tokens'],7)
        self.assertEqual(result['missing_usage'],1)
        self.assertEqual(result['successful_unique_requests'],2)

    def test_incomplete_usage_is_not_silently_zero(self):
        with self.assertRaises(ValueError):
            summarize_usage([dict(metadata=dict(usage=dict(input_tokens=4)))])

    def test_cached_and_long_context_costs_are_explicit_estimates(self):
        request=dict(metadata=dict(usage=dict(input_tokens=300000,output_tokens=100000,
            input_tokens_details=dict(cached_tokens=100000))))
        result=api_equivalent_cost([request])
        self.assertAlmostEqual(result['estimated_api_equivalent_cost'],.117)
        self.assertIsNone(result['actual_oauth_charge'])
