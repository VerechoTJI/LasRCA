"""Lossless raw test groundtruth format adaptation, not a paper method."""
import argparse
import json
from pathlib import Path

import pandas as pd

from experiments.artifacts import sha256_file
from llm.run_labeling import write_json


def groundtruth_frame(value):
    required={'timestamp','level','cmdb_id','failure_type'}
    if not isinstance(value,dict) or not required<=set(value):
        raise ValueError('Groundtruth JSON lacks required source fields')
    if any(not isinstance(v,list) for v in value.values()):
        raise ValueError('Groundtruth fields must be parallel lists')
    if len({len(v) for v in value.values()})!=1:
        raise ValueError('Groundtruth list lengths differ')
    return pd.DataFrame(value)


def convert(source,output):
    source,output=Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for path in sorted(source.glob('*.json')):
        frame=groundtruth_frame(json.loads(path.read_text(encoding='utf-8')))
        target=output/path.with_suffix('.csv').name
        if target.exists():
            old=pd.read_csv(target)
            pd.testing.assert_frame_equal(old,frame,check_dtype=False)
        else:
            frame.to_csv(target,index=False,encoding='utf-8')
        rows.append(dict(source=str(path.resolve()),source_sha256=sha256_file(path),
            output=str(target.resolve()),output_sha256=sha256_file(target),fault_cases=len(frame),columns=list(frame)))
    if not rows:raise FileNotFoundError('No groundtruth JSON files')
    write_json(output/'conversion_manifest.json',dict(files=rows,total_fault_cases=sum(r['fault_cases'] for r in rows),
        transformation='Parallel JSON lists to CSV rows; timestamps, labels and all fields unchanged'))
    print(f'Converted {len(rows)} GT files; {sum(r["fault_cases"] for r in rows)} fault cases')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    convert(args.source,args.output)
