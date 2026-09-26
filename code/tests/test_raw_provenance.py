import io
import unittest

from experiments.raw_provenance import (
    ascii_console_text,
    scan_csv_stream,
    source_member_for_metric,
)


class RawProvenanceTests(unittest.TestCase):
    def test_renders_non_ascii_archive_paths_as_ascii_console_text(self):
        rendered = ascii_console_text("初赛评分数据/2022-05-01")

        rendered.encode("ascii")
        self.assertIn("\\u521d", rendered)

    def test_tracks_csv_ordinals_and_physical_lines_for_multiline_logs(self):
        stream = io.StringIO(
            "log_id,timestamp,cmdb_id,value\n"
            'a,100,recommendationservice-0,"first line\nsecond line"\n'
            "b,105,other-0,plain\n"
            "c,110,recommendationservice-0,last\n"
            "d,120,recommendationservice-0,outside\n"
        )

        result = scan_csv_stream(
            stream,
            start_timestamp=100,
            end_timestamp=120,
            root_entity="recommendationservice-0",
        )

        self.assertEqual(result["case_record_count"], 3)
        self.assertEqual(result["root_record_count"], 2)
        self.assertEqual(result["case_physical_line_ranges"], [[2, 5]])
        self.assertEqual(result["root_physical_line_ranges"], [[2, 3], [5, 5]])
        self.assertEqual(result["root_records"][0]["record_ordinal"], 1)
        self.assertEqual(result["root_records"][0]["physical_line_start"], 2)
        self.assertEqual(result["root_records"][0]["physical_line_end"], 3)
        self.assertEqual(result["root_records"][1]["record_ordinal"], 3)

    def test_applies_timestamp_divisor_for_millisecond_trace_rows(self):
        stream = io.StringIO(
            "timestamp,cmdb_id,duration\n"
            "100000,recommendationservice-0,12\n"
            "119999,other-0,13\n"
            "120000,recommendationservice-0,14\n"
        )

        result = scan_csv_stream(
            stream,
            start_timestamp=100,
            end_timestamp=120,
            timestamp_divisor=1000,
            root_entity="recommendationservice-0",
        )

        self.assertEqual(result["case_record_count"], 2)
        self.assertEqual(result["root_record_count"], 1)
        self.assertEqual(result["minimum_timestamp"], 100000)
        self.assertEqual(result["maximum_timestamp"], 119999)

    def test_maps_model_metric_names_to_archive_members(self):
        prefix = "初赛评分数据/2022-05-01/cloudbed"

        container = source_member_for_metric(
            prefix, "Disk/kpi_container_fs_reads_MB"
        )
        istio = source_member_for_metric(
            prefix, "Network/kpi_istio_requests.source"
        )

        self.assertEqual(
            container,
            prefix + "/metric/container/kpi_container_fs_reads_MB.csv",
        )
        self.assertEqual(
            istio,
            prefix + "/metric/istio/kpi_istio_requests.csv",
        )
        with self.assertRaisesRegex(ValueError, "unsupported metric feature"):
            source_member_for_metric(prefix, "Unknown/value")


if __name__ == "__main__":
    unittest.main()
