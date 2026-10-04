"""Preserve evaluator inputs so metrics can be independently recomputed."""
import csv
import json
from pathlib import Path
import numpy as np
from llm.run_labeling import write_json


def save(output, probabilities, truth, metadata, *, seed, split, threshold=.5):
    output=Path(output)/f'seed_{seed}_{split}'
    output.mkdir(parents=True,exist_ok=False)
    arrays,scores,all_truth={},[],[]
    records=[]
    for kind in metadata['ent_types']:
        start,end=metadata['ent_type_index'][kind]
        fault_start,fault_end=metadata['ent_fault_type_index'][kind]
        p=np.asarray(probabilities[kind]).reshape(-1,end-start,fault_end-fault_start)
        y=np.asarray(truth[kind]).reshape(p.shape)
        if not np.isfinite(p).all() or not np.isfinite(y).all():
            raise ValueError('Cannot preserve nonfinite evaluator inputs')
        arrays[kind+'_probabilities']=p
        arrays[kind+'_truth']=y
        scores.append(p.max(axis=2))
        all_truth.append(y.max(axis=2))
        for case in range(len(p)):
            for entity in range(end-start):
                records.append(dict(case_index=case,entity_index=start+entity,
                    entity=metadata['ent_names'][start+entity],entity_type=kind,
                    ground_truth_fault_ids=json.dumps((np.flatnonzero(y[case,entity])+fault_start+1).tolist()),
                    predicted_fault_ids=json.dumps((np.flatnonzero(p[case,entity]>threshold)+fault_start+1).tolist())))
    arrays['entity_scores']=np.concatenate(scores,axis=1)
    arrays['entity_truth']=np.concatenate(all_truth,axis=1)
    arrays['entity_ranking']=np.argsort(arrays['entity_scores'])[:,::-1]
    np.savez_compressed(output/'predictions.npz',**arrays)
    with (output/'entity_predictions.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader();writer.writerows(records)
    write_json(output/'manifest.json',dict(seed=seed,split=split,cases=len(arrays['entity_ranking']),
        threshold=threshold,metadata=metadata,
        classification='Strict probability > threshold; all-zero Ground Truth is No Fault, matching source evaluator',
        localization='Max fault probability per entity; concatenate entity types in metadata order; numpy argsort descending',
        entity_level_selection='Evaluate each fault level on cases with exactly one positive entity of that type',
        source='Captured probabilities and Ground Truth before the original classification threshold operation'))
