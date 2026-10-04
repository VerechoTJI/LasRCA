import copy
import unittest
import numpy as np
from llm.dataset_evidence import distribution,input_signature


class DatasetEvidenceTests(unittest.TestCase):
    def fixture(self):
        return dict(meta_data=dict(en_fault_type_list=['CPU'],ent_type_index={'node':(0,2)}),
            data=dict(unlabeled=dict(y=np.array([[0,1]]),y_mask=np.array([[0,1]]),x_metric=[np.array([3.])]),
                test=dict(y=np.array([[1,0]]),x_metric=[np.array([4.])])) )
    def test_hidden_ground_truth_not_counted_as_training_label(self):
        rows=distribution(self.fixture())
        self.assertEqual([r['labeled_count'] for r in rows if r['split']=='unlabeled'],[0,1])
    def test_label_update_allowed_but_feature_or_test_change_detected(self):
        before=self.fixture()
        after=copy.deepcopy(before)
        after['data']['unlabeled']['y'][0,0]=1
        self.assertEqual(input_signature(before),input_signature(after))
        after['data']['test']['y'][0,0]=0
        self.assertNotEqual(input_signature(before),input_signature(after))
