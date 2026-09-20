import os
import sys
import time
from pathlib import Path

sys.path.append("E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/code")

from experiments.artifacts import sha256_file
from experiments.checkpoints import (
    checkpoint_path,
    ensure_checkpoint_target_available,
    resolve_checkpoint_directory,
)
from experiments.evaluation_output import (
    build_metric_records,
    resolve_metrics_output_directory,
    summarize_metric_records,
    write_evaluation_outputs,
)
from experiments.training_output import (
    ensure_training_output_available,
    make_epoch_record,
    write_training_outputs,
)
from tasks.base import *
import argparse
from shared_util.seed import *
from tasks.dataset import *
from tasks.util import *
from torch.utils.data import DataLoader
from llm.util import *
from pprint import pprint


class LasRCA(BaseClass):
    def __init__(self, data_config, model_config):
        super().__init__(data_config, model_config)

    def mix_up_load_data(self):
        data_loader = dict()
        for dataset_type in self.dataset["data"].keys():
            self.dataset["data"][dataset_type]["y"] = label_to_multi_class_format(
                self.dataset["data"][dataset_type]["y"],
                num_of_fault_types=len(self.dataset["meta_data"]["fault_type_list"]),
            )
            if dataset_type == "valid" or dataset_type == "test":
                data_loader[dataset_type] = DataLoader(
                    OriginalDataset(self.dataset["data"][dataset_type]),
                    batch_size=self.model_config["batch_size"],
                    shuffle=False,
                )
            elif dataset_type == "train":
                data_loader[dataset_type] = DataLoader(
                    OriginalDataset(self.dataset["data"][dataset_type]),
                    batch_size=self.model_config["batch_size"],
                    shuffle=True,
                )
            elif dataset_type == "unlabeled":
                new_labeled_samples = np.any(
                    self.dataset["data"]["unlabeled"]["y_mask"], axis=1
                )
                if not np.any(new_labeled_samples):
                    data_loader["iter_labeled"] = None
                else:
                    new_labeled_data = dict()
                    for key, value in self.dataset["data"]["unlabeled"].items():
                        if (
                            "x_" in key
                            or key == "y"
                            or key == "y_mask"
                            or key == "y_true"
                            or key == "ent_edge_index"
                        ):
                            new_labeled_data[key] = np.array(value)[new_labeled_samples]
                    data_loader["iter_labeled"] = DataLoader(
                        UnlabeledDataset(new_labeled_data),
                        batch_size=self.model_config["batch_size"],
                        shuffle=True,
                    )
                data_loader[dataset_type] = DataLoader(
                    UnlabeledDataset(self.dataset["data"][dataset_type]),
                    batch_size=self.model_config["batch_size"],
                    shuffle=False,
                )
        return data_loader

    def mix_up_train(self, data_loader):
        """
        采用MixUp方法进行训练.
        :param data_loader:
        :return:
        """
        self.training_history = []
        training_started = time.monotonic()
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats(self.model_config["device"])

        labeled_train_iter = iter(data_loader["train"])
        iter_labeled_train_iter = data_loader["iter_labeled"]
        if iter_labeled_train_iter is not None:
            iter_labeled_train_iter = iter(data_loader["iter_labeled"])

        for epoch in range(self.model_config["epochs"]):
            epoch_started = time.monotonic()
            learning_rate = self.optimizer.param_groups[0]["lr"]
            self.model.train()
            train_loss, train_loss_x, train_loss_i = 0, 0, 0
            for batch_id in range(len(data_loader["train"])):
                self.optimizer.zero_grad()
                ent_index_dict = dict()
                for ent_type, index_pair in self.dataset["meta_data"][
                    "ent_type_index"
                ].items():
                    ent_index_dict[ent_type] = index_pair[1] - index_pair[0]

                """
                Load labeled dataset.
                """
                try:
                    labeled_batch_data = next(labeled_train_iter)
                except:
                    labeled_train_iter = iter(data_loader["train"])
                    labeled_batch_data = next(labeled_train_iter)
                labeled_batch_size = labeled_batch_data["y"].size(0)
                y_l_dict = rearrange_y(
                    self.dataset["meta_data"],
                    labeled_batch_data["y"],
                    self.model_config["device"],
                )

                """
                Load iteratively labeled dataset and predicted labels.
                """
                iter_labeled_batch_data, iter_labeled_batch_size, y_i_dict = (
                    ...,
                    ...,
                    ...,
                )
                if iter_labeled_train_iter is not None:
                    try:
                        iter_labeled_batch_data = next(iter_labeled_train_iter)
                    except:
                        iter_labeled_train_iter = iter(data_loader["iter_labeled"])
                        iter_labeled_batch_data = next(iter_labeled_train_iter)
                    iter_labeled_batch_size = iter_labeled_batch_data[
                        "ent_edge_index"
                    ].size(0)
                    if iter_labeled_train_iter is not None:
                        y_i_dict = rearrange_y(
                            self.dataset["meta_data"],
                            iter_labeled_batch_data["y"],
                            self.model_config["device"],
                        )

                mask_dict = dict()
                for ent_type in self.dataset["meta_data"]["ent_types"]:
                    y_l_dict[ent_type] = y_l_dict[ent_type].view(
                        labeled_batch_size, -1, y_l_dict[ent_type].shape[1]
                    )

                    if iter_labeled_train_iter is not None:
                        y_i_dict[ent_type] = y_i_dict[ent_type].view(
                            iter_labeled_batch_size, -1, y_i_dict[ent_type].shape[1]
                        )
                        temp = iter_labeled_batch_data["y_mask"][
                            :,
                            self.dataset["meta_data"]["ent_type_index"][ent_type][
                                0
                            ] : self.dataset["meta_data"]["ent_type_index"][ent_type][
                                1
                            ],
                        ]
                        mask_dict[ent_type] = (
                            temp.reshape(temp.shape[0] * temp.shape[1], 1)
                            .contiguous()
                            .to(device)
                        )

                mix_x, mix_y = mix_up(
                    labeled_batch_data,
                    y_l_dict,
                    alpha=self.model_config["alpha"],
                    pseudo=False,
                )

                """
                Labeled loss calculation.
                """
                mix_pred = self.model(mix_x)
                mix_pred = {
                    ent_type: value.view(-1, ent_index_dict[ent_type], value.size(1))
                    for ent_type, value in mix_pred.items()
                }

                i_pred = ...
                if iter_labeled_train_iter is not None:
                    i_pred = self.model(iter_labeled_batch_data)
                    i_pred = {
                        ent_type: value.view(
                            -1, ent_index_dict[ent_type], value.size(1)
                        )
                        for ent_type, value in i_pred.items()
                    }

                loss, loss_x, loss_i = 0, 0, 0
                for ent_type in self.dataset["meta_data"]["ent_types"]:
                    # L_x
                    temp_loss = self.criterion[ent_type](
                        mix_pred[ent_type].view(-1, mix_pred[ent_type].shape[2]),
                        mix_y[ent_type].view(-1, mix_y[ent_type].shape[2]),
                    )
                    loss_x += temp_loss

                    # L_u
                    if iter_labeled_train_iter is not None:
                        temp_loss = (
                            self.u_criterion[ent_type](
                                i_pred[ent_type].view(-1, i_pred[ent_type].shape[2]),
                                y_i_dict[ent_type].view(
                                    -1, y_i_dict[ent_type].shape[2]
                                ),
                            )
                            * mask_dict[ent_type]
                        ).mean()
                        loss_i += temp_loss

                loss = loss_x + loss_i
                train_loss += loss.item()
                train_loss_x += loss_x
                train_loss_i += loss_i

                loss.backward()
                self.optimizer.step()
            self.scheduler.step()
            labeled_loss = (
                train_loss_x.detach().cpu().item()
                if torch.is_tensor(train_loss_x)
                else float(train_loss_x)
            )
            iterative_loss = (
                train_loss_i.detach().cpu().item()
                if torch.is_tensor(train_loss_i)
                else float(train_loss_i)
            )
            self.training_history.append(
                make_epoch_record(
                    epoch=epoch,
                    total_loss=train_loss,
                    labeled_loss=labeled_loss,
                    iterative_loss=iterative_loss,
                    learning_rate=learning_rate,
                    duration_seconds=time.monotonic() - epoch_started,
                )
            )
            logger.info(
                f'[{epoch}/{self.model_config["epochs"]}] | train_loss: {train_loss:.5f}, train_loss_x: {train_loss_x:.5f}, train_loss_i: {train_loss_i:.5f}'
            )
        self.evaluate_las_fault_localization(data_loader, "test")
        self.evaluate_las_fault_classification(data_loader, "test")
        output_checkpoint = checkpoint_path(
            self.data_config["model_dir"],
            seed=self.model_config["seed"],
            k=self.model_config["k"],
            labeling_strategy=self.model_config["labeling_strategy"],
        )
        ensure_checkpoint_target_available(output_checkpoint)
        torch.save(self.model.state_dict(), output_checkpoint)
        self.training_checkpoint_path = output_checkpoint
        self.training_duration_seconds = time.monotonic() - training_started
        self.peak_gpu_memory_bytes = (
            int(torch.cuda.max_memory_allocated(self.model_config["device"]))
            if torch.cuda.is_available()
            else 0
        )

    def mean_evaluate_data_loader(self):
        mean_unlabeled_probs = None
        for seed in [405, 406, 407, 408, 409]:
            self.prepare_dataset()
            data_loader = self.mix_up_load_data()

            if self.model_config["k"] != 0:
                self.model.load_state_dict(
                    torch.load(
                        f'{self.data_config["model_dir"]}/model_seed_{seed}_k_{self.model_config["k"]}_{self.model_config["labeling_strategy"]}.pkl'
                    )
                )
            else:
                self.model.load_state_dict(
                    torch.load(
                        f'{self.data_config["model_dir"]}/model_seed_{seed}_k_{self.model_config["k"]}.pkl'
                    )
                )
            meta_data = self.dataset["meta_data"]

            unlabeled_probs = self.predict_probs(data_loader, "unlabeled")
            unlabeled_probs = reverse_probs_to_graph(
                unlabeled_probs,
                meta_data["ent_types"],
                meta_data["ent_type_index"],
                meta_data["ent_fault_type_index"],
                len(meta_data["fault_type_list"]),
            )
            if mean_unlabeled_probs is None:
                mean_unlabeled_probs = unlabeled_probs
            else:
                mean_unlabeled_probs += unlabeled_probs
        mean_unlabeled_probs /= 5
        samples = get_suspect_unlabeled_samples(
            self.dataset, probs=mean_unlabeled_probs
        )
        # prepare_a_fault_type_infer_examples(fault_example_dict=get_fault_examples(self.dataset, probs=mean_unlabeled_probs))
        selected_samples_save_path = "E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/temp_data/A/selected_samples"
        os.makedirs(selected_samples_save_path, exist_ok=True)
        pkl_save(
            f'{selected_samples_save_path}/selected_samples_k_{self.model_config["k"]}.pkl',
            samples,
        )
        get_fault_labeling_prompts(self.model_config["k"])

    def prepare_prompts(self):
        for dataset_type in ["train_valid", "test", "unlabeled"]:
            get_all_samples(self.dataset, dataset_type)
            all_prompt_save_path = (
                "E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/temp_data/A/prompt"
            )
            sample_list = pkl_load(
                f"{all_prompt_save_path}/all_{dataset_type}_samples.pkl"
            )
            get_all_prompt_template(sample_list, dataset_type)

    def train(self):
        data_loader = self.mix_up_load_data()
        self.mix_up_train(data_loader)

    def explanation(self):
        self.prepare_dataset()
        data_loader = dict()
        for data_type in ["train", "test"]:
            self.dataset["data"][data_type]["y"] = label_to_multi_class_format(
                self.dataset["data"][data_type]["y"],
                num_of_fault_types=len(self.dataset["meta_data"]["fault_type_list"]),
            )
            data_loader[data_type] = DataLoader(
                OriginalDataset(self.dataset["data"][data_type]),
                batch_size=self.model_config["batch_size"],
                shuffle=False,
            )

        if self.model_config["k"] != 0:
            self.model.load_state_dict(
                torch.load(
                    f'{self.data_config["model_dir"]}/model_seed_{self.model_config["seed"]}_k_{self.model_config["k"]}_{self.model_config["labeling_strategy"]}.pkl'
                )
            )
        else:
            self.model.load_state_dict(
                torch.load(
                    f'{self.data_config["model_dir"]}/model_seed_{self.model_config["seed"]}_k_{self.model_config["k"]}.pkl'
                )
            )
        meta_data = self.dataset["meta_data"]

        train_probs = self.predict_probs(data_loader, "train")
        train_probs = reverse_probs_to_graph(
            train_probs,
            meta_data["ent_types"],
            meta_data["ent_type_index"],
            meta_data["ent_fault_type_index"],
            len(meta_data["fault_type_list"]),
        )
        explanation_examples = prepare_explanation_examples(
            fault_example_dict=get_fault_examples(self.dataset, probs=train_probs)
        )

        test_probs = self.predict_probs(data_loader, "test")
        test_probs = reverse_probs_to_graph(
            test_probs,
            meta_data["ent_types"],
            meta_data["ent_type_index"],
            meta_data["ent_fault_type_index"],
            len(meta_data["fault_type_list"]),
        )
        get_explanation_prompts(
            self.dataset, test_probs, explanation_examples, self.model_config["k"]
        )

    def final_test(self):
        data_loader = self.mix_up_load_data()
        input_checkpoint = checkpoint_path(
            self.data_config["model_dir"],
            seed=self.model_config["seed"],
            k=self.model_config["k"],
            labeling_strategy=self.model_config["labeling_strategy"],
        )
        self.model.load_state_dict(torch.load(input_checkpoint))
        self.evaluate_las_fault_localization(data_loader, "test")
        self.evaluate_las_fault_classification(data_loader, "test")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    window_size = 9
    parser.add_argument(
        "--mode", choices=("evaluate", "train"), default="evaluate"
    )
    parser.add_argument("--dataset", default="A/metric_trace_log")
    parser.add_argument(
        "--dataset_path",
        default="2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl",
    )
    parser.add_argument(
        "--ground_truth_path",
        default=f"2022_CCF_AIOps_challenge/dataset/time_interval_and_label/time_interval_window_size_{window_size}.pkl",
    )

    parser.add_argument(
        "--sample_strategy",
        default="narrow_few_shot",
        help="random or narrow_few_shot or broad_few_shot",
    )
    parser.add_argument("--train_size", type=int, default=200)
    parser.add_argument("--valid_size", type=int, default=100)
    parser.add_argument("--each_train_size", type=int, default=1)
    parser.add_argument("--each_valid_size", type=int, default=1)
    parser.add_argument("--window_size", default=window_size)

    parser.add_argument("--strategy", type=str, default="fix_match")

    parser.add_argument(
        "--seed", type=int, default=409, help="Random seed for deterministic"
    )
    parser.add_argument(
        "--eval_seeds",
        type=int,
        nargs="+",
        default=[405, 406, 407, 408, 409],
        help="Checkpoint seeds evaluated in evaluate mode.",
    )
    parser.add_argument("--k", type=int, default=1, help="The k-th retraining.")
    parser.add_argument(
        "--labeling_strategy", type=str, default="GPT4", help="random_labeling_24"
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=0,
        help="The gpu no. used for training and inference (defaults to 0)",
    )
    parser.add_argument(
        "--max_threads",
        type=int,
        default=None,
        help="The maximum allowed number of threads used by this process",
    )
    parser.add_argument(
        "--metrics_output_dir",
        type=Path,
        default=None,
        help="Write structured evaluation metrics here; existing files are never overwritten.",
    )
    parser.add_argument(
        "--track",
        default="released-artifact",
        help="Provenance label for the evaluated checkpoints.",
    )
    parser.add_argument(
        "--environment_id",
        default="primary-windows",
        help="Execution environment identifier recorded with metrics.",
    )
    parser.add_argument(
        "--checkpoint_dir",
        type=Path,
        default=None,
        help="Checkpoint input/output directory. Training may not target released models.",
    )
    parser.add_argument(
        "--batch_size", type=int, default=32, help="The batch size (defaults to 8)"
    )

    parser.add_argument("--epochs", type=int, default=500, help="The number of epochs")
    parser.add_argument("--lr", default=0.0001, type=float)
    parser.add_argument("--weight_decay", default=0.001, type=float)

    # MixUp params
    parser.add_argument("--optimizer", default="Adam", help="Adam or SGD")
    parser.add_argument("--T", default=0.5, help="Sharpening Temperature")
    parser.add_argument(
        "--alpha", type=float, default=0.2, help="MixUp beta hyperparameter"
    )
    parser.add_argument(
        "--mu",
        type=float,
        default=1,
        help="Unlabeled batch size ratio, 1 for MixMatch and 7 for FixMatch",
    )

    # O11y representation learning params
    parser.add_argument("--orl_te_heads", default=2, type=int)
    parser.add_argument("--orl_te_layers", default=2, type=int)
    parser.add_argument("--orl_te_in_channels", default=256, type=int)

    # RE feature integration params
    parser.add_argument("--efi_in_dim", default=256, type=int)
    parser.add_argument("--efi_te_heads", default=4, type=int)
    parser.add_argument("--efi_te_layers", default=2, type=int)
    parser.add_argument("--efi_out_dim", default=64 * 4, type=int)

    # RE feature fusion params
    parser.add_argument("--eff_in_dim", default=64 * 4, type=int)
    parser.add_argument("--eff_GAT_out_channels", default=128, type=int)
    parser.add_argument("--eff_GAT_heads", default=2, type=int)
    parser.add_argument("--eff_GAT_dropout", default=0.1, type=float)

    args = parser.parse_args()

    device = init_dl_program(args.gpu, max_threads=args.max_threads)

    args = vars(args)

    seed_everything(seed=args["seed"])
    args["device"] = device
    released_model_dir = Path(
        f'E:/Misc/FastCodingWorkspace/AI/SMCI/LasRCA/LasRCA/model/LasRCA/{args["dataset"]}'
    )
    model_dir = resolve_checkpoint_directory(
        args["mode"], released_model_dir, args["checkpoint_dir"], os.environ
    )
    if args["mode"] == "train":
        model_dir.mkdir(parents=True, exist_ok=True)
        ensure_checkpoint_target_available(
            checkpoint_path(
                model_dir,
                seed=args["seed"],
                k=args["k"],
                labeling_strategy=args["labeling_strategy"],
            )
        )
    elif not model_dir.is_dir():
        raise FileNotFoundError(f"checkpoint directory does not exist: {model_dir}")
    test_data_config = {
        "dataset": f'{args["dataset"]}',
        "dataset_path": f'{args["dataset_path"]}',
        "ground_truth_path": f'{args["ground_truth_path"]}',
        "model_dir": str(model_dir),
        "sample_strategy": args["sample_strategy"],
        "train_size": args["train_size"],
        "valid_size": args["valid_size"],
        "each_train_size": args["each_train_size"],
        "each_valid_size": args["each_valid_size"],
        "window_size": args["window_size"],
    }
    if args["mode"] == "train":
        training_metrics_directory = resolve_metrics_output_directory(
            args["metrics_output_dir"], os.environ
        )
        if training_metrics_directory is None:
            raise ValueError(
                "training requires a run-scoped metrics directory; use the stage "
                "runner or --metrics_output_dir"
            )
        ensure_training_output_available(training_metrics_directory)
        las_rca = LasRCA(test_data_config, args)
        las_rca.train()
        data_base_path = Path(las_rca.base_path)
        dataset_path = (data_base_path / args["dataset_path"]).resolve()
        ground_truth_path = (data_base_path / args["ground_truth_path"]).resolve()
        training_summary = {
            "environment_id": os.environ.get(
                "LASRCA_ENVIRONMENT_ID", args["environment_id"]
            ),
            "run_id": os.environ.get("LASRCA_RUN_ID", "standalone"),
            "dataset": args["dataset"],
            "track": args["track"],
            "strategy": "one-shot-k0"
            if args["k"] == 0
            else f'{args["labeling_strategy"]}-k{args["k"]}',
            "seed": args["seed"],
            "requested_epochs": args["epochs"],
            "completed_epochs": len(las_rca.training_history),
            "duration_seconds": las_rca.training_duration_seconds,
            "peak_gpu_memory_bytes": las_rca.peak_gpu_memory_bytes,
            "checkpoint_path": str(las_rca.training_checkpoint_path.resolve()),
            "checkpoint_sha256": sha256_file(las_rca.training_checkpoint_path),
            "dataset_path": str(dataset_path),
            "dataset_sha256": sha256_file(dataset_path),
            "ground_truth_path": str(ground_truth_path),
            "ground_truth_sha256": sha256_file(ground_truth_path),
            "localization": las_rca.fl_result,
            "classification": las_rca.fc_result,
        }
        write_training_outputs(
            training_metrics_directory,
            las_rca.training_history,
            training_summary,
        )
        print(f"training checkpoint: {las_rca.training_checkpoint_path.resolve()}")
        print(f"structured metrics: {training_metrics_directory.resolve()}")
        raise SystemExit(0)

    final_dict = dict()
    seed_results = []
    for seed in args["eval_seeds"]:
        args["seed"] = seed
        fault_type_classification = LasRCA(test_data_config, args)
        fault_type_classification.final_test()
        seed_checkpoint_path = checkpoint_path(
            model_dir,
            seed=seed,
            k=args["k"],
            labeling_strategy=args["labeling_strategy"],
        )
        seed_results.append(
            {
                "seed": seed,
                "checkpoint_path": str(seed_checkpoint_path.resolve()),
                "checkpoint_sha256": sha256_file(seed_checkpoint_path),
                "localization": fault_type_classification.fl_result,
                "classification": fault_type_classification.fc_result,
            }
        )
        for result in [
            fault_type_classification.fl_result,
            fault_type_classification.fc_result,
        ]:
            for ent_type in result.keys():
                if ent_type not in final_dict.keys():
                    final_dict[ent_type] = dict()
                for em in result[ent_type].keys():
                    if (
                        em == "precision_score"
                        or em == "recall_score"
                        or em == "f1_score"
                    ):
                        continue
                    if em not in final_dict[ent_type].keys():
                        final_dict[ent_type][em] = []
                    temp = result[ent_type][em]
                    while isinstance(temp, list):
                        temp = temp[0]
                    temp = float(temp)
                    final_dict[ent_type][em].append(temp)
    pprint(final_dict)
    for ent_type in final_dict.keys():
        for em in final_dict[ent_type].keys():
            print(
                f"{ent_type} | {em} | mean: {np.mean(final_dict[ent_type][em])}; std: {np.std(final_dict[ent_type][em])}"
            )

    metrics_output_directory = resolve_metrics_output_directory(
        args["metrics_output_dir"], os.environ
    )
    if metrics_output_directory is not None:
        data_base_path = Path(fault_type_classification.base_path)
        dataset_path = (data_base_path / args["dataset_path"]).resolve()
        ground_truth_path = (data_base_path / args["ground_truth_path"]).resolve()
        strategy = (
            "one-shot-k0"
            if args["k"] == 0
            else f'{args["labeling_strategy"]}-k{args["k"]}'
        )
        records = build_metric_records(
            seed_results,
            dataset=args["dataset"],
            track=args["track"],
            method="LasRCA",
            strategy=strategy,
            environment_id=os.environ.get(
                "LASRCA_ENVIRONMENT_ID", args["environment_id"]
            ),
            run_id=os.environ.get("LASRCA_RUN_ID", "standalone"),
            dataset_path=dataset_path,
            dataset_sha256=sha256_file(dataset_path),
            ground_truth_path=ground_truth_path,
            ground_truth_sha256=sha256_file(ground_truth_path),
        )
        summary = summarize_metric_records(records)
        write_evaluation_outputs(metrics_output_directory, records, summary)
        print(f"structured metrics: {metrics_output_directory.resolve()}")
