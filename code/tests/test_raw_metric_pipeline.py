import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from data_filter.CCF_AIOps_challenge_2022.dao.metric_dao import RawMetricDao


class RawMetricPipelineTests(unittest.TestCase):
    def test_generation_covers_every_resource_required_by_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            dao = RawMetricDao.__new__(RawMetricDao)
            dao.config = SimpleNamespace(
                data_dict={'file': {'normal': {
                    'date': ['2022-03-19'], 'cloud_bed': ['cloudbed-1'],
                    'base_folder': tmp,
                }}}, param_dict={'temp_data_storage': tmp},
            )
            processors = {}
            for resource in ('node', 'container', 'service', 'istio'):
                processors[resource] = Mock()
                setattr(dao, 'process_' + resource + '_metric', processors[resource])
            dao.generate_metric_csv()
            for resource, processor in processors.items():
                with self.subTest(resource=resource):
                    processor.assert_called_once()
                    self.assertEqual(len(processor.call_args.args[0]), 1440)
