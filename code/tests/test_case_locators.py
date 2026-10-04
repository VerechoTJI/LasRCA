import copy
import unittest
import numpy as np
from llm.case_locators import locate_cases


class CaseLocatorTests(unittest.TestCase):
    def setUp(self):
        self.dataset={'data':{'train_valid':{'y':[[0],[1],[1]],'y_marker':['normal','fault','fault'],
            'raw_data':[[np.array([[i]])] for i in range(3)]},
            'unlabeled':{'y':[[1]],'y_marker':['fault'],'raw_data':[[np.array([[2]])]]}}}
        self.gt={'time_interval':{'train_valid':[['day','cloud',i,i+9] for i in range(3)]},
            **{key:{'train_valid':['x']*3} for key in ('cmdb_id','entity_type','root_cause_type')}}

    def test_same_labels_do_not_replace_observation_verification(self):
        self.assertEqual(locate_cases(self.dataset,[0,1],self.gt)[0]['start_timestamp'],2)
        wrong=copy.deepcopy(self.dataset)
        wrong['data']['unlabeled']['raw_data'][0]=[np.array([[1]])]
        with self.assertRaises(ValueError):locate_cases(wrong,[0,1],self.gt)
