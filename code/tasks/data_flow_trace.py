import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import torch

from experiments.artifacts import sha256_file
from experiments.data_flow import (
    describe_modality_coverage,
    summarize_tensor,
    trace_sequential_model,
    validate_edge_index,
    write_data_flow_outputs,
)
from experiments.raw_provenance import (
    read_archive_json,
    scan_archive_csv,
    source_member_for_metric,
)
from shared_util.seed import init_dl_program, seed_everything
from tasks.dataset import OriginalDataset
from tasks.las_rca import LasRCA


ARCHIVE_ROOT = "初赛评分数据"


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Trace one LasRCA classifier case from raw input to predictions."
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--raw-archive", type=Path, required=True)
    parser.add_argument("--seven-zip", type=Path, required=True)
    parser.add_argument("--split", default="test", choices=("test", "train"))
    parser.add_argument("--case-index", type=int, default=2)
    parser.add_argument("--seed", type=int, default=405)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--max-threads", type=int, default=None)
    parser.add_argument("--output-dir", type=Path)
    return parser


def _model_config(arguments, device):
    return {
        "mode": "evaluate",
        "dataset": "A/metric_trace_log",
        "sample_strategy": "narrow_few_shot",
        "train_size": 200,
        "valid_size": 100,
        "each_train_size": 1,
        "each_valid_size": 1,
        "window_size": 9,
        "strategy": "fix_match",
        "seed": arguments.seed,
        "k": 0,
        "labeling_strategy": "GPT4",
        "gpu": arguments.gpu,
        "max_threads": arguments.max_threads,
        "batch_size": 1,
        "epochs": 500,
        "lr": 0.0001,
        "weight_decay": 0.001,
        "optimizer": "Adam",
        "T": 0.5,
        "alpha": 0.2,
        "mu": 1,
        "orl_te_heads": 2,
        "orl_te_layers": 2,
        "orl_te_in_channels": 256,
        "efi_in_dim": 256,
        "efi_te_heads": 4,
        "efi_te_layers": 2,
        "efi_out_dim": 256,
        "eff_in_dim": 256,
        "eff_GAT_out_channels": 128,
        "eff_GAT_heads": 2,
        "eff_GAT_dropout": 0.1,
        "trace_zero_iqr_fallback": "std",
        "trace_statistics_path": (
            "2022_CCF_AIOps_challenge/analysis/trace/statistic.json"
        ),
        "trace_percentile_clip": "stored-1-99",
        "device": device,
    }


def _data_config(checkpoint):
    return {
        "dataset": "A/metric_trace_log",
        "dataset_path": (
            "2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl"
        ),
        "ground_truth_path": (
            "2022_CCF_AIOps_challenge/dataset/time_interval_and_label/"
            "time_interval_window_size_9.pkl"
        ),
        "model_dir": str(checkpoint.parent),
        "sample_strategy": "narrow_few_shot",
        "train_size": 200,
        "valid_size": 100,
        "each_train_size": 1,
        "each_valid_size": 1,
        "window_size": 9,
    }


def _batched_case(dataset, split, case_index, device):
    item = OriginalDataset(dataset["data"][split])[case_index]
    return {
        key: value.unsqueeze(0).to(device)
        for key, value in item.items()
    }


def _prediction_records(meta_data, trace, root_entity_index, ground_truth_code):
    records = []
    for entity_type in meta_data["ent_types"]:
        entity_start, entity_end = meta_data["ent_type_index"][entity_type]
        fault_start, fault_end = meta_data["ent_fault_type_index"][entity_type]
        probabilities = trace["probabilities"][entity_type]
        confusion = trace["confusion_scores"][entity_type]
        logits = trace["logits"][entity_type]
        expected_shape = (entity_end - entity_start, fault_end - fault_start)
        if probabilities.shape != expected_shape:
            raise ValueError(
                f"unexpected probability shape for {entity_type}: "
                f"{probabilities.shape}, expected {expected_shape}"
            )
        for local_entity, entity_index in enumerate(range(entity_start, entity_end)):
            for local_fault, fault_index in enumerate(range(fault_start, fault_end)):
                records.append(
                    {
                        "entity_index": entity_index,
                        "entity_name": meta_data["ent_names"][entity_index],
                        "entity_type": entity_type,
                        "fault_type_index": fault_index,
                        "fault_type_name": meta_data["fault_type_list"][fault_index],
                        "fault_type_name_en": meta_data["en_fault_type_list"][fault_index],
                        "logit": float(logits[local_entity, local_fault]),
                        "probability": float(
                            probabilities[local_entity, local_fault]
                        ),
                        "confusion_score": float(
                            confusion[local_entity, local_fault]
                        ),
                        "predicted_positive": bool(
                            probabilities[local_entity, local_fault] > 0.5
                        ),
                        "is_root_entity": entity_index == root_entity_index,
                        "is_ground_truth_fault_type": (
                            entity_index == root_entity_index
                            and fault_index == ground_truth_code - 1
                        ),
                    }
                )
    return records


def _member_paths(date, cloud_bed):
    prefix = f"{ARCHIVE_ROOT}/{date}/{cloud_bed}"
    return {
        "prefix": prefix,
        "ground_truth": f"{ARCHIVE_ROOT}/groundtruth/groundtruth-{date}.json",
        "node_metric": f"{prefix}/metric/node/kpi_cloudbed1_metric_0324.csv",
        "service_metric": f"{prefix}/metric/service/metric_service.csv",
        "trace": f"{prefix}/trace/all/trace_jaeger-span.csv",
        "service_log": f"{prefix}/log/all/log_filebeat-testbed-log-service.csv",
        "envoy_log": f"{prefix}/log/all/log_filebeat-testbed-log-envoy.csv",
    }


def _log_member(paths, feature_name):
    envoy_features = {"http2.remote_reset", "UH", "no_healthy_upstream"}
    return paths["envoy_log"] if feature_name in envoy_features else paths["service_log"]


def _feature_lineage(meta_data, paths, root_entity_index):
    records = []
    modal_offsets = {modal_type: 0 for modal_type in meta_data["modal_types"]}
    for entity_type in meta_data["ent_types"]:
        entity_start, entity_end = meta_data["ent_type_index"][entity_type]
        for entity_index in range(entity_start, entity_end):
            for modal_type in meta_data["modal_types"]:
                feature_names = meta_data["o11y_names"][entity_type][modal_type]
                for local_feature, feature_name in enumerate(feature_names):
                    if modal_type == "metric":
                        if entity_type == "node":
                            member = paths["node_metric"]
                            transform = "select timestamp, cmdb_id, and kpi_name"
                        elif entity_type == "service":
                            member = paths["service_metric"]
                            transform = "select timestamp and service protocol row"
                        else:
                            member = source_member_for_metric(paths["prefix"], feature_name)
                            transform = (
                                "select container row containing pod id"
                                if "kpi_container_" in feature_name
                                else "sum Istio rows by source/destination role"
                            )
                    elif modal_type == "trace":
                        member = paths["trace"]
                        transform = "minute bucket; derive upstream/current/downstream intensity or mean duration"
                    else:
                        member = _log_member(paths, feature_name)
                        transform = "minute bucket; count parsed log template or Envoy keyword"
                    records.append(
                        {
                            "modality": modal_type,
                            "tensor_feature_index": modal_offsets[modal_type]
                            + local_feature,
                            "entity_index": entity_index,
                            "entity_name": meta_data["ent_names"][entity_index],
                            "entity_type": entity_type,
                            "entity_feature_index": local_feature,
                            "feature_name": feature_name,
                            "archive_member": member,
                            "transformation": transform,
                            "is_root_entity": entity_index == root_entity_index,
                        }
                    )
                modal_offsets[modal_type] += len(feature_names)
    return records


def _raw_provenance(
    arguments,
    *,
    case,
    root_entity,
    paths,
    feature_lineage,
):
    ground_truth = read_archive_json(
        arguments.seven_zip, arguments.raw_archive, paths["ground_truth"]
    )
    case_index = arguments.case_index
    archive_ground_truth = {
        "array_index": case_index,
        "timestamp": ground_truth["timestamp"][case_index],
        "level": ground_truth["level"][case_index],
        "cmdb_id": ground_truth["cmdb_id"][case_index],
        "failure_type": ground_truth["failure_type"][case_index],
    }
    if archive_ground_truth["cmdb_id"] != root_entity:
        raise ValueError("archive and prepared-dataset root entities differ")
    if not (
        case["window_start_inclusive"]
        <= archive_ground_truth["timestamp"]
        < case["window_end_exclusive"]
    ):
        raise ValueError("archive ground-truth timestamp is outside model window")

    members = sorted({record["archive_member"] for record in feature_lineage})
    ranges = []
    root_records = []
    for member_index, member in enumerate(members, start=1):
        timestamp_divisor = 1000 if member == paths["trace"] else 1
        print(f"raw provenance {member_index}/{len(members)}: {member}", flush=True)
        result = scan_archive_csv(
            arguments.seven_zip,
            arguments.raw_archive,
            member,
            start_timestamp=case["window_start_inclusive"],
            end_timestamp=case["window_end_exclusive"],
            timestamp_divisor=timestamp_divisor,
            root_entity=root_entity,
        )
        ranges.append(
            {
                key: value
                for key, value in result.items()
                if key != "root_records"
            }
        )
        for record in result["root_records"]:
            root_records.append({"member_path": member, **record})

    return (
        {
            "archive_path": str(arguments.raw_archive.resolve()),
            "archive_sha256": sha256_file(arguments.raw_archive),
            "archive_ground_truth_member": paths["ground_truth"],
            "archive_ground_truth": archive_ground_truth,
            "window_semantics": "start inclusive, end exclusive",
            "member_count": len(members),
            "members": members,
        },
        ranges,
        root_records,
    )


def _tensor_outputs(batch, trace):
    arrays = {}
    summaries = []
    for modality in ("metric", "trace", "log"):
        input_name = f"input_{modality}"
        arrays[input_name] = batch[f"x_{modality}"].detach().cpu().numpy()
        summaries.append(summarize_tensor(input_name, arrays[input_name]))
        embedding_name = f"embedding_{modality}"
        arrays[embedding_name] = trace["modal_embeddings"][modality]
        summaries.append(summarize_tensor(embedding_name, arrays[embedding_name]))

    arrays["ent_edge_index"] = batch["ent_edge_index"].detach().cpu().numpy()
    summaries.append(summarize_tensor("ent_edge_index", arrays["ent_edge_index"]))
    arrays["entity_pre_graph"] = trace["entity_pre_graph"]
    arrays["entity_post_graph"] = trace["entity_post_graph"]
    summaries.append(
        summarize_tensor("entity_pre_graph", arrays["entity_pre_graph"])
    )
    summaries.append(
        summarize_tensor("entity_post_graph", arrays["entity_post_graph"])
    )
    for entity_type in trace["logits"]:
        for category in ("logits", "probabilities", "confusion_scores"):
            name = f"{category}_{entity_type}"
            arrays[name] = trace[category][entity_type]
            summaries.append(summarize_tensor(name, arrays[name]))
    return arrays, summaries


def _readme(case, checkpoint, raw_source, validation):
    return f"""# LasRCA single-case data-flow evidence

This immutable package traces one test case through the formal seed-405 small
classifier and links the model inputs back to records inside the AIOps 2022
archive.

## Case

- Prepared split/index: `{case['split']}[{case['case_index']}]`
- Ground truth: `{case['ground_truth_marker']}`
- Root entity: `{case['root_entity_name']}` (index {case['root_entity_index']})
- Model window: `{case['window_start_inclusive']}` inclusive to
  `{case['window_end_exclusive']}` exclusive
- Checkpoint: `{checkpoint}`

## Data flow

`data_flow.npz` contains the complete Metric, Trace, and Log inputs; per-modal
encoder embeddings; entity representations before and after graph fusion;
classifier logits; sigmoid probabilities; and binary-entropy confusion scores.
Human-readable schemas and finite-value checks are in `tensor_summary.*`, while
`predictions.*` maps every output value to its entity and fault type.

## Raw source lineage

- Archive: `{raw_source['archive_path']}`
- Ground truth member: `{raw_source['archive_ground_truth_member']}`
- `raw_source_ranges.*` records CSV ordinals and physical line ranges for the
  complete nine-minute case window.
- `raw_source_rows.*` records exact root-entity rows, including multiline CSV
  physical line spans.
- `feature_lineage.*` maps every model input feature to its archive member and
  transformation rule.

## Declared preprocessing deviation

The traced model input uses the same zero-IQR standard-deviation fallback and
stored 1st/99th percentile clipping as the formal training run. It is not a
paper-faithful preprocessing path.

Validation status: `{validation['status']}`.
"""


def main(argv=None):
    arguments = build_argument_parser().parse_args(argv)
    if not arguments.checkpoint.is_file():
        raise FileNotFoundError(arguments.checkpoint)
    if not arguments.raw_archive.is_file():
        raise FileNotFoundError(arguments.raw_archive)
    if not arguments.seven_zip.is_file():
        raise FileNotFoundError(arguments.seven_zip)

    run_directory = os.environ.get("LASRCA_RUN_DIR")
    output_directory = arguments.output_dir
    if output_directory is None:
        if not run_directory:
            raise ValueError("use --output-dir or execute through the stage runner")
        output_directory = Path(run_directory) / "data_flow"

    seed_everything(arguments.seed)
    device = init_dl_program(arguments.gpu, max_threads=arguments.max_threads)
    model_config = _model_config(arguments, device)
    data_config = _data_config(arguments.checkpoint.resolve())
    las_rca = LasRCA(data_config, model_config)
    state_dict = torch.load(
        arguments.checkpoint, map_location=device, weights_only=True
    )
    las_rca.model.load_state_dict(state_dict)
    las_rca.model.eval()

    split_data = las_rca.dataset["data"][arguments.split]
    if not 0 <= arguments.case_index < len(split_data["y"]):
        raise IndexError("case index is outside the selected split")
    labels = np.asarray(split_data["y"][arguments.case_index])
    root_indices = np.flatnonzero(labels)
    if root_indices.size != 1:
        raise ValueError(f"expected one root entity, got {root_indices.tolist()}")
    root_entity_index = int(root_indices[0])
    ground_truth_code = int(labels[root_entity_index])
    root_entity = las_rca.dataset["meta_data"]["ent_names"][root_entity_index]
    date, cloud_bed, window_start, window_end = las_rca.ground_truth[
        "time_interval"
    ][arguments.split][arguments.case_index]
    case = {
        "split": arguments.split,
        "case_index": arguments.case_index,
        "date": date,
        "cloud_bed": cloud_bed,
        "window_start_inclusive": int(window_start),
        "window_end_exclusive": int(window_end),
        "window_minutes": int((window_end - window_start) / 60),
        "ground_truth_marker": split_data["y_marker"][arguments.case_index],
        "root_entity_index": root_entity_index,
        "root_entity_name": root_entity,
        "ground_truth_code": ground_truth_code,
        "ground_truth_fault_type": las_rca.dataset["meta_data"]["fault_type_list"][
            ground_truth_code - 1
        ],
        "window_start_utc": datetime.fromtimestamp(
            int(window_start), tz=timezone.utc
        ).isoformat(),
        "window_end_utc": datetime.fromtimestamp(
            int(window_end), tz=timezone.utc
        ).isoformat(),
    }

    batch = _batched_case(
        las_rca.dataset, arguments.split, arguments.case_index, device
    )
    trace = trace_sequential_model(
        las_rca.model,
        batch,
        modal_types=tuple(las_rca.dataset["meta_data"]["modal_types"]),
    )
    arrays, tensor_summaries = _tensor_outputs(batch, trace)
    graph = validate_edge_index(
        arrays["ent_edge_index"],
        entity_count=len(las_rca.dataset["meta_data"]["ent_names"]),
    )
    graph["edge_index"] = arrays["ent_edge_index"][0].tolist()
    predictions = _prediction_records(
        las_rca.dataset["meta_data"], trace, root_entity_index, ground_truth_code
    )
    modality_coverage = describe_modality_coverage(las_rca.dataset["meta_data"])
    paths = _member_paths(date, cloud_bed)
    feature_lineage = _feature_lineage(
        las_rca.dataset["meta_data"], paths, root_entity_index
    )
    raw_source, raw_ranges, raw_rows = _raw_provenance(
        arguments,
        case=case,
        root_entity=root_entity,
        paths=paths,
        feature_lineage=feature_lineage,
    )
    fault_timestamp = int(raw_source["archive_ground_truth"]["timestamp"])
    case["fault_timestamp"] = fault_timestamp
    case["fault_timestamp_utc"] = datetime.fromtimestamp(
        fault_timestamp, tz=timezone.utc
    ).isoformat()
    case["fault_timestamp_asia_taipei"] = datetime.fromtimestamp(
        fault_timestamp, tz=timezone.utc
    ).astimezone(timezone(timedelta(hours=8))).isoformat()

    nonfinite = [
        summary["name"]
        for summary in tensor_summaries
        if summary["finite_count"] != summary["element_count"]
    ]
    probability_values = np.concatenate(
        [value.reshape(-1) for value in trace["probabilities"].values()]
    )
    confusion_values = np.concatenate(
        [value.reshape(-1) for value in trace["confusion_scores"].values()]
    )
    validation = {
        "status": "passed",
        "checks": {
            "checkpoint_loaded": True,
            "single_root_entity": True,
            "all_tensors_finite": not nonfinite,
            "normal_and_traced_forward_match": trace[
                "max_forward_difference"
            ]
            == 0.0,
            "graph_indices_in_range": graph["dangling_edge_count"] == 0,
            "probabilities_in_unit_interval": bool(
                np.all((probability_values >= 0) & (probability_values <= 1))
            ),
            "confusion_scores_in_unit_interval": bool(
                np.all((confusion_values >= 0) & (confusion_values <= 1))
            ),
            "raw_ground_truth_matches_prepared_case": True,
            "every_input_feature_has_lineage": len(feature_lineage)
            == sum(
                array.size // array.shape[-1]
                for name, array in arrays.items()
                if name.startswith("input_")
            ),
        },
        "nonfinite_tensors": nonfinite,
        "max_forward_difference": trace["max_forward_difference"],
    }
    if not all(validation["checks"].values()):
        failed = [key for key, value in validation["checks"].items() if not value]
        raise ValueError(f"data-flow validation failed: {failed}")

    base_path = Path(las_rca.base_path)
    schema = {
        "modal_types": las_rca.dataset["meta_data"]["modal_types"],
        "entity_types": las_rca.dataset["meta_data"]["ent_types"],
        "entity_type_index": las_rca.dataset["meta_data"]["ent_type_index"],
        "entity_feature_count": las_rca.dataset["meta_data"]["ent_feature_num"],
        "entity_fault_type_index": las_rca.dataset["meta_data"][
            "ent_fault_type_index"
        ],
        "entity_names": las_rca.dataset["meta_data"]["ent_names"],
        "fault_type_names": las_rca.dataset["meta_data"]["fault_type_list"],
    }
    completion = {
        "status": "completed",
        "completed_at": datetime.now().astimezone().isoformat(),
        "checkpoint_path": str(arguments.checkpoint.resolve()),
        "checkpoint_sha256": sha256_file(arguments.checkpoint),
        "dataset_path": str((base_path / data_config["dataset_path"]).resolve()),
        "dataset_sha256": sha256_file(base_path / data_config["dataset_path"]),
        "ground_truth_path": str(
            (base_path / data_config["ground_truth_path"]).resolve()
        ),
        "ground_truth_sha256": sha256_file(
            base_path / data_config["ground_truth_path"]
        ),
        "trace_statistics_path": str(
            Path(las_rca.trace_preprocessing["statistics_path"]).resolve()
        ),
        "trace_statistics_sha256": sha256_file(
            las_rca.trace_preprocessing["statistics_path"]
        ),
        "preprocessing_deviation": las_rca.trace_preprocessing,
        "tensor_count": len(tensor_summaries),
        "prediction_record_count": len(predictions),
        "feature_lineage_record_count": len(feature_lineage),
        "raw_member_count": len(raw_ranges),
        "root_source_record_count": len(raw_rows),
    }
    documents = {
        "case.json": case,
        "schema.json": schema,
        "tensor_summary.json": tensor_summaries,
        "missing_modality.json": modality_coverage,
        "graph.json": graph,
        "predictions.json": predictions,
        "raw_source_provenance.json": raw_source,
        "validation.json": validation,
        "completion.json": completion,
    }
    tables = {
        "tensor_summary.csv": tensor_summaries,
        "missing_modality.csv": modality_coverage,
        "predictions.csv": predictions,
        "raw_source_ranges.csv": raw_ranges,
        "raw_source_rows.csv": raw_rows,
        "feature_lineage.csv": feature_lineage,
    }
    write_data_flow_outputs(
        output_directory,
        documents=documents,
        tables=tables,
        arrays=arrays,
        readme=_readme(case, arguments.checkpoint.resolve(), raw_source, validation),
    )
    print(Path(output_directory).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
