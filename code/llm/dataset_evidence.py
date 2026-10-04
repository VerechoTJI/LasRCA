"""Full label snapshots and distribution audit; reproduction evidence only."""
from collections import Counter
import hashlib
import pickle

import numpy as np

from llm.run_labeling import write_json
from llm.export_evidence import write_csv


def input_signature(dataset):
    feature_values={split:{key:value for key,value in data.items()
                   if key.startswith('x_') or key.startswith('o11y_name_') or key=='ent_edge_index'}
                    for split,data in dataset['data'].items()}
    split_values={split:dict(y_marker=data.get('y_marker'),size=len(data['y']))
                  for split,data in dataset['data'].items()}
    protected={split:data['y'] for split,data in dataset['data'].items() if split!='unlabeled'}
    digest=lambda value: hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()
    return dict(features_sha256=digest(feature_values),split_sha256=digest(split_values),
                protected_labels_sha256=digest(protected))


def distribution(dataset):
    rows=[]
    names=['No fault']+dataset['meta_data']['en_fault_type_list']
    for split,data in dataset['data'].items():
        y=np.asarray(data['y'])
        mask=np.asarray(data.get('y_mask',np.ones_like(y)))
        for entity,(start,end) in dataset['meta_data']['ent_type_index'].items():
            counts=Counter(y[:,start:end][mask[:,start:end]==1].astype(int).ravel())
            for label,name in enumerate(names):
                rows.append(dict(split=split,entity_type=entity,fault_id=label,fault_name=name,
                    labeled_count=int(counts[label]),masked_entity_count=int((mask[:,start:end]==0).sum())))
    return rows


def save(output,before,after,changes):
    output.mkdir(parents=True,exist_ok=True)
    before_signature=input_signature(before)
    after_signature=input_signature(after)
    if before_signature!=after_signature:
        raise ValueError('Features, splits or protected labels changed during label update')
    for name,dataset in [('before',before),('after',after)]:
        arrays={}
        absent=[]
        for split,data in dataset['data'].items():
            for field in ('y','y_mask'):
                if field in data: arrays[split+'__'+field]=np.asarray(data[field])
                else: absent.append(split+'__'+field)
        np.savez_compressed(output/f'labels_{name}.npz',**arrays)
        write_json(output/f'labels_{name}_schema.json',dict(absent_fields=absent,
            arrays={key:dict(shape=list(value.shape),dtype=str(value.dtype)) for key,value in arrays.items()}))
    b,a=distribution(before),distribution(after)
    rows=[]
    for old,new in zip(b,a):
        row={key:old[key] for key in ('split','entity_type','fault_id','fault_name')}
        row.update(labeled_count_before=old['labeled_count'],labeled_count_after=new['labeled_count'],
            net_labeled_change=new['labeled_count']-old['labeled_count'],masked_count_before=old['masked_entity_count'],
            masked_count_after=new['masked_entity_count'])
        matching=[]
        if old['split']=='unlabeled':
            start,end=before['meta_data']['ent_type_index'][old['entity_type']]
            matching=[r for r in changes if r.get('entity_index') is not None and start<=r['entity_index']<end]
        row['newly_labeled_count']=sum(r['status']=='applied' and r['mask_before']==0 and r['y_after']==old['fault_id'] for r in matching)
        row['changed_to_count']=sum(r['status']=='applied' and r['y_before']!=r['y_after'] and r['y_after']==old['fault_id'] for r in matching)
        row['ignored_at_previous_label_count']=sum(r['status']!='applied' and r.get('y_before')==old['fault_id'] for r in matching)
        rows.append(row)
    write_csv(output/'fault_type_distribution.csv',rows)
    write_json(output/'fault_type_distribution.json',rows)
    write_json(output/'input_signature.json',dict(before=before_signature,after=after_signature,checks_passed=True))
    write_json(output/'update_statistics.json',dict(applied=sum(r['status']=='applied' for r in changes),
        new_mask_count=sum(r['status']=='applied' and r['mask_before']==0 for r in changes),
        changed_y_count=sum(r['status']=='applied' and r['y_before']!=r['y_after'] for r in changes),
        already_labeled_count=sum(r['status']=='applied' and r['mask_before']==1 for r in changes),
        ignored_counts=dict(Counter(r['status'] for r in changes if r['status']!='applied'))))
