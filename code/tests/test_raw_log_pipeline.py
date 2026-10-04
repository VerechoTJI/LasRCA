import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from data_filter.CCF_AIOps_challenge_2022.service.log_generator import LogGenerator


class RawLogPipelineTests(unittest.TestCase):
    def test_word_statistics_accept_directory_created_by_log_dao(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'analysis' / 'log'
            folder.mkdir(parents=True)
            words = folder / 'istio_words.json'
            words.write_text(json.dumps({'word_set': []}), encoding='utf-8')
            generator = LogGenerator.__new__(LogGenerator)
            generator.config = SimpleNamespace(param_dict={'temp_data_storage': tmp}, data_dict={'file': {}})
            generator.load_raw_log = Mock(return_value={})
            generator.calculate_word_tf_idf()
            self.assertEqual(json.loads(words.read_text()), {'word_set': []})
            self.assertEqual(json.loads((folder / 'istio_selected_words.json').read_text()), [])
            generator.load_raw_log.assert_called_once_with('istio')
