import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from experiments.artifacts import sha256_file
from experiments.selection import (
    audit_selected_samples,
    build_candidate_ranking,
    paper_literal_entity_ranking,
    ranking_indices,
    select_repository_case_budget,
    write_selection_outputs,
)
from shared_util.seed import init_dl_program, seed_everything
from tasks.las_rca import LasRCA
from tasks.util import (
    get_suspect_unlabeled_samples,
    reverse_probs_to_graph,
)


EXPECTED_SEEDS = [405, 406, 407, 408, 409]


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Run five-checkpoint LasRCA high-confusion selection."
    )
    parser.add_argument("--checkpoint-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--max-threads", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--alpha", type=int, default=100)
    parser.add_argument("--neighbor-hop", type=int, default=2)
    parser.add_argument("--max-entities", type=int, default=10)
    parser.add_argument("--track", default="local-full-trace-stable")
    return parser


def resolve_output_directory(explicit_output):
    if explicit_output is not None:
        return Path(explicit_output)
    run_directory = os.environ.get("LASRCA_RUN_DIR")
    if not run_directory:
        raise ValueError("selection requires --output-dir or LASRCA_RUN_DIR")
    return Path(run_directory) / "selection"


def load_checkpoint_records(manifest_path):
    manifest_path = Path(manifest_path)
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("checkpoint manifest must be a JSON list")
    records = sorted(records, key=lambda record: int(record["seed"]))
    seeds = [int(record["seed"]) for record in records]
    if seeds != EXPECTED_SEEDS:
        raise ValueError(
            f"checkpoint manifest seeds must be {EXPECTED_SEEDS}, got {seeds}"
        )

    normalized = []
    for record in records:
        checkpoint_path = Path(record["checkpoint_path"]).resolve()
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"checkpoint does not exist: {checkpoint_path}")
        actual_sha256 = sha256_file(checkpoint_path)
        expected_sha256 = record.get("checkpoint_sha256", record.get("sha256"))
        if expected_sha256 and expected_sha256 != actual_sha256:
            raise ValueError(f"checkpoint hash mismatch: {checkpoint_path}")
        normalized.append(
            {
                "seed": int(record["seed"]),
                "checkpoint_path": str(checkpoint_path),
                "bytes": checkpoint_path.stat().st_size,
                "checkpoint_sha256": actual_sha256,
                "verified": True,
            }
        )
    return normalized


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
        "seed": EXPECTED_SEEDS[0],
        "k": 0,
        "labeling_strategy": "GPT4",
        "gpu": arguments.gpu,
        "max_threads": arguments.max_threads,
        "batch_size": arguments.batch_size,
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
        "trace_statistics_path": (
            "2022_CCF_AIOps_challenge/analysis/trace/statistic.json"
        ),
        "trace_percentile_clip": "stored-1-99",
        "device": device,
    }


def _data_config(first_checkpoint):
    return {
        "dataset": "A/metric_trace_log",
        "dataset_path": (
            "2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl"
        ),
        "ground_truth_path": (
            "2022_CCF_AIOps_challenge/dataset/time_interval_and_label/"
            "time_interval_window_size_9.pkl"
        ),
        "model_dir": str(Path(first_checkpoint).parent),
        "sample_strategy": "narrow_few_shot",
        "train_size": 200,
        "valid_size": 100,
        "each_train_size": 1,
        "each_valid_size": 1,
        "window_size": 9,
    }


def _predict_checkpoint(las_rca, data_loader, checkpoint_path, device):
    state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
    las_rca.model.load_state_dict(state_dict)
    probabilities = las_rca.predict_probs(data_loader, "unlabeled")
    meta_data = las_rca.dataset["meta_data"]
    return reverse_probs_to_graph(
        probabilities,
        meta_data["ent_types"],
        meta_data["ent_type_index"],
        meta_data["ent_fault_type_index"],
        len(meta_data["fault_type_list"]),
    )


def _git_head(repository_root):
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def main(argv=None):
    arguments = build_argument_parser().parse_args(argv)
    if arguments.alpha <= 0 or arguments.max_entities <= 0:
        raise ValueError("alpha and max-entities must be positive")

    checkpoint_records = load_checkpoint_records(arguments.checkpoint_manifest)
    output_directory = resolve_output_directory(arguments.output_dir)
    device = init_dl_program(arguments.gpu, max_threads=arguments.max_threads)
    seed_everything(EXPECTED_SEEDS[0])
    model_config = _model_config(arguments, device)
    data_config = _data_config(checkpoint_records[0]["checkpoint_path"])
    las_rca = LasRCA(data_config, model_config)
    data_loader = las_rca.mix_up_load_data()

    seed_probabilities = []
    for offset, checkpoint_record in enumerate(checkpoint_records, start=1):
        print(
            f"checkpoint inference {offset}/{len(checkpoint_records)}: "
            f"seed {checkpoint_record['seed']}",
            flush=True,
        )
        seed_probabilities.append(
            _predict_checkpoint(
                las_rca,
                data_loader,
                checkpoint_record["checkpoint_path"],
                device,
            )
        )
    seed_probabilities = np.stack(seed_probabilities, axis=0)
    mean_probabilities = seed_probabilities.mean(axis=0)

    meta_data = las_rca.dataset["meta_data"]
    y_mask = np.asarray(las_rca.dataset["data"]["unlabeled"]["y_mask"])
    candidate_ranking = build_candidate_ranking(
        meta_data,
        mean_probabilities,
        y_mask,
        seed_probabilities=seed_probabilities,
        seeds=EXPECTED_SEEDS,
    )
    repository_prefix = select_repository_case_budget(
        candidate_ranking, alpha=arguments.alpha
    )
    repository_keys = {
        (
            record["sample_index"],
            record["entity_index"],
            record["fault_type_index"],
        )
        for record in repository_prefix
    }
    direct_entities_by_case = {}
    for record in repository_prefix:
        direct_entities_by_case.setdefault(record["sample_index"], set()).add(
            record["entity_index"]
        )
    paper_literal = paper_literal_entity_ranking(
        candidate_ranking, alpha=arguments.alpha
    )
    paper_keys = {
        (record["sample_index"], record["entity_index"])
        for record in paper_literal
    }
    for record in candidate_ranking:
        record_key = (
            record["sample_index"],
            record["entity_index"],
            record["fault_type_index"],
        )
        record["repository_selected_prefix"] = record_key in repository_keys
        record["paper_literal_entity_selected"] = (
            record["sample_index"], record["entity_index"]
        ) in paper_keys

    selected_samples = get_suspect_unlabeled_samples(
        las_rca.dataset,
        mean_probabilities,
        neighbor_hop=arguments.neighbor_hop,
        max_ent_per_graph=arguments.max_entities,
        max_samples=arguments.alpha,
        ranked_index=ranking_indices(candidate_ranking),
    )
    audit = audit_selected_samples(
        selected_samples,
        direct_entities_by_case,
        max_entities=arguments.max_entities,
    )

    base_path = Path(las_rca.base_path)
    dataset_path = (base_path / data_config["dataset_path"]).resolve()
    ground_truth_path = (base_path / data_config["ground_truth_path"]).resolve()
    statistics_path = Path(las_rca.trace_preprocessing["statistics_path"])
    released_selection_path = (
        base_path / "A" / "selected_samples" / "selected_samples_k_0.pkl"
    ).resolve()
    released_selection_sha256 = (
        sha256_file(released_selection_path)
        if released_selection_path.is_file()
        else None
    )

    selected_case_indices = {sample["sample_index"] for sample in selected_samples}
    prefix_case_indices = {record["sample_index"] for record in repository_prefix}
    eligible_cases = {
        record["sample_index"]
        for record in candidate_ranking
        if record["selection_eligible"]
    }
    eligible_entities = {
        (record["sample_index"], record["entity_index"])
        for record in candidate_ranking
        if record["selection_eligible"]
    }
    checks = {
        "five_checkpoint_hashes_verified": all(
            record["verified"] for record in checkpoint_records
        ),
        "seed_probabilities_finite": bool(np.isfinite(seed_probabilities).all()),
        "mean_probabilities_finite": bool(np.isfinite(mean_probabilities).all()),
        "probabilities_in_unit_interval": bool(
            np.all((seed_probabilities >= 0) & (seed_probabilities <= 1))
        ),
        "repository_case_budget_exact": len(selected_case_indices)
        == min(arguments.alpha, len(eligible_cases)),
        "selected_cases_match_rank_prefix": selected_case_indices
        == prefix_case_indices,
        "maximum_ten_entities": audit["summary"]["over_max_entities_count"] == 0,
        "no_dangling_edges": audit["summary"]["dangling_edge_count"] == 0,
        "paper_literal_entity_budget_exact": len(paper_literal)
        == min(arguments.alpha, len(eligible_entities)),
        "released_selection_untouched": (
            not released_selection_path.is_file()
            or sha256_file(released_selection_path) == released_selection_sha256
        ),
    }
    validation = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
    }
    if validation["status"] != "passed":
        raise RuntimeError(f"selection validation failed: {checks}")

    preprocessing = dict(las_rca.trace_preprocessing)
    preprocessing["statistics_sha256"] = sha256_file(statistics_path)
    repository_root = Path(__file__).resolve().parents[2]
    completion = {
        "status": "completed",
        "completed_at": datetime.now().astimezone().isoformat(),
        "source_commit": _git_head(repository_root),
        "run_id": os.environ.get("LASRCA_RUN_ID", "standalone"),
        "environment_id": os.environ.get(
            "LASRCA_ENVIRONMENT_ID", "primary-windows"
        ),
        "track": arguments.track,
        "seeds": EXPECTED_SEEDS,
        "alpha": arguments.alpha,
        "beta_neighbor_hops": arguments.neighbor_hop,
        "n_g_max_entities": arguments.max_entities,
        "ranking_policy": (
            "descending binary entropy of five-seed mean probability over "
            "eligible case-entity-fault candidates"
        ),
        "tie_policy": (
            "sample_index ascending, entity_index ascending, fault_type_index ascending"
        ),
        "repository_selection_unit": "unique case_index",
        "paper_literal_selection_unit": "case-entity occurrence",
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "ground_truth_path": str(ground_truth_path),
        "ground_truth_sha256": sha256_file(ground_truth_path),
        "checkpoint_manifest_path": str(arguments.checkpoint_manifest.resolve()),
        "released_selection_path": str(released_selection_path),
        "released_selection_sha256_before": released_selection_sha256,
        "preprocessing_deviation": {
            "percentile_clip": "stored-1-99",
        },
    }
    write_selection_outputs(
        output_directory,
        selected_samples=selected_samples,
        candidate_ranking=candidate_ranking,
        paper_literal_ranking=paper_literal,
        direct_entities_by_case=direct_entities_by_case,
        checkpoint_records=checkpoint_records,
        seed_probabilities=seed_probabilities,
        mean_probabilities=mean_probabilities,
        preprocessing=preprocessing,
        validation=validation,
        completion=completion,
        max_entities=arguments.max_entities,
    )
    print(output_directory.resolve(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
