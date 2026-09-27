import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from experiments.selection import (
    audit_selected_samples,
    build_candidate_ranking,
    paper_literal_entity_ranking,
    select_repository_case_budget,
    write_selection_outputs,
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

    def test_audit_counts_oversized_subgraphs_and_dangling_edges(self):
        samples = [
            {
                "sample_index": 7,
                "ent_indices": list(range(11)),
                "ent_names": [f"entity-{index}" for index in range(11)],
                "ent_types": ["pod"] * 11,
                "ent_edges": [["entity-0", "entity-1"], ["entity-1", "missing"]],
            }
        ]

        audit = audit_selected_samples(samples, {7: {0}}, max_entities=10)

        self.assertEqual(audit["summary"]["over_max_entities_count"], 1)
        self.assertEqual(audit["summary"]["dangling_edge_count"], 1)
        self.assertEqual(audit["entities"][0]["selection_origin"], "direct_confusion")

    def test_writer_refuses_nonempty_output_and_emits_reloadable_pickle(self):
        samples = [
            {
                "sample_index": 0,
                "ent_indices": [0, 1],
                "ent_names": ["service-0", "pod-0"],
                "ent_types": ["service", "pod"],
                "ent_edges": [["service-0"], ["pod-0"]],
            }
        ]
        ranking = [
            {
                "rank": 1,
                "sample_index": 0,
                "entity_index": 0,
                "entity_name": "service-0",
                "entity_type": "service",
                "fault_type_index": 0,
                "fault_type_name": "fault-a",
                "fault_type_name_en": "Fault A",
                "mean_probability": 0.5,
                "confusion_score": 1.0,
                "masked_as_labeled": False,
                "selection_eligible": True,
            }
        ]

        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "selection"
            result = write_selection_outputs(
                output,
                selected_samples=samples,
                candidate_ranking=ranking,
                paper_literal_ranking=ranking,
                direct_entities_by_case={0: {0}},
                checkpoint_records=[{"seed": 405, "checkpoint_sha256": "abc"}],
                seed_probabilities=np.full((1, 1, 2, 2), 0.5),
                mean_probabilities=np.full((1, 2, 2), 0.5),
                preprocessing={"zero_iqr_fallback": "std"},
                validation={"status": "passed", "checks": {"test": True}},
                completion={"status": "completed"},
            )

            self.assertTrue((output / "selected_samples_k_0.pkl").is_file())
            self.assertTrue((output / "artifact_manifest.json").is_file())
            self.assertEqual(result["summary"]["dangling_edge_count"], 0)
            with self.assertRaises(FileExistsError):
                write_selection_outputs(
                    output,
                    selected_samples=samples,
                    candidate_ranking=ranking,
                    paper_literal_ranking=ranking,
                    direct_entities_by_case={0: {0}},
                    checkpoint_records=[],
                    seed_probabilities=np.empty((0,)),
                    mean_probabilities=np.empty((0,)),
                    preprocessing={},
                    validation={},
                    completion={},
                )


if __name__ == "__main__":
    unittest.main()
