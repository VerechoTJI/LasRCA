import copy
import unittest
import json
import tempfile
from pathlib import Path
import numpy as np
from llm.dataset_evidence import distribution,input_signature,save


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
    def test_distribution_separates_new_labels_changes_and_ignored_entities(self):
        before=self.fixture()
        after=copy.deepcopy(before)
        after['data']['unlabeled']['y'][0,0]=1
        after['data']['unlabeled']['y_mask'][0,0]=1
        changes=[dict(entity_index=0,status='applied',mask_before=0,y_before=0,y_after=1),
                 dict(entity_index=1,status='invalid_label',y_before=1)]
        with tempfile.TemporaryDirectory() as tmp:
            save(Path(tmp),before,after,changes)
            rows=json.loads((Path(tmp)/'fault_type_distribution.json').read_text())
        cpu=next(row for row in rows if row['split']=='unlabeled' and row['fault_id']==1)
        self.assertEqual(cpu['newly_labeled_count'],1)
        self.assertEqual(cpu['changed_to_count'],1)
        self.assertEqual(cpu['ignored_at_previous_label_count'],1)
