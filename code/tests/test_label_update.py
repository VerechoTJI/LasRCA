import copy
import unittest
import numpy as np
import pickle
import tempfile
from pathlib import Path
from tasks.base import BaseClass
from llm.build_labeled_dataset import update_labels, parse_summary


class UpdateTests(unittest.TestCase):
    def test_explicit_dataset_bypasses_released_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'prepared.pkl'
            path.write_bytes(pickle.dumps({'meta_data':{},'data':{'marker':'isolated'}}))
            instance = object.__new__(BaseClass)
            instance.data_config = {'prepared_dataset_path':path}
            instance.prepare_dataset()
            self.assertEqual(instance.dataset['data']['marker'],'isolated')
    def test_only_selected_unlabeled_labels_change(self):
        dataset = {'meta_data':{'ent_names':['node-1','pod-1'], 'en_fault_type_list':['Node CPU Fault']},
            'data':{'unlabeled':{'y':np.array([[0,1]]),'y_mask':np.array([[0,0]]),'x_metric':np.array([9])},
                    'test':{'y':np.array([[1,0]])}}}
        original = copy.deepcopy(dataset)
        sample = {'sample_index':0,'ent_names':['node-1','pod-1']}
        updated, rows = update_labels(dataset,[sample],{0:{'node-1':{'exact_fault_type':'Node CPU Fault'},
            'pod-1':{'exact_fault_type':['invalid']}}})
        np.testing.assert_array_equal(original['data']['unlabeled']['y'],[[0,1]])
        np.testing.assert_array_equal(updated['data']['unlabeled']['y'],[[1,1]])
        np.testing.assert_array_equal(updated['data']['unlabeled']['y_mask'],[[1,0]])
        np.testing.assert_array_equal(updated['data']['test']['y'],original['data']['test']['y'])
        self.assertEqual([r['status'] for r in rows],['applied','invalid_type'])

    def test_json_surrounded_by_prose_and_apostrophes(self):
        self.assertEqual(parse_summary('Here is JSON: {"pod-1":{"exact_fault_type":"No Fault"}} End.'),
            {'pod-1':{'exact_fault_type':'No Fault'}})
        with self.assertRaises(ValueError):
            parse_summary('No JSON')
