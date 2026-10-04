"""Compare every covered raw window/label and edge set against released data."""
import argparse
import json
from pathlib import Path
import pickle

import numpy as np

from llm.export_evidence import write_csv
from llm.run_labeling import write_json


def compare(run,released):
    run=Path(run).resolve()
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    own=Path(config['temp_data_storage'])
    released=Path(released).resolve()
    load=lambda root,name:pickle.load((root/name).open('rb'))
    filename='dataset/time_interval_and_label/time_interval_window_size_9.pkl'
    a,b=load(own,filename),load(released,filename)
    labels=[]
    excluded=0
    for split,intervals in a['time_interval'].items():
        ref_intervals=b['time_interval'][split]
        ref_entities=b.get('cmdb_id',{}).get(split,[None]*len(ref_intervals))
        own_entities=a.get('cmdb_id',{}).get(split,[None]*len(intervals))
        reference={tuple(interval)+(ref_entities[i],):i for i,interval in enumerate(ref_intervals)}
        for i,interval in enumerate(intervals):
            scope=config['file'][split]
            if interval[0] not in scope['date'] or interval[1] not in scope['cloud_bed']:
                excluded+=1
                continue
            entity=own_entities[i]
            key=tuple(interval)+(entity,)
            j=reference.get(key)
            labels.append(dict(split=split,case_index=i,reference_case_index=j,date=interval[0],cloudbed=interval[1],
                start_timestamp=int(interval[2]),end_timestamp=int(interval[3]),root_entity=entity,
                own_label=np.asarray(a['y'][split][i]).tolist(),
                released_label=np.asarray(b['y'][split][j]).tolist() if j is not None else None,
                status='missing_reference_locator' if j is None else 'equal' if np.array_equal(a['y'][split][i],b['y'][split][j]) else 'label_mismatch'))
    a,b=load(own,'dataset/ent_edge_index/ent_edge_index.pkl'),load(released,'dataset/ent_edge_index/ent_edge_index.pkl')
    edges=[]
    excluded_edges=0
    for split,dates in a.items():
        for date,value in dates.items():
            day,cloud=date.split('/')
            scope=config['file'][split]
            if day not in scope['date'] or cloud not in scope['cloud_bed']:
                excluded_edges+=1
                continue
            reference=b.get(split,{}).get(date)
            source_set=set(zip(*value))
            target_set=set(zip(*reference)) if reference is not None else set()
            edges.append(dict(split=split,date=date,own_edges=len(value[0]),reference_edges=len(reference[0]) if reference else None,
                equal_edge_order=bool(np.array_equal(value,reference)),only_own=sorted(source_set-target_set),only_released=sorted(target_set-source_set),
                dangling_edges=[edge for edge in source_set if min(edge)<0 or max(edge)>=56],
                status='missing_reference' if reference is None else 'equal' if source_set==target_set else 'edge_set_mismatch'))
    output=run/'comparison'
    write_csv(output/'labels.csv',labels)
    write_json(output/'labels.json',labels)
    write_json(output/'topology.json',edges)
    write_json(output/'structural_summary.json',dict(covered_windows=len(labels),label_mismatches=sum(r['status']!='equal' for r in labels),
        covered_topologies=len(edges),topology_mismatches=sum(r['status']!='equal' for r in edges),
        edge_index_entity_count=56,scope=config['file'],excluded_out_of_scope_windows=excluded,
        excluded_out_of_scope_topologies=excluded_edges,sampling='all configured covered windows and edge sets'))
    print(f'Compared {len(labels)} windows and {len(edges)} topologies')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--released',required=True)
    args=parser.parse_args()
    compare(args.run,args.released)
