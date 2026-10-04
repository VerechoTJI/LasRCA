"""Post-run count/schema comparison evidence, independent of preprocessing math."""
import argparse
import json
from pathlib import Path
import pickle
import time

import numpy as np
import pandas as pd

from experiments.artifacts import sha256_file
from llm.export_evidence import write_csv
from llm.run_labeling import write_json


def inspect_value(value,path=''):
    rows=[]
    if isinstance(value,pd.DataFrame):
        numeric=value.select_dtypes(include='number')
        array=numeric.to_numpy()
        rows.append(dict(field_path=path,kind='DataFrame',rows=len(value),columns=list(value.columns),
            dtypes={str(k):str(v) for k,v in value.dtypes.items()},shape=list(value.shape),
            nan_count=int(value.isna().sum().sum()),inf_count=int(np.isinf(array).sum()),
            unit='rows (wide observations; see columns for feature count)'))
    elif isinstance(value,np.ndarray):
        numeric=np.issubdtype(value.dtype,np.number)
        rows.append(dict(field_path=path,kind='ndarray',shape=list(value.shape),dtype=str(value.dtype),
            count=int(value.size),unit='array elements',nan_count=int(np.isnan(value).sum()) if numeric else None,
            inf_count=int(np.isinf(value).sum()) if numeric else None))
    elif isinstance(value,dict):
        rows.append(dict(field_path=path,kind='dict',keys=[str(k) for k in value],count=len(value),unit='keys'))
        for key,item in value.items(): rows.extend(inspect_value(item,path+'/'+str(key)))
    elif isinstance(value,(list,tuple)):
        rows.append(dict(field_path=path,kind=type(value).__name__,count=len(value),unit='items'))
        # Lists of homogeneous vectors record a shape, not one schema per scalar.
        if value:
            if isinstance(value[0],(dict,pd.DataFrame,np.ndarray)):
                for i,item in enumerate(value): rows.extend(inspect_value(item,path+'/'+str(i)))
            else:
                try:
                    array=np.asarray(value)
                    if array.dtype!=object: rows.extend(inspect_value(array,path))
                except ValueError: pass
    else:
        rows.append(dict(field_path=path,kind=type(value).__name__,unit='scalar'))
    return rows


def inspect_csv(path):
    count=0
    nonnull=0
    columns=[]
    types={}
    for chunk in pd.read_csv(path,chunksize=50000):
        if not columns:
            columns=list(chunk.columns)
            types={str(k):str(v) for k,v in chunk.dtypes.items()}
        count+=len(chunk)
        nonnull+=int(chunk.drop(columns=['timestamp'],errors='ignore').notna().sum().sum())
    return dict(rows=count,columns=columns,dtypes=types,non_null_non_timestamp_cells=nonnull,
        unit='CSV records (multiline quoted records parsed by pandas)',dtype_policy='first chunk inferred dtypes')


def producing_stage(path):
    parts=path.parts
    mapping={'raw_metric':'dao.metric_dao','raw_trace':'dao.trace_dao','raw_log':'dao.log_dao'}
    for part,stage in mapping.items():
        if part in parts:return stage
    if 'dataset' in parts:
        child=parts[parts.index('dataset')+1]
        return {'metric':'service.metric_generator','trace':'service.trace_generator','log':'service.log_generator',
            'final':'service.dataset_generator','time_interval_and_label':'service.time_interval_label_generator',
            'ent_edge_index':'service.ent_edge_index_generator'}.get(child,'unknown')
    if 'analysis' in parts:
        child=parts[parts.index('analysis')+1]
        return {'metric':'service.metric_generator','trace':'service.trace_generator','log':'dao.log_dao'}.get(child,'unknown')
    return 'unknown'


def consuming_stages(path,role):
    parts=path.parts
    if role.startswith('ground_truth'):return ['service.time_interval_label_generator']
    if role.startswith('input'):
        return [stage for category,stage in [('metric','dao.metric_dao'),('trace','dao.trace_dao'),('log','dao.log_dao')] if category in parts]
    for category,stage in [('raw_metric','service.metric_generator'),('raw_trace','service.trace_generator'),('raw_log','service.log_generator'),('resource_entity','service.ent_edge_index_generator')]:
        if category in parts:return [stage]
    if 'dataset' in parts and 'final' not in parts:return ['service.dataset_generator']
    return []


def collect(run,include_inputs=False):
    run=Path(run).resolve()
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    roots=[('output',Path(config['temp_data_storage']))]
    if include_inputs:
        roots.extend(('input_'+split,Path(value['base_folder'])) for split,value in config['file'].items())
        roots.extend(('ground_truth_'+split,Path(value)) for split,value in config['ground_truth'].items())
    records,schemas,errors=[],{},[]
    started=time.monotonic()
    seen=set()
    for role,root in roots:
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.resolve() in seen:continue
            seen.add(path.resolve())
            record=dict(role=role,path=str(path.resolve()),relative_path=str(path.relative_to(root)),
                producing_stage=producing_stage(path.relative_to(root)) if role=='output' else 'source',bytes=path.stat().st_size)
            record['consuming_stages']=consuming_stages(path.relative_to(root),role)
            try:
                if path.suffix.lower()=='.csv':
                    schema=inspect_csv(path)
                    record.update(count=schema['rows'],unit=schema['unit'])
                elif path.suffix.lower()=='.pkl':
                    with path.open('rb') as f:value=pickle.load(f)
                    schema=inspect_value(value)
                    record.update(count=None,unit='see field-level counts and units in schema')
                    del value
                elif path.suffix.lower()=='.json':
                    schema=inspect_value(json.loads(path.read_text(encoding='utf-8')))
                    record.update(count=None,unit='see field-level schema')
                else:
                    schema=dict(kind='file',suffix=path.suffix,count=None,unit='not a parsed observation artifact')
                record['sha256']=sha256_file(path)
                schemas[record['path']]=schema
                record['schema_ref']=record['path']
                record['status']='inspected'
            except Exception as error:
                record['status']='inspection_failed'
                errors.append(dict(path=str(path),error_type=type(error).__name__,message=str(error)))
            records.append(record)
    write_csv(run/'stage_counts.csv',records)
    write_json(run/'stage_counts.json',records)
    write_json(run/'stage_schemas.json',schemas)
    io_rows=[]
    for record in records:
        if record['role']=='output':
            io_rows.append(dict(module=record['producing_stage'],direction='output',path=record['path'],
                count=record.get('count'),unit=record.get('unit'),schema_ref=record.get('schema_ref'),status=record['status']))
        for module in record['consuming_stages']:
            io_rows.append(dict(module=module,direction='input',path=record['path'],count=record.get('count'),
                unit=record.get('unit'),schema_ref=record.get('schema_ref'),status=record['status']))
    write_csv(run/'stage_input_output_counts.csv',io_rows)
    write_json(run/'evidence_failures.json',errors)
    write_json(run/'final_manifest.json',dict(scope=config['file'],includes_inputs=include_inputs,
        artifacts=records,inspection_errors=errors,duration_seconds=time.monotonic()-started,
        limitations='Counts are per artifact with explicit units. Intermediate stages share inputs; not claimed to be an instrumented read count. Unknown producing stages are explicitly marked.'))
    print(f'Inspected {len(records)} artifacts; {len(errors)} inspection failures',flush=True)


def feature_coverage(own, reference, own_counts, reference_counts):
    """Use the generator's Metric/Trace/Log concatenation order, checking dimensions."""
    def partition(frame, counts):
        columns=[column for column in frame.columns if column!='timestamp']
        if sum(counts.get(modality,0) for modality in ('metric','trace','log'))!=len(columns):
            raise ValueError('Feature counts do not match the actual observation columns')
        groups={}
        start=0
        for modality in ('metric','trace','log'):
            end=start+counts.get(modality,0)
            groups[modality]=columns[start:end]
            start=end
        return groups
    a,b=partition(own,own_counts),partition(reference,reference_counts)
    rows=[]
    for modality in a:
        shared=[column for column in a[modality] if column in b[modality]]
        rows.append(dict(modality=modality,own_columns=a[modality],released_columns=b[modality],
            shared_columns=shared,own_only_columns=[c for c in a[modality] if c not in b[modality]],
            released_only_columns=[c for c in b[modality] if c not in a[modality]],
            own_feature_count=len(a[modality]),released_feature_count=len(b[modality]),
            shared_feature_count=len(shared),column_order_equal=a[modality]==b[modality],
            numeric_comparison_status='shared_features_only' if shared else 'no_shared_features'))
    return rows


def compare(run,released):
    run=Path(run).resolve()
    config=json.loads((run/'config.json').read_text(encoding='utf-8'))
    own_path=Path(config['temp_data_storage'])/'dataset/final/metric_trace_log.pkl'
    released=Path(released).resolve()
    with own_path.open('rb') as f:own=pickle.load(f)
    with released.open('rb') as f:reference=pickle.load(f)
    summary,samples,coverage,shapes=[],[],[],[]
    for split,dates in own['data'].items():
        if not dates:continue
        # Explicit sample: first date/cloudbed in each split, first entity/type.
        date=sorted(dates)[0]
        if date not in reference['data'].get(split,{}):
            summary.append(dict(split=split,date=date,status='missing_released_date'))
            continue
        for entity_type,entities in dates[date].items():
            if not entities:continue
            name=sorted(entities)[0]
            a=entities[name]
            b=reference['data'][split][date][entity_type][name]
            locator=dict(split=split,date=date,entity_type=entity_type,entity=name)
            coverage.extend(dict(**locator,**row) for row in feature_coverage(a,b,
                own['meta_data']['ent_feature_num'][entity_type],reference['meta_data']['ent_feature_num'][entity_type]))
            shared=[c for c in a.columns if c!='timestamp' and c in b.columns]
            aligned=a.merge(b,on='timestamp',suffixes=('_own','_released'),how='inner')
            shapes.append(dict(**locator,own_rows=len(a),own_columns=len(a.columns),released_rows=len(b),
                released_columns=len(b.columns),aligned_timestamps=len(aligned),
                own_unmatched_timestamps=len(a)-len(aligned),released_unmatched_timestamps=len(b)-len(aligned),
                own_timestamp_unique=bool(a['timestamp'].is_unique),released_timestamp_unique=bool(b['timestamp'].is_unique)))
            for column in shared:
                x=aligned[column+'_own'].to_numpy()
                y=aligned[column+'_released'].to_numpy()
                valid=np.isfinite(x)&np.isfinite(y)
                diff=np.abs(x[valid]-y[valid])
                summary.append(dict(split=split,date=date,entity_type=entity_type,entity=name,feature=column,
                    own_shape=list(a.shape),released_shape=list(b.shape),aligned_timestamps=len(aligned),
                    valid_pairs=int(valid.sum()),mean_abs=float(diff.mean()) if diff.size else None,
                    max_abs=float(diff.max()) if diff.size else None,nan_mismatch=int((np.isnan(x)!=np.isnan(y)).sum()),
                    over_1e_6=int((diff>1e-6).sum()),column_order_equal=list(a.columns)==list(b.columns)))
                for index in range(min(5,len(aligned))):
                    samples.append(dict(split=split,date=date,entity=name,entity_type=entity_type,feature=column,
                        timestamp=int(aligned['timestamp'].iloc[index]),own_value=float(x[index]),released_value=float(y[index])))
    output=run/'comparison'
    write_csv(output/'feature_summary.csv',summary)
    write_csv(output/'feature_samples.csv',samples)
    write_csv(output/'shapes.csv',shapes)
    write_json(output/'feature_coverage.json',coverage)
    write_csv(output/'feature_coverage.csv',coverage)
    meta={key:dict(own=own['meta_data'].get(key),released=reference['meta_data'].get(key),equal=own['meta_data'].get(key)==reference['meta_data'].get(key))
          for key in ('ent_types','ent_names','ent_type_index','ent_feature_num','o11y_names')}
    write_json(output/'metadata_topology_alignment.json',meta)
    write_json(output/'summary.json',dict(own_path=str(own_path),own_sha256=sha256_file(own_path),
        released_path=str(released),released_sha256=sha256_file(released),
        sampling_policy='first date/cloudbed per available split, first entity per type; first five timestamps shown per shared feature',
        feature_rows=len(summary),numeric_tolerance=1e-6,
        limitations='Numeric differences cover shared feature names only; absent or differently named features are explicitly listed in feature_coverage. No shared features is not a numeric match. Metadata alignment is not an edge-set comparison. Labels and exact topology edges need separate evidence. Sample-fit statistics may differ from full-fit.'))
    print('Released feature sampling comparison written')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--include-inputs',action='store_true')
    parser.add_argument('--compare-released')
    args=parser.parse_args()
    if args.compare_released:compare(args.run,args.compare_released)
    else:collect(args.run,args.include_inputs)
