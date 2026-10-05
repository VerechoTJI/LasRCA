import unittest
import tempfile
from pathlib import Path
from experiments.raw_accounting import field_counts,source_consumers


class RawAccountingTests(unittest.TestCase):
    def test_unused_metric_csv_and_out_of_scope_inputs_not_counted_as_script_reads(self):
        config={'file':{'normal':{'date':['day'],'cloud_bed':['cloud']}}}
        settings={'related_metrics':{'container':{'CPU':['used']}}}
        with tempfile.TemporaryDirectory() as tmp:
            record=dict(role='input_normal',path=str(Path(tmp)/'unused.csv'),relative_path='day/cloud/metric/container/unused.csv')
            self.assertEqual(source_consumers(record,config,settings),[])
            record.update(path=str(Path(tmp)/'used.csv'),relative_path='day/cloud/metric/container/used.csv')
            self.assertEqual(source_consumers(record,config,settings),['dao.metric_dao'])
            record['relative_path']='other/cloud/metric/container/used.csv'
            self.assertEqual(source_consumers(record,config,settings),[])
    def test_edges_not_endpoint_count_and_nested_keys_not_observation_totals(self):
        rows=field_counts([dict(field_path='',kind='dict',count=3),
            dict(field_path='/test/edge_index',kind='ndarray',shape=[2,164],count=328)])
        self.assertFalse(rows[0]['aggregate'])
        self.assertEqual((rows[1]['count'],rows[1]['unit']),(164,'stored_directed_edges'))
    def test_windows_and_label_vectors_have_distinct_units(self):
        rows=field_counts([dict(field_path='/time_interval/test',kind='list',count=241),
            dict(field_path='/y/test',kind='list',count=241),
            dict(field_path='/y/test/0',kind='ndarray',shape=[56],count=56)])
        self.assertEqual([r['unit'] for r in rows],['time_windows','label_vectors','entity_label_values'])
        self.assertEqual([r['count'] for r in rows],[241,241,56])
    def test_csv_and_wide_frames_keep_rows_separate_from_cells(self):
        self.assertEqual(field_counts({'rows':2,'non_null_non_timestamp_cells':5})[0]['count'],2)
        rows=field_counts([dict(field_path='/data/test',kind='DataFrame',rows=1440,shape=[1440,9],columns=['timestamp']+list('abcdefgh'))])
        self.assertEqual([r['count'] for r in rows],[1440,11520])
