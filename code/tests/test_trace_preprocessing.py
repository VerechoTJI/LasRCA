import unittest

import numpy as np

from experiments.trace_preprocessing import (
    apply_stored_percentile_clipping,
    apply_zero_iqr_std_fallback,
)


class TracePreprocessingTests(unittest.TestCase):
    def test_scales_only_features_left_raw_by_zero_iqr(self):
        dataset = {
            "meta_data": {
                "ent_types": ["pod"],
                "ent_names": ["cartservice-0"],
                "ent_type_index": {"pod": [0, 1]},
                "ent_feature_num": {"pod": {"trace": 2}},
                "o11y_names": {
                    "pod": {
                        "trace": [
                            "<duration>; cmdb_id: adservice-0; type: downstream",
                            "<intensity>; cmdb_id: adservice-0; type: current",
                        ]
                    }
                },
            },
            "data": {
                "train": {
                    "x_trace": [
                        np.array([[0.0, 4.0], [1000.0, 8.0], [500.0, 12.0]])
                    ]
                },
                "test": {
                    "x_trace": [
                        np.array([[500.0, 12.0], [0.0, 16.0], [100.0, 20.0]])
                    ]
                },
            },
        }
        statistics = {
            "<duration>; cmdb_id: cartservice; type: downstream": {
                "percentile_1": 0.0,
                "percentile_99": 500.0,
                "q1": 0.0,
                "q3": 0.0,
                "median": 0.0,
                "std": 100.0,
            },
            "<intensity>; cmdb_id: cartservice; type: current": {
                "percentile_1": -2.0,
                "percentile_99": 4.0,
                "q1": 0.0,
                "q3": 2.0,
                "median": 1.0,
                "std": 3.0,
            },
        }

        transformed = apply_zero_iqr_std_fallback(dataset, statistics)

        self.assertEqual(
            transformed,
            ["<duration>; cmdb_id: cartservice; type: downstream"],
        )
        np.testing.assert_allclose(
            dataset["data"]["train"]["x_trace"][0],
            np.array([[0.0, 4.0], [10.0, 8.0], [5.0, 12.0]]),
        )
        np.testing.assert_allclose(
            dataset["data"]["test"]["x_trace"][0],
            np.array([[5.0, 12.0], [0.0, 16.0], [1.0, 20.0]]),
        )

    def test_constant_zero_feature_is_left_unchanged(self):
        dataset = {
            "meta_data": {
                "ent_types": ["pod"],
                "ent_names": ["adservice-0"],
                "ent_type_index": {"pod": [0, 1]},
                "ent_feature_num": {"pod": {"trace": 1}},
                "o11y_names": {
                    "pod": {
                        "trace": [
                            "<duration>; cmdb_id: adservice-0; type: downstream"
                        ]
                    }
                },
            },
            "data": {"train": {"x_trace": [np.zeros((2, 1))]}},
        }
        statistics = {
            "<duration>; cmdb_id: adservice; type: downstream": {
                "percentile_1": 0.0,
                "percentile_99": 0.0,
                "q1": 0.0,
                "q3": 0.0,
                "median": 0.0,
                "std": 0.0,
            }
        }

        self.assertEqual(apply_zero_iqr_std_fallback(dataset, statistics), [])

    def test_clips_preprocessed_values_to_stored_percentiles(self):
        dataset = {
            "meta_data": {
                "ent_types": ["pod"],
                "ent_names": ["cartservice-0"],
                "ent_type_index": {"pod": [0, 1]},
                "ent_feature_num": {"pod": {"trace": 1}},
                "o11y_names": {
                    "pod": {
                        "trace": [
                            "<duration>; cmdb_id: adservice-0; type: upstream"
                        ]
                    }
                },
            },
            "data": {
                "train": {"x_trace": [np.array([[-2.0], [0.0], [2.0]])]}
            },
        }
        statistics = {
            "<duration>; cmdb_id: cartservice; type: upstream": {
                "percentile_1": 5.0,
                "percentile_99": 25.0,
                "q1": 10.0,
                "q3": 20.0,
                "median": 15.0,
                "std": 100.0,
            }
        }

        clipped_values = apply_stored_percentile_clipping(
            dataset, statistics, zero_iqr_fallback="std"
        )

        self.assertEqual(clipped_values, 2)
        np.testing.assert_allclose(
            dataset["data"]["train"]["x_trace"][0],
            np.array([[-1.0], [0.0], [1.0]]),
        )


if __name__ == "__main__":
    unittest.main()
