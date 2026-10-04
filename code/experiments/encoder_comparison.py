"""Paired downstream execution and evidence, independent of the paper algorithm."""
import argparse
import json
from pathlib import Path
import sys

from experiments.artifacts import sha256_file
from experiments.retraining_comparison import compare_records
from experiments.run_stage import capture_runtime_environment, execute_logged_command
from llm.run_labeling import ROOT, write_json
from llm.export_evidence import write_csv


def run(output, own_embedding=None, seed=405):
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    variants={'released':ROOT/'temp_data/A/embeddings/embedding_600.pkl'}
    if own_embedding is not None:
        variants['self_service']=Path(own_embedding).resolve()
    for name,embedding in variants.items():
        target=output/name
        if (target/'summary.json').exists():
            summary=json.loads((target/'summary.json').read_text(encoding='utf-8'))
            if summary['seed']!=seed or summary['epochs']!=500 or summary['embedding_sha256']!=sha256_file(embedding):
                raise ValueError('Existing downstream run configuration differs')
            continue
        # Retain the uv-selected interpreter; PATH resolves a different Python here.
        command=[sys.executable,'-m','experiments.encoder_downstream','downstream',
                 '--output',str(target),'--embedding',str(embedding),'--seed',str(seed),'--epochs','500']
        directory=execute_logged_command(output/'execution','train',command,capture_runtime_environment(),
            working_directory=ROOT/'code',config=dict(variant=name,seed=seed,embedding_sha256=sha256_file(embedding)))
        manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        if manifest['exit_code']!=0:
            raise RuntimeError(f'Downstream {name} failed; inspect {directory}')
        print(f'{name}: 500 epochs and evaluation completed',flush=True)
    if len(variants)!=2:
        return
    before=json.loads((output/'released/split_labels.json').read_text(encoding='utf-8'))
    after=json.loads((output/'self_service/split_labels.json').read_text(encoding='utf-8'))
    if before!=after:
        raise ValueError('Paired downstream labels or splits differ')
    metrics=[json.loads((output/name/'metrics/per_seed_metrics.json').read_text(encoding='utf-8')) for name in variants]
    rows,summary=compare_records(*metrics)
    protocol={name:dict(configuration=json.loads((output/name/'configuration.json').read_text(encoding='utf-8')),
        summary=json.loads((output/name/'summary.json').read_text(encoding='utf-8')),
        split_labels_sha256=sha256_file(output/name/'split_labels.json'),
        dataset_sha256=sha256_file(output/name/'dataset/fine_tuning.pkl')) for name in variants}
    write_json(output/'comparison.json',dict(seed=seed,count_seeds=1,split_labels_equal=True,
        scope='service encoder replaced; node/pod encoders remain released',variants=protocol,per_seed=rows,summary=summary))
    write_csv(output/'comparison.csv',rows)
    lines=['# Released／自訓練 service encoder 下游比較','',
           '相同 seed 405、500 epochs、Ground Truth 與 split；一個 seed 的結果不代表五 seed 的穩定性。',
           '僅替換 service embedding；node、pod 沿用 released。定位評估為本次新增驗證輸出。','',
           '| Entity | Metric | Released | Self service | 差（百分點） |',
           '|---|---|---|---|---|']
    for row in rows:
        lines.append(f"| {row['entity_type']} | {row['metric']} | {row['before']:.6f} | {row['after']:.6f} | {row['delta_percentage_points']:+.2f} |")
    (output/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--own-embedding')
    parser.add_argument('--seed',type=int,default=405)
    args=parser.parse_args()
    run(args.output,args.own_embedding,args.seed)
