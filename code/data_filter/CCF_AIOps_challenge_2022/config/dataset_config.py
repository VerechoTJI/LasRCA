import os
import json


class DataConfig:
    def __init__(self, config_path=None):
        self.data_dict = dict()
        self.param_dict = dict()

        self.set_data_dict()
        self.set_param_dict()
        config_path = config_path or os.environ.get('LASRCA_PREPROCESS_CONFIG')
        if config_path:
            with open(config_path,encoding='utf-8') as f:
                overrides = json.load(f)
            for name in ('file','ground_truth'):
                if name in overrides:
                    self.data_dict[name] = overrides[name]
            if 'temp_data_storage' in overrides:
                self.param_dict['temp_data_storage'] = overrides['temp_data_storage']

    def set_data_dict(self):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metric_setting.json')) as f:
            metric_setting_dict = json.load(f)

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_knowledge.json')) as f:
            service_knowledge_dict = json.load(f)

        data_base_path = '/workspace/dataset/2022_CCF_AIOps_challenge/'
        self.data_dict = {
            'file': {
                'normal': {
                    'base_folder': data_base_path + 'training_data_normal',
                    'date': ['2022-03-19'],
                    'cloud_bed': ['cloudbed-1', 'cloudbed-2', 'cloudbed-3']
                },
                'train_valid': {
                    'base_folder': data_base_path + 'training_data_with_faults',
                    'date': ['2022-03-20', '2022-03-21', '2022-03-24'],
                    'cloud_bed': ['cloudbed-1', 'cloudbed-2', 'cloudbed-3']
                },
                'test': {
                    'base_folder': data_base_path + 'test_data',
                    'date': ['2022-05-01', '2022-05-03', '2022-05-05', '2022-05-07', '2022-05-09'],
                    'cloud_bed': ['cloudbed'],
                }
            },
            'ground_truth': {
                'train_valid': data_base_path + 'training_data_with_faults/groundtruth',
                'test': data_base_path + 'test_data/groundtruth-csv'
            },
            'setting': {
                'metric': metric_setting_dict,
                'service_knowledge': service_knowledge_dict
            }
        }

    def set_param_dict(self):
        data_base_path = '/workspace/project/working/2024/LasRCA'
        self.param_dict = {
            'logging': {
                'level': 'DEBUG'
            },
            'temp_data_storage': f'{data_base_path}/temp_data/2022_CCF_AIOps_challenge'
        }
