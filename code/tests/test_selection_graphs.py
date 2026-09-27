import unittest

import numpy as np

from tasks.util import filter_edges_to_entities, get_suspect_unlabeled_samples


class FilterEdgesToEntitiesTests(unittest.TestCase):
    def test_removes_edge_when_target_is_not_selected(self):
        edge_index = np.array([[0, 1, 2], [1, 2, 3]])

        filtered_edges = filter_edges_to_entities(edge_index, [0, 1, 2])

        np.testing.assert_array_equal(filtered_edges, np.array([[0, 1], [1, 2]]))

    def test_returns_empty_two_row_array_when_no_edges_remain(self):
        edge_index = np.array([[0], [3]])

        filtered_edges = filter_edges_to_entities(edge_index, [0, 1, 2])

        self.assertEqual(filtered_edges.shape, (2, 0))

    def test_selected_sample_contains_only_edges_between_selected_entities(self):
        edge_index = np.array([[0, 1, 2], [1, 2, 3]])
        dataset = {
            "meta_data": {
                "en_fault_type_list": ["CPU Load"],
                "ent_names": ["service-0", "pod-0", "pod-1", "pod-2"],
                "ent_type_index": {"service": (0, 1), "pod": (1, 4)},
            },
            "data": {
                "unlabeled": {
                    "y_mask": np.zeros((2, 4, 1)),
                    "y": np.zeros((2, 4, 1)),
                    "ent_edge_index": [edge_index, edge_index],
                    "raw_data": [[None] * 4, [None] * 4],
                    "data": [[None] * 4, [None] * 4],
                }
            },
        }
        probabilities = np.full((2, 4, 1), 0.5)

        samples = get_suspect_unlabeled_samples(
            dataset,
            probabilities,
            neighbor_hop=1,
            max_ent_per_graph=3,
            max_samples=1,
        )

        self.assertEqual(len(samples), 1)
        selected_names = set(samples[0]["ent_names"])
        for source, target in zip(*samples[0]["ent_edges"]):
            self.assertIn(source, selected_names)
            self.assertIn(target, selected_names)

    def test_returns_all_cases_when_case_budget_exceeds_available_cases(self):
        edge_index = np.array([[0], [1]])
        dataset = {
            "meta_data": {
                "en_fault_type_list": ["CPU Load"],
                "ent_names": ["service-0", "pod-0"],
                "ent_type_index": {"service": (0, 1), "pod": (1, 2)},
            },
            "data": {
                "unlabeled": {
                    "y_mask": np.zeros((2, 2, 1)),
                    "y": np.zeros((2, 2, 1)),
                    "ent_edge_index": [edge_index, edge_index],
                    "raw_data": [[None] * 2, [None] * 2],
                    "data": [[None] * 2, [None] * 2],
                }
            },
        }
        probabilities = np.full((2, 2, 1), 0.5)

        samples = get_suspect_unlabeled_samples(
            dataset,
            probabilities,
            neighbor_hop=1,
            max_ent_per_graph=2,
            max_samples=3,
        )

        self.assertEqual(len(samples), 2)


if __name__ == "__main__":
    unittest.main()
