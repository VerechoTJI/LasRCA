"""Non-paper execution support: finish dependent work after active jobs complete."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time

from experiments.artifacts import sha256_file
from experiments.raw_pipeline import MODULES
from experiments.retraining_comparison import write_report
from experiments.run_stage import capture_runtime_environment,execute_logged_command
from llm.run_labeling import ROOT,write_json


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def wait_for(check):
    while not check():time.sleep(30)


def source_pairing(baseline,k1,dataset):
    before=read(baseline/'sweep_status.json')['completed']
    after=read(k1/'sweep_status.json')['completed']
    a,b={r['seed']:r for r in before},{r['seed']:r for r in after}
    if set(a)!=set(b) or set(a)!={405,406,407,408,409}:
        raise ValueError('Paired classifier seed sets are incomplete')
    labels=read(dataset/'summary.json')
    signatures=read(dataset/'input_signature.json')
    if not signatures['checks_passed'] or signatures['before']!=signatures['after']:
        raise ValueError('Label update changed protected inputs')
    rows=[]
    for seed in sorted(a):
        x=read(Path(a[seed]['run'])/'metrics/training_summary.json')
        y=read(Path(b[seed]['run'])/'metrics/training_summary.json')
        if x['prepared_dataset_sha256']!=labels['source_sha256'] or y['prepared_dataset_sha256']!=labels['target_sha256']:
            raise ValueError('Paired actual prepared dataset hashes differ from label update')
        if x['ground_truth_sha256']!=y['ground_truth_sha256'] or x['trace_preprocessing']!=y['trace_preprocessing']:
            raise ValueError('Paired Ground Truth or preprocessing differs')
        if x['completed_epochs']!=500 or y['completed_epochs']!=500:
            raise ValueError('Paired classifier epoch count differs')
        rows.append(dict(seed=seed,before_run=a[seed]['run'],after_run=b[seed]['run'],
            ground_truth_sha256=x['ground_truth_sha256'],trace_preprocessing=x['trace_preprocessing'],
            before_checkpoint_sha256=sha256_file(a[seed]['checkpoint']),
            after_checkpoint_sha256=sha256_file(b[seed]['checkpoint'])))
    return dict(input_signatures=signatures,seeds=rows,all_pairing_checks_passed=True)


def run(output,legs=None):
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    runs=ROOT/'runs/lasrca'
    environment=capture_runtime_environment()
    def invoke(module,args,stage='evaluate'):
        directory=execute_logged_command(output/'execution',stage,[sys.executable,'-m',module]+list(map(str,args)),
            environment,working_directory=ROOT/'code',config=dict(action=module,relation_to_paper='execution support only'))
        if read(directory/'manifest.json')['exit_code']!=0:
            raise RuntimeError(f'{module} failed; inspect {directory}')
    def classifiers():
        luna=runs/'luna_20261004'
        def ready():
            state=read(luna/'status.json')
            return sum(row['status']=='completed' for row in state.values())==100
        wait_for(ready)
        invoke('llm.export_evidence',['--run-dir',luna])
        dataset=luna/'dataset'
        if not (dataset/'k1_luna.pkl').exists():invoke('llm.build_labeled_dataset',['--run-dir',luna])
        if read(dataset/'summary.json')['partial']:raise ValueError('Formal dataset is marked partial')
        k1=runs/'luna_k1_no_std'
        if not (k1/'evaluation/per_seed_metrics.json').exists():
            invoke('experiments.classifier_sweep',['--output',k1,'--prepared',dataset/'k1_luna.pkl','--k','1'],'train')
        invoke('llm.audit_labels',['--run-dir',luna])
        if not (k1/'prediction_verification/verification.json').exists():
            invoke('experiments.classifier_predictions',['--sweep',k1,'--prepared',dataset/'k1_luna.pkl','--k','1'])
        comparison=runs/'luna_k0_k1_comparison'
        if not (comparison/'comparison.json').exists():
            write_report(runs/'baseline_no_std/evaluation/per_seed_metrics.json',k1/'evaluation/per_seed_metrics.json',comparison)
        write_json(comparison/'pairing_manifest.json',source_pairing(runs/'baseline_no_std',k1,dataset))
        invoke('experiments.paper_comparison',['--comparison',comparison/'comparison.json','--output',comparison])
        return dict(labeling=100,seeds=[405,406,407,408,409],comparison=str(comparison),audit=str(luna/'audit'))
    def preprocessing():
        sample=runs/'raw_20261004'
        full=runs/'raw_full_20261004'
        def ready(run,modules):
            state=read(run/'pipeline_status.json')
            for module in modules:
                if module in state and state[module]['exit_code']!=0:
                    raise RuntimeError(f'Prerequisite failed: {run} {module}')
            return all(state.get(module,{}).get('exit_code')==0 for module in modules)
        wait_for(lambda:ready(full,MODULES[:7]))
        invoke('experiments.raw_pipeline',['--config',full/'config.json','--output',full,'--stages']+MODULES[7:],'trace')
        wait_for(lambda:ready(sample,MODULES))
        released=ROOT/'temp_data/2022_CCF_AIOps_challenge'
        for run in (sample,full):
            invoke('experiments.raw_evidence',['--run',run,'--include-inputs'])
            invoke('experiments.raw_evidence',['--run',run,'--compare-released',released/'dataset/final/metric_trace_log.pkl'])
            invoke('experiments.structural_comparison',['--run',run,'--released',released])
        return dict(sample=str(sample),full=str(full),completed_stages=10)
    def encoder():
        own=runs/'ts2vec_downstream/service_replaced.pkl'
        manifest=runs/'ts2vec_downstream/encoding_manifest.json'
        wait_for(lambda:own.exists() and manifest.exists())
        if read(manifest)['replaced_sequences']!=150:raise ValueError('Service embedding coverage is incomplete')
        target=runs/'encoder_pair_20261004'
        invoke('experiments.encoder_comparison',['--output',target,'--own-embedding',own],'train')
        return dict(comparison=str(target),self_encoder_entity_type='service',downstream_seed=405)
    actions={'classifiers':classifiers,'preprocessing':preprocessing,'encoder':encoder}
    selected=list(actions) if legs is None else list(legs)
    if not selected or len(set(selected))!=len(selected) or any(key not in actions for key in selected):
        raise ValueError('Choose distinct known follow-up legs')
    state={key:dict(status='waiting_or_running') for key in selected}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={key:pool.submit(actions[key]) for key in selected}
        while futures:
            for key,future in list(futures.items()):
                if not future.done():continue
                try:state[key]=dict(status='completed',result=future.result())
                except Exception as error:state[key]=dict(status='failed',error_type=type(error).__name__,message=str(error))
                futures.pop(key)
                print(f'{key}: {state[key]["status"]}',flush=True)
            write_json(output/'status.json',state)
            if futures:time.sleep(30)
    if any(row['status']!='completed' for row in state.values()):
        raise RuntimeError('A follow-up leg failed; inspect status and execution logs')
    print('Dependent experimental runs and comparisons completed; final acceptance audit remains',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--legs',nargs='+',choices=['classifiers','preprocessing','encoder'])
    args=parser.parse_args()
    run(args.output,args.legs)
