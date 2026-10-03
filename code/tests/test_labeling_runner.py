import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from llm.run_labeling import ResumingClient, run


class RunnerTests(unittest.TestCase):
    def test_completed_request_is_reused_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = Mock(complete=Mock(return_value='response − 中文'),last_metadata={})
            first = ResumingClient(tmp,api).complete('prompt')
            blocked = Mock(complete=Mock(side_effect=AssertionError('Must not request again')))
            self.assertEqual(ResumingClient(tmp,blocked).complete('prompt'),first)

    def test_failed_request_not_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = ResumingClient(tmp,Mock(complete=Mock(side_effect=RuntimeError('failed'))))
            with self.assertRaises(RuntimeError):
                client.complete('prompt')
            self.assertEqual(list(Path(tmp).glob('*.json')),[])

    def test_four_stages_preserve_unicode_on_windows(self):
        with tempfile.TemporaryDirectory() as tmp, patch('llm.run_labeling.LunaClient',
                return_value=Mock(complete=Mock(return_value='Observation − 中文'),last_metadata={})):
            run(tmp,1)
            statuses = json.loads((Path(tmp)/'status.json').read_text(encoding='utf-8'))
            self.assertEqual(statuses['0']['status'],'completed')
            result = (Path(tmp)/'responses/summarization/0.txt').read_text(encoding='utf-8')
            self.assertEqual(result,'Observation − 中文')
