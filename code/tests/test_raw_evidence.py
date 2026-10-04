from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from experiments.raw_evidence import inspect_csv,inspect_value,feature_coverage


class RawEvidenceTests(unittest.TestCase):
    def test_different_log_features_are_not_reported_as_numeric_matches(self):
        own=pd.DataFrame({'timestamp':[1],'CPU':[2.],'new pattern':[1.]})
        reference=pd.DataFrame({'timestamp':[1],'CPU':[2.],'old pattern':[1.]})
        rows=feature_coverage(own,reference,{'metric':1,'log':1},{'metric':1,'log':1})
        log=next(row for row in rows if row['modality']=='log')
        self.assertEqual(log['numeric_comparison_status'],'no_shared_features')
        self.assertEqual(log['own_only_columns'],['new pattern'])
        self.assertEqual(log['released_only_columns'],['old pattern'])
        with self.assertRaises(ValueError):feature_coverage(own,reference,{'metric':1},{'metric':1,'log':1})
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
