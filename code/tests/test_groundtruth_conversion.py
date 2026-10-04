import unittest
from experiments.groundtruth_conversion import groundtruth_frame


class GroundtruthConversionTests(unittest.TestCase):
    def test_parallel_fields_and_labels_are_preserved(self):
        source=dict(timestamp=[1,2],level=['pod','node'],cmdb_id=['a','b'],failure_type=['CPU','Disk'])
        self.assertEqual(groundtruth_frame(source).to_dict('list'),source)
    def test_misaligned_lists_are_not_guessed(self):
        with self.assertRaises(ValueError):
            groundtruth_frame(dict(timestamp=[1,2],level=['pod'],cmdb_id=['a'],failure_type=['CPU']))
