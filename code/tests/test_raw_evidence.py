from pathlib import Path
import tempfile
import unittest
import numpy as np
from experiments.raw_evidence import inspect_csv,inspect_value


class RawEvidenceTests(unittest.TestCase):
    def test_multiline_log_messages_count_as_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'logs.csv'
            path.write_text('timestamp,message\n1,"first\nsecond"\n2,normal\n',encoding='utf-8')
            result=inspect_csv(path)
            self.assertEqual(result['rows'],2)
            self.assertEqual(result['columns'],['timestamp','message'])
    def test_array_schema_exposes_infinity_and_nan_separately(self):
        schema=inspect_value(np.array([[np.nan,np.inf,3.]]))[0]
        self.assertEqual(schema['shape'],[1,3])
        self.assertEqual((schema['nan_count'],schema['inf_count']),(1,1))
