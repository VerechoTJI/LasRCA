import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch
from torch import nn

from experiments.data_flow import (
    binary_confusion_score,
    describe_modality_coverage,
    summarize_tensor,
    trace_sequential_model,
    validate_edge_index,
    write_data_flow_outputs,
)


class Representation(nn.Module):
    def forward(self, batch):
        batch["x_metric"] = batch["x_metric"] + 1
        batch["x_trace"] = batch["x_trace"] + 2
        batch["x_log"] = batch["x_log"] + 3
        return batch


class Integration(nn.Module):
    def forward(self, batch):
        batch["x_ent"] = torch.cat(
            [
                batch["x_metric"].mean(dim=1, keepdim=True),
                batch["x_trace"].mean(dim=1, keepdim=True),
                batch["x_log"].mean(dim=1, keepdim=True),
            ],
            dim=1,
        )
        return batch


class Fusion(nn.Module):
    def forward(self, batch):
        return batch["x_ent"] * 2


class Classifier(nn.Module):
    def forward(self, entities):
        return {
            "node": entities[:, :1, :].reshape(-1, 2),
            "pod": entities[:, 1:, :].reshape(-1, 2),
        }


class DataFlowTests(unittest.TestCase):
    def test_summarizes_shape_dtype_and_nonfinite_values(self):
        summary = summarize_tensor(
            "example", np.array([[1.0, np.nan], [np.inf, -2.0]])
        )

        self.assertEqual(summary["name"], "example")
        self.assertEqual(summary["shape"], [2, 2])
        self.assertEqual(summary["element_count"], 4)
        self.assertEqual(summary["finite_count"], 2)
        self.assertEqual(summary["nan_count"], 1)
        self.assertEqual(summary["positive_inf_count"], 1)
        self.assertEqual(summary["minimum"], -2.0)
        self.assertEqual(summary["maximum"], 1.0)

    def test_computes_binary_entropy_without_log_zero(self):
        score = binary_confusion_score(np.array([0.0, 0.5, 1.0]))

        self.assertTrue(np.isfinite(score).all())
        self.assertAlmostEqual(score[0], 0.0, places=8)
        self.assertEqual(score[1], 1.0)
        self.assertAlmostEqual(score[2], 0.0, places=8)

    def test_validates_graph_and_reports_structure(self):
        result = validate_edge_index(
            np.array([[0, 1, 1, 2], [1, 1, 1, 0]]), entity_count=3
        )

        self.assertEqual(result["edge_count"], 4)
        self.assertEqual(result["self_loop_count"], 2)
        self.assertEqual(result["duplicate_edge_count"], 1)
        self.assertEqual(result["dangling_edge_count"], 0)

        with self.assertRaisesRegex(ValueError, "outside entity range"):
            validate_edge_index(np.array([[0, 3], [1, 0]]), entity_count=3)

    def test_traces_layers_and_matches_normal_forward(self):
        model = nn.Sequential(
            Representation(), Integration(), Fusion(), Classifier()
        )
        batch = {
            "x_metric": torch.ones((1, 2, 2)),
            "x_trace": torch.ones((1, 1, 2)),
            "x_log": torch.ones((1, 1, 2)),
            "ent_edge_index": torch.tensor([[[0, 1], [1, 0]]]),
        }

        trace = trace_sequential_model(
            model, batch, modal_types=("metric", "trace", "log")
        )

        self.assertEqual(trace["modal_embeddings"]["metric"].shape, (1, 2, 2))
        self.assertEqual(trace["entity_pre_graph"].shape, (1, 3, 2))
        self.assertEqual(trace["entity_post_graph"].shape, (1, 3, 2))
        self.assertEqual(trace["probabilities"]["node"].shape, (1, 2))
        self.assertEqual(trace["confusion_scores"]["pod"].shape, (2, 2))
        self.assertEqual(trace["max_forward_difference"], 0.0)

    def test_describes_structural_missing_modalities(self):
        records = describe_modality_coverage(
            {
                "ent_types": ["node", "pod"],
                "modal_types": ["metric", "trace", "log"],
                "ent_feature_num": {
                    "node": {"metric": 2, "trace": 0, "log": 0},
                    "pod": {"metric": 3, "trace": 1, "log": 2},
                },
            }
        )

        lookup = {
            (record["entity_type"], record["modality"]): record
            for record in records
        }
        self.assertEqual(lookup[("node", "trace")]["status"], "structurally_absent")
        self.assertEqual(lookup[("pod", "log")]["status"], "available")
        self.assertEqual(lookup[("pod", "log")]["feature_count"], 2)

    def test_writes_immutable_data_flow_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "data_flow"
            output.mkdir()
            paths = write_data_flow_outputs(
                output,
                documents={"case.json": {"case_index": 2}},
                tables={
                    "tensor_summary.csv": [
                        {"name": "input", "shape": [1, 2]},
                        {"name": "output", "finite_count": 2},
                    ]
                },
                arrays={"input": np.ones((1, 2))},
                readme="# Evidence\n",
            )

            self.assertEqual(
                {path.name for path in paths.values()},
                {
                    "case.json",
                    "tensor_summary.csv",
                    "data_flow.npz",
                    "README.md",
                    "artifact_manifest.json",
                },
            )
            manifest = json.loads(
                (output / "artifact_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["artifacts"]), 4)
            with self.assertRaises(FileExistsError):
                write_data_flow_outputs(
                    output,
                    documents={},
                    tables={},
                    arrays={},
                    readme="",
                )


if __name__ == "__main__":
    unittest.main()
