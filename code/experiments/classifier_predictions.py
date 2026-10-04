"""Re-evaluate saved classifiers to preserve predictions and verify recorded metrics."""
import argparse
import json
from pathlib import Path
import sys

from experiments.artifacts import sha256_file
from experiments.evaluation_output import METRIC_FIELDS,summarize_metric_records,write_evaluation_outputs
from experiments.run_stage import capture_runtime_environment,execute_logged_command
from llm.run_labeling import ROOT,write_json


def matching_metrics(actual,expected,tolerance=1e-6):
    by_kind={r['entity_type']:r for r in expected}
    if set(by_kind)!={r['entity_type'] for r in actual}:
        raise ValueError('Re-evaluation entity types differ')
    for record in actual:
        reference=by_kind[record['entity_type']]
        for field in METRIC_FIELDS:
            if abs(float(record[field])-float(reference[field]))>tolerance:
                raise ValueError(f'Re-evaluation changed {record["entity_type"]} {field}')


def run(sweep,prepared,k):
    sweep=Path(sweep).resolve()
    prepared=Path(prepared).resolve()
    output=sweep/'prediction_verification'
    output.mkdir(exist_ok=True)
    original=json.loads((sweep/'evaluation/per_seed_metrics.json').read_text(encoding='utf-8'))
    completed=json.loads((sweep/'sweep_status.json').read_text(encoding='utf-8'))['completed']
    evidence,records=[],[]
    for item in completed:
        seed=item['seed']
        reference=[r for r in original if r['seed']==seed]
        marker=output/f'seed_{seed}.json'
        if marker.exists():
            verification=json.loads(marker.read_text(encoding='utf-8'))
            if verification['prepared_sha256']!=sha256_file(prepared):
                raise ValueError('Prepared dataset changed after prediction verification')
            directory=Path(verification['evaluation_run'])
        else:
            command=[sys.executable,'-m','tasks.las_rca','--mode','evaluate','--k',str(k),
                '--labeling_strategy','Luna','--eval_seeds',str(seed),'--seed',str(seed),
                '--checkpoint_dir',str(Path(item['checkpoint']).parent),
                '--prepared_dataset_path',str(prepared),'--trace_percentile_clip','stored-1-99',
                '--track','paired-no-std']
            directory=execute_logged_command(output/'runs','evaluate',command,capture_runtime_environment(),
                working_directory=ROOT/'code',config=dict(seed=seed,k=k,prepared_sha256=sha256_file(prepared)))
            if json.loads((directory/'manifest.json').read_text(encoding='utf-8'))['exit_code']!=0:
                raise RuntimeError(f'Re-evaluation failed: {directory}')
            verification=dict(seed=seed,prepared_path=str(prepared),prepared_sha256=sha256_file(prepared),
                evaluation_run=str(directory),checkpoint_path=item['checkpoint'],
                checkpoint_sha256=sha256_file(item['checkpoint']),
                training_run=item['run'],trace_percentile_clip='stored-1-99',metric_match_tolerance=1e-6)
        actual=json.loads((directory/'metrics/per_seed_metrics.json').read_text(encoding='utf-8'))
        matching_metrics(actual,reference)
        verification['all_metrics_match_training']=True
        verification['predictions_path']=str(directory/f'predictions/seed_{seed}_test')
        write_json(marker,verification)
        records.extend(actual);evidence.append(verification)
        print(f'seed {seed}: predictions saved; all 12 metrics match training',flush=True)
    if not (output/'metrics/per_seed_metrics.json').exists():
        write_evaluation_outputs(output/'metrics',records,summarize_metric_records(records,summary_run_id=sweep.name))
    write_json(output/'verification.json',dict(k=k,seeds=evidence,
        purpose='Evidence-only re-evaluation; no classifier updates or retraining'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--sweep',required=True)
    parser.add_argument('--prepared',required=True)
    parser.add_argument('--k',required=True,type=int)
    args=parser.parse_args()
    run(args.sweep,args.prepared,args.k)
