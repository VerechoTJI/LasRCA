import json
from pathlib import Path
import tempfile
import unittest
from data_filter.CCF_AIOps_challenge_2022.config.dataset_config import DataConfig


class RawConfigTests(unittest.TestCase):
    def test_scope_and_output_override_preserve_metric_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'config.json'
            override = dict(file={'normal':{'base_folder':tmp,'date':['2022-03-19'],'cloud_bed':['cloudbed-1']}},
                ground_truth={'train_valid':tmp,'test':tmp},temp_data_storage=tmp+'/generated')
            path.write_text(json.dumps(override))
            config = DataConfig(path)
            self.assertEqual(config.data_dict['file'],override['file'])
            self.assertEqual(config.param_dict['temp_data_storage'],override['temp_data_storage'])
            self.assertIn('node_order',config.data_dict['setting']['metric'])
