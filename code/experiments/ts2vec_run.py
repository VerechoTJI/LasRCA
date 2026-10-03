"""Isolated TS2Vec training using source loader and released processed inputs."""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np
import torch
from experiments.artifacts import sha256_file
from pretrain.data_loader import load_train_data
from pretrain.ts2vec import TS2Vec
from shared_util.common import pkl_load, pkl_save
from shared_util.seed import seed_everything, init_dl_program

ROOT = Path(__file__).resolve().parents[2]


def validate_training_data(data):
    if data.ndim != 3 or not all(data.shape):
        raise ValueError('TS2Vec training data must have nonempty series/time/feature axes')
    if np.isinf(data).any() or not np.isfinite(data).any():
        raise ValueError('TS2Vec input contains infinity or no finite values')
    return dict(shape=list(data.shape),nan_count=int(np.isnan(data).sum()),
        max_abs=float(np.nanmax(np.abs(data))))


def run(output, epochs=600, seed=405, entity='service'):
    output = Path(output).resolve()
    if (output/'model.pkl').exists() or (output/'progress.json').exists():
        raise FileExistsError('Refusing to overwrite an existing encoder run')
    output.mkdir(parents=True,exist_ok=True)
    source = ROOT/'temp_data/2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl'
    started = time.monotonic()
    # Set PyTorch thread limits directly: importing mkl-service after Torch
    # loads a second OpenMP runtime in this Windows environment.
    torch.set_num_threads(4)
    torch.set_num_interop_threads(4)
    device = init_dl_program(0)
    seed_everything(seed)
    data = load_train_data(f'A_{entity[0]}/metric_trace_log',str(source))
    info = validate_training_data(data)
    config = dict(input_dims=data.shape[-1],output_dims=320,batch_size=32,lr=.001,max_train_length=3000)
    metadata = dict(dataset_path=str(source),dataset_sha256=sha256_file(source),entity_type=entity,
        seed=seed,epochs=epochs,config=config,input=info,training_splits=['normal','train_valid'])
    (output/'config.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    history = []
    def after_epoch(model, loss):
        if not math.isfinite(float(loss)):
            raise RuntimeError('TS2Vec epoch loss is not finite')
        history.append(dict(epoch=model.n_epochs,loss=float(loss),elapsed_seconds=time.monotonic()-started))
        (output/'progress.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
        if model.n_epochs % 20 == 0:
            model.save(str(output/f'model_{model.n_epochs}.pkl'))
        print(f'epoch {model.n_epochs}: loss={loss:.6f}',flush=True)
    model = TS2Vec(device=device,after_epoch_callback=after_epoch,**config)
    model.fit(data,n_epochs=epochs,verbose=False)
    model.save(str(output/'model.pkl'))
    (output/'loss.csv').write_text('epoch,loss,elapsed_seconds\n'+''.join(
        f"{r['epoch']},{r['loss']},{r['elapsed_seconds']}\n" for r in history),encoding='utf-8')
    # Exact source encoding settings on the same released series; test excluded from fitting.
    raw = pkl_load(source)
    split = 'test'
    date = next(iter(raw['data'][split]))
    name = next(iter(raw['data'][split][date][entity]))
    frame = raw['data'][split][date][entity][name]
    values = frame.iloc[:,frame.columns!='timestamp'].to_numpy()[None]
    embedding = model.encode(values,causal=True,sliding_length=1,sliding_padding=10)
    if not np.isfinite(embedding).all():
        raise RuntimeError('Encoded embedding contains non-finite values')
    pkl_save(output/'sample_embedding.pkl',embedding)
    released_path = ROOT/'temp_data/A/embeddings/embedding_600.pkl'
    released = pkl_load(released_path)[split][date][entity][name]
    if hasattr(released,'values'):
        released = released.values
    released = np.asarray(released)
    own = embedding[0]
    difference = None
    if released.shape == own.shape:
        difference = dict(mean_abs=float(np.mean(np.abs(own-released))),
            max_abs=float(np.max(np.abs(own-released))))
    summary = dict(metadata,duration_seconds=time.monotonic()-started,
        checkpoint_sha256=sha256_file(output/'model.pkl'),completed_epochs=len(history),
        comparison=dict(split=split,date=date,entity=name,own_shape=list(own.shape),
            released_shape=list(released.shape),finite=True,difference=difference),
        downstream_evaluation='pending: one series comparison is not a downstream RCA evaluation')
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('TS2Vec training and sample embedding comparison completed',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--epochs',type=int,default=600)
    parser.add_argument('--seed',type=int,default=405)
    parser.add_argument('--entity',choices=['node','service','pod'],default='service')
    args = parser.parse_args()
    run(args.output,args.epochs,args.seed,args.entity)
