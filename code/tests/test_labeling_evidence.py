import unittest
from llm.export_evidence import summarize_usage


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
