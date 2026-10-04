"""Isolated encoder experiment; added evidence and localization are reproduction checks."""
import argparse
import copy
import json
from pathlib import Path
import pickle
import time

import numpy as np
import torch

from experiments.artifacts import sha256_file
from llm.run_labeling import ROOT, write_json
from pretrain.ts2vec import TS2Vec
from shared_util.seed import init_dl_program, seed_everything


def replace_embedding(released, replacements, entity_type):
    result=copy.deepcopy(released)
    for (split,date,name),embedding in replacements.items():
        old=np.asarray(released[split][date][entity_type][name])
        embedding=np.asarray(embedding)
        if old.shape!=embedding.shape or not np.isfinite(embedding).all():
            raise ValueError('Embedding shape or finite check failed')
        result[split][date][entity_type][name]=embedding
    expected={(split,date,name) for split,dates in released.items() for date,types in dates.items()
              for name in types.get(entity_type,{})}
    if set(replacements)!=expected:
        raise ValueError('Encoder replacement coverage differs from released')
    return result


def encode(output,encoder_run):
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    target=output/'service_replaced.pkl'
    if target.exists():
        raise FileExistsError('Refusing to overwrite existing embeddings')
    encoder_run=Path(encoder_run).resolve()
    config=json.loads((encoder_run/'config.json').read_text(encoding='utf-8'))
    with Path(config['dataset_path']).open('rb') as f:
        raw=pickle.load(f)
    released_path=ROOT/'temp_data/A/embeddings/embedding_600.pkl'
    with released_path.open('rb') as f:
        released=pickle.load(f)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(4)
    device=init_dl_program(0)
    seed_everything(config['seed'])
    model=TS2Vec(device=device,**config['config'])
    model.load(str(encoder_run/'model.pkl'))
    entity=config['entity_type']
    replacements,rows={},[]
    markers,data=[],[]
    features={}
    for split in ('normal','train_valid','test'):
        for date,types in raw['data'][split].items():
            for name,frame in types[entity].items():
                markers.append((split,date,name))
                columns=[c for c in frame.columns if c!='timestamp']
                features[name]=columns
                data.append(frame.loc[:,columns].to_numpy())
    started=time.monotonic()
    encoded=model.encode(np.array(data),causal=True,sliding_length=1,sliding_padding=10)
    for marker,embedding in zip(markers,encoded):
        split,date,name=marker
        old=np.asarray(released[split][date][entity][name])
        replacements[marker]=embedding
        rows.append(dict(split=split,date=date,entity=name,own_shape=list(embedding.shape),
            released_shape=list(old.shape),finite=bool(np.isfinite(embedding).all()),
            mean_abs=float(np.mean(np.abs(embedding-old))),max_abs=float(np.max(np.abs(embedding-old)))))
    combined=replace_embedding(released,replacements,entity)
    with target.open('xb') as f: pickle.dump(combined,f)
    write_json(output/'encoding_manifest.json',dict(entity_type=entity,replaced_sequences=len(markers),
        other_entity_types='released embeddings unchanged',encoder_sha256=sha256_file(encoder_run/'model.pkl'),
        source_dataset_sha256=config['dataset_sha256'],released_embedding_sha256=sha256_file(released_path),
        output_sha256=sha256_file(target),encoding=dict(causal=True,sliding_length=1,sliding_padding=10),
        duration_seconds=time.monotonic()-started,input_feature_order=features,comparisons=rows))
    print(f'Encoded {len(markers)} {entity} sequences')


def downstream(output, embedding, seed=405,epochs=500):
    from experiments.evaluation_output import build_metric_records, summarize_metric_records, write_evaluation_outputs
    from tasks.fine_tuning_fault_type_classification import FineTuningFaultTypeClassification
    from tasks.base import BaseClass as LasBase

    output=Path(output).resolve()
    if (output/'summary.json').exists():
        raise FileExistsError('Completed downstream run already exists')
    output.mkdir(parents=True,exist_ok=True)
    cache=output/'dataset'
    models=output/'models'
    models.mkdir(exist_ok=True)
    embedding=Path(embedding).resolve()
    torch.set_num_threads(4)
    torch.set_num_interop_threads(4)
    device=init_dl_program(0)
    seed_everything(seed)
    class IsolatedFineTuning(FineTuningFaultTypeClassification):
        def get_dataset_file_name(self):
            return str(cache),'fine_tuning.pkl'
        def evaluate_las_fault_classification(self,loaders,split,threshold=.5):
            super().evaluate_las_fault_classification(loaders,split,threshold)
            # Same max fault probability ranking used by the LasRCA evaluator.
            # This adds an evaluation output; it does not change fine-tuning.
            LasBase.evaluate_las_fault_localization(self,loaders,split,threshold)
    base=ROOT/'temp_data'
    # The original fine-tuning loader prefixes temp_data; retain relative routing.
    import os
    data_config=dict(dataset='A/metric_trace_log',dataset_path='2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl',
        embedding_path=os.path.relpath(embedding,base),ground_truth_path='2022_CCF_AIOps_challenge/dataset/time_interval_and_label/time_interval_window_size_9.pkl',
        model_dir=str(models),sample_strategy='narrow_few_shot',train_size=200,valid_size=100,
        each_train_size=1,each_valid_size=1,window_size=9)
    model_config=dict(device=device,seed=seed,epochs=epochs,window_size=9,batch_size=32,lr=.0001,weight_decay=.001,
        in_dim=320,GAT_out_channels=128,GAT_heads=2,GAT_dropout=.1)
    write_json(output/'configuration.json',dict(seed=seed,epochs=epochs,data_config=data_config,
        model_config={k:str(v) if k=='device' else v for k,v in model_config.items()},embedding_path=str(embedding),embedding_sha256=sha256_file(embedding)))
    started=time.monotonic()
    task=IsolatedFineTuning(data_config,model_config)
    write_json(output/'split_labels.json',dict((split,dict(y_marker=value.get('y_marker'),y=value['y'])) for split,value in task.dataset['data'].items()))
    task.train_based_on_representation()
    checkpoint=models/f'model_seed_{seed}.pkl'
    result=dict(seed=seed,checkpoint_path=str(checkpoint),checkpoint_sha256=sha256_file(checkpoint),
        localization=task.fl_result,classification=task.fc_result)
    ground_truth=base/data_config['ground_truth_path']
    records=build_metric_records([result],dataset='A/metric_trace_log',track='paired-encoder',method='Pretrain and Fine-tuning',
        strategy='encoder-comparison',environment_id='primary-windows',run_id=output.name,
        dataset_path=cache/'fine_tuning.pkl',dataset_sha256=sha256_file(cache/'fine_tuning.pkl'),
        ground_truth_path=ground_truth,ground_truth_sha256=sha256_file(ground_truth))
    write_evaluation_outputs(output/'metrics',records,summarize_metric_records(records))
    write_json(output/'summary.json',dict(result=result,duration_seconds=time.monotonic()-started,
        seed=seed,epochs=epochs,embedding_sha256=sha256_file(embedding),
        localization_note='Added reproduction evaluator, identical max-fault-probability ranking to LasRCA; not an original fine-tuning output'))
    print('Downstream training and classification/localization evaluation completed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['encode','downstream'])
    parser.add_argument('--output',required=True)
    parser.add_argument('--encoder-run')
    parser.add_argument('--embedding')
    parser.add_argument('--seed',type=int,default=405)
    parser.add_argument('--epochs',type=int,default=500)
    args=parser.parse_args()
    if args.mode=='encode': encode(args.output,args.encoder_run)
    else: downstream(args.output,args.embedding,args.seed,args.epochs)
