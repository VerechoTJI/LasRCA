"""Five-seed execution/evidence controller; not a paper algorithm."""
import argparse
import json
from pathlib import Path
import sys

from experiments.artifacts import sha256_file
from experiments.evaluation_output import build_metric_records, summarize_metric_records, write_evaluation_outputs
from experiments.run_stage import capture_runtime_environment, execute_logged_command
from llm.run_labeling import ROOT, write_json


def run(output, prepared, k, seeds):
    output=Path(output).resolve()
    prepared=Path(prepared).resolve()
    output.mkdir(parents=True,exist_ok=True)
    records,completed=[],[]
    gt=ROOT/'temp_data/2022_CCF_AIOps_challenge/dataset/time_interval_and_label/time_interval_window_size_9.pkl'
    for seed in seeds:
        summaries=[]
        for path in output.glob('*/metrics/training_summary.json'):
            value=json.loads(path.read_text(encoding='utf-8'))
            if value['seed']==seed:
                summaries.append((path,value))
        if len(summaries)>1:
            raise ValueError('Duplicate successful seed summaries')
        if not summaries:
            # Use the exact interpreter selected by uv, avoiding PATH's system Python.
            command=[sys.executable,'-m','tasks.las_rca','--mode','train','--k',str(k),
                '--seed',str(seed),'--epochs','500','--labeling_strategy','Luna',
                '--track','local-full-trace-stable','--trace_percentile_clip','stored-1-99',
                '--prepared_dataset_path',str(prepared)]
            run_dir=execute_logged_command(output,'train',command,capture_runtime_environment(),
                working_directory=ROOT/'code',config=dict(seed=seed,k=k,prepared_dataset_sha256=sha256_file(prepared)))
            manifest=json.loads((run_dir/'manifest.json').read_text(encoding='utf-8'))
            if manifest['exit_code']!=0:
                raise RuntimeError(f'Seed {seed} failed; inspect {run_dir}')
            path=run_dir/'metrics/training_summary.json'
            summaries=[(path,json.loads(path.read_text(encoding='utf-8')))]
        path,summary=summaries[0]
        if summary['prepared_dataset_sha256']!=sha256_file(prepared) or summary['completed_epochs']!=500:
            raise ValueError('Existing run input/epoch mismatch')
        result=dict(seed=seed,checkpoint_path=summary['checkpoint_path'],checkpoint_sha256=summary['checkpoint_sha256'],
            localization=summary['localization'],classification=summary['classification'])
        records.extend(build_metric_records([result],dataset='A/metric_trace_log',track='paired-no-std',
            method='LasRCA',strategy='one-shot-k0' if k==0 else 'Luna-k1',environment_id='primary-windows',run_id=path.parent.parent.name,
            dataset_path=prepared,dataset_sha256=sha256_file(prepared),ground_truth_path=gt,ground_truth_sha256=sha256_file(gt)))
        completed.append(dict(seed=seed,run=str(path.parent.parent),checkpoint=summary['checkpoint_path']))
        write_json(output/'sweep_status.json',dict(k=k,completed=completed,requested_seeds=seeds))
        print(f'k={k} seed={seed} complete',flush=True)
    write_evaluation_outputs(output/'evaluation',records,summarize_metric_records(records,summary_run_id=output.name))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--prepared',required=True)
    parser.add_argument('--k',type=int,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[405,406,407,408,409])
    args=parser.parse_args()
    run(args.output,args.prepared,args.k,args.seeds)
