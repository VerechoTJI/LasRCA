import unittest
from llm.audit_labels import error_kinds


class AuditKindTests(unittest.TestCase):
    def test_invalid_unknown_is_not_mislabeled_as_false_positive(self):
        self.assertEqual(error_kinds(dict(status='unknown_fault',ground_truth=0,y_after=0)),['unknown_fault'])
        for gt,pred,kind in [(1,0,'missed_fault'),(0,1,'false_positive_fault'),(1,2,'wrong_fault_type')]:
            self.assertIn(kind,error_kinds(dict(status='applied',ground_truth=gt,y_after=pred)))
        self.assertEqual(error_kinds(dict(status='applied',ground_truth=1,y_after=1)),[])
