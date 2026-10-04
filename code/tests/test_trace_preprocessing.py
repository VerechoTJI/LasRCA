import unittest

import numpy as np

from experiments.trace_preprocessing import (
    apply_stored_percentile_clipping,
)


class TracePreprocessingTests(unittest.TestCase):


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
            dataset, statistics
        )

        self.assertEqual(clipped_values, 2)
        np.testing.assert_allclose(
            dataset["data"]["train"]["x_trace"][0],
            np.array([[-1.0], [0.0], [1.0]]),
        )

        # Source preprocessing leaves zero-IQR observations in raw coordinates,
        # even with a nonzero median and standard deviation.
        statistics["<duration>; cmdb_id: cartservice; type: upstream"]["q3"] = 10.0
        dataset["data"]["train"]["x_trace"] = [np.array([[-20.0], [15.0], [40.0]])]
        self.assertEqual(apply_stored_percentile_clipping(dataset, statistics), 2)
        np.testing.assert_allclose(
            dataset["data"]["train"]["x_trace"][0],
            np.array([[5.0], [15.0], [25.0]]),
        )


if __name__ == "__main__":
    unittest.main()
