import unittest

import numpy as np

from experiments.selection import (
    build_candidate_ranking,
    paper_literal_entity_ranking,
    select_repository_case_budget,
)


class SelectionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.meta_data = {
            "ent_names": ["service-0", "pod-0"],
            "ent_types": ["service", "pod"],
            "ent_type_index": {"service": (0, 1), "pod": (1, 2)},
            "ent_fault_type_index": {"service": (0, 2), "pod": (0, 2)},
            "fault_type_list": ["fault-a", "fault-b"],
            "en_fault_type_list": ["Fault A", "Fault B"],
        }

    def test_ranking_masks_labeled_entities_and_breaks_ties_by_indices(self):
        mean_probabilities = np.full((2, 2, 2), 0.5)
        seed_probabilities = np.stack(
            [mean_probabilities, mean_probabilities], axis=0
        )
        y_mask = np.array([[1, 0], [0, 0]])

        records = build_candidate_ranking(
            self.meta_data,
            mean_probabilities,
            y_mask,
            seed_probabilities=seed_probabilities,
            seeds=[405, 406],
        )

        eligible = [record for record in records if record["selection_eligible"]]
        self.assertEqual(
            [
                (
                    record["sample_index"],
                    record["entity_index"],
                    record["fault_type_index"],
                )
                for record in eligible
            ],
            [(0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)],
        )
        self.assertEqual([record["rank"] for record in eligible], list(range(1, 7)))
        self.assertTrue(all(record["probability_seed_405"] == 0.5 for record in records))
        self.assertTrue(
            all(
                not record["selection_eligible"]
                for record in records
                if record["sample_index"] == 0 and record["entity_index"] == 0
            )
        )

    def test_repository_budget_stops_before_the_next_unique_case(self):
        ranking = [
            {"sample_index": 2, "entity_index": 0},
            {"sample_index": 2, "entity_index": 1},
            {"sample_index": 0, "entity_index": 0},
            {"sample_index": 1, "entity_index": 0},
        ]

        selected = select_repository_case_budget(ranking, alpha=2)

        self.assertEqual([record["sample_index"] for record in selected], [2, 2, 0])

    def test_paper_literal_ranking_keeps_one_best_fault_per_case_entity(self):
        ranking = [
            {"sample_index": 0, "entity_index": 0, "fault_type_index": 0, "confusion_score": 0.8},
            {"sample_index": 0, "entity_index": 0, "fault_type_index": 1, "confusion_score": 0.9},
            {"sample_index": 0, "entity_index": 1, "fault_type_index": 0, "confusion_score": 0.7},
        ]

        literal = paper_literal_entity_ranking(ranking, alpha=100)

        self.assertEqual(len(literal), 2)
        self.assertEqual(literal[0]["entity_index"], 0)
        self.assertEqual(literal[0]["fault_type_index"], 1)
        self.assertEqual(literal[0]["paper_entity_rank"], 1)


if __name__ == "__main__":
    unittest.main()
