"""Validate summaries and update only selected unlabeled y/y_mask in a new file."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import pickle

from llm.run_labeling import ROOT, write_json


def parse_summary(text):
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char == '{':
            try:
                value, _ = decoder.raw_decode(text[i:])
                if isinstance(value,dict):
                    return value
            except json.JSONDecodeError:
                pass
    raise ValueError('No valid JSON object in summary')


def update_labels(dataset, samples, summaries):
    result = copy.deepcopy(dataset)
    rows = []
    names = dataset['meta_data']['ent_names']
    faults = dataset['meta_data']['en_fault_type_list']
    for sample in samples:
        case = int(sample['sample_index'])
        summary = summaries.get(case,{})
        for name in sample['ent_names']:
            row = {'case':case,'entity':name,'status':'missing_label'}
            if name not in names:
                row['status'] = 'unknown_entity'
                rows.append(row)
                continue
            entity = names.index(name)
            row.update(entity_index=entity,y_before=int(dataset['data']['unlabeled']['y'][case][entity]),
                mask_before=int(dataset['data']['unlabeled']['y_mask'][case][entity]),
                ground_truth=int(dataset['data']['unlabeled']['y_true'][case][entity])
                if 'y_true' in dataset['data']['unlabeled'] else int(dataset['data']['unlabeled']['y'][case][entity]))
            value = summary.get(name)
            fault = value.get('exact_fault_type') if isinstance(value,dict) else None
            row['llm_label'] = fault
            if fault is not None:
                if not isinstance(fault,str):
                    row['status'] = 'invalid_type'
                else:
                    normalized = 'Node Disk Space Consumption' if fault=='Node Disk Space IO Consumption' else fault
                    label = 0 if normalized.lower()=='no fault' else faults.index(normalized)+1 if normalized in faults else None
                    if label is None:
                        row['status'] = 'unknown_fault'
                    else:
                        result['data']['unlabeled']['y'][case][entity] = label
                        result['data']['unlabeled']['y_mask'][case][entity] = 1
                        row['status'] = 'applied'
            row.update(y_after=int(result['data']['unlabeled']['y'][case][entity]),
                mask_after=int(result['data']['unlabeled']['y_mask'][case][entity]))
            rows.append(row)
        for extra in set(summary)-set(sample['ent_names']):
            rows.append(dict(case=case,entity=extra,status='unexpected_entity'))
    return result, rows


def build(run_directory, allow_partial=False):
    run_directory = Path(run_directory)
    target = run_directory/'dataset/k1_luna.pkl'
    if target.exists():
        raise FileExistsError('Refusing to overwrite k1 dataset')
    base = ROOT/'temp_data/A'
    source = base/'metric_trace_log/dataset/narrow_few_shot_train_size_1.pkl'
    selected = base/'selected_samples/selected_samples_k_0.pkl'
    with selected.open('rb') as f:
        samples = pickle.load(f)
    statuses = json.loads((run_directory/'status.json').read_text(encoding='utf-8'))
    if not allow_partial and any(statuses.get(str(s['sample_index']),{}).get('status')!='completed' for s in samples):
        raise ValueError('All 100 selected cases must complete before producing the formal dataset')
    summaries, errors = {}, []
    for sample in samples:
        index = int(sample['sample_index'])
        if statuses.get(str(index),{}).get('status') != 'completed':
            continue
        try:
            summaries[index] = parse_summary((run_directory/f'responses/summarization/{index}.txt').read_text(encoding='utf-8'))
        except ValueError as error:
            errors.append(dict(case=index,error=str(error)))
    with source.open('rb') as f:
        original = pickle.load(f)
    updated, rows = update_labels(original,samples,summaries)
    if not any(row['status']=='applied' for row in rows):
        raise ValueError('No valid labels to apply')
    target.parent.mkdir(parents=True,exist_ok=True)
    from llm.dataset_evidence import save as save_dataset_evidence
    save_dataset_evidence(target.parent,original,updated,rows)
    with target.open('xb') as f:
        pickle.dump(updated,f)
    write_json(run_directory/'dataset/label_changes.json',rows)
    write_json(run_directory/'dataset/summary.json',dict(source=str(source),target=str(target),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),parse_errors=errors,
        partial=allow_partial,applied=sum(r['status']=='applied' for r in rows),
        new_mask_count=sum(r['status']=='applied' and r['mask_before']==0 for r in rows)))
    print(str(target.resolve()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir',required=True)
    parser.add_argument('--allow-partial',action='store_true')
    args = parser.parse_args()
    build(args.run_dir,args.allow_partial)
