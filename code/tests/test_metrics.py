import unittest

import numpy as np

from experiments.metrics import compute_localization_metrics


class LocalizationMetricsTests(unittest.TestCase):
    def test_computes_ac_at_every_rank_and_paper_avg_at_5(self):
        ranked_indices = np.array(
            [
                [0, 1, 2, 3, 4, 5],
                [0, 1, 2, 3, 4, 5],
                [0, 1, 2, 3, 4, 5],
            ]
        )
        truth = np.array(
            [
                [1, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1],
            ]
        )

        metrics = compute_localization_metrics(ranked_indices, truth, max_k=5)

        self.assertAlmostEqual(metrics["AC@1"], 1 / 3)
        self.assertAlmostEqual(metrics["AC@2"], 1 / 3)
        self.assertAlmostEqual(metrics["AC@3"], 2 / 3)
        self.assertAlmostEqual(metrics["AC@4"], 2 / 3)
        self.assertAlmostEqual(metrics["AC@5"], 2 / 3)
        self.assertAlmostEqual(metrics["Avg@5"], 8 / 15)

    def test_rejects_an_empty_evaluation_cohort(self):
        with self.assertRaisesRegex(ValueError, "at least one sample"):
            compute_localization_metrics(
                np.empty((0, 5), dtype=int),
                np.empty((0, 5), dtype=int),
                max_k=5,
            )


if __name__ == "__main__":
    unittest.main()
