"""Complete stage accounting from retained artifact schemas; no preprocessing changes."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil

from experiments.artifacts import sha256_file
from experiments.raw_evidence import producing_stage,consuming_stages,inspect_value
from experiments.raw_pipeline import MODULES
from llm.export_evidence import write_csv
from llm.run_labeling import ROOT,write_json


def field_counts(schema):
    """Keep nested units distinct; never sum parent and child containers as records."""
    if isinstance(schema,dict):
        if 'rows' in schema:
            return [dict(field_path='',count=schema['rows'],unit='CSV_records',aggregate=True),
                    dict(field_path='',count=schema.get('non_null_non_timestamp_cells',0),
                         unit='non_null_non_timestamp_cells',aggregate=True)]
        return [dict(field_path='',count=1,unit='opaque_files',aggregate=True)]
    results=[]
    for row in schema:
        field=row['field_path']
        kind=row['kind']
        count=row.get('count')
        if kind=='DataFrame':
            processed='raw' if field.startswith('/raw_data/') else 'processed'
            results.extend([dict(field_path=field,count=row['rows'],unit=processed+'_observation_rows',aggregate=True),
                dict(field_path=field,count=row['shape'][0]*max(0,row['shape'][1]-int('timestamp' in row['columns'])),
                     unit=processed+'_feature_cells',aggregate=True)])
            continue
        if kind=='ndarray':
            shape=row['shape']
            if len(shape)==2 and shape[0]==2 and ('edge' in field or field==''):
                count=shape[1];unit='stored_directed_edges'
            elif field.startswith('/y/') or '/labels/' in field:unit='entity_label_values'
            else:unit='array_elements'
            results.append(dict(field_path=field,count=count,unit=unit,aggregate=True))
            continue
        if kind=='list' and field.startswith('/time_interval/') and field.count('/')==2:
            unit='time_windows';aggregate=True
        elif kind=='list' and field.startswith('/y/') and field.count('/')==2:
            unit='label_vectors';aggregate=True
        else:
            unit={'dict':'mapping_entries','list':'list_items','tuple':'tuple_fields'}.get(kind,'scalar_fields')
            aggregate=False
        results.append(dict(field_path=field,count=1 if count is None else count,unit=unit,aggregate=aggregate))
    return results


def source_consumers(record,config,metric_settings):
    path=Path(record['path'])
    relative=Path(record['relative_path'])
    role=record['role']
    if not role.startswith('input_'):return consuming_stages(relative,role)
    parts=relative.parts
    split=role[len('input_'):]
    scope=config['file'][split]
    if len(parts)<4 or parts[0] not in scope['date'] or parts[1] not in scope['cloud_bed']:
        return []
    if parts[0]=='2022-03-24' and parts[1] in ('cloudbed-1','cloudbed-2'):return []
    if path.suffix!='.csv':return []
    if parts[2]=='metric':
        resource=parts[3]
        if resource in ('node','service'):
            # The public loader explicitly reads glob(...)[0], not all CSVs.
            files=list(path.parent.glob('*.csv'))
            used=bool(files) and path==files[0]
        elif resource in ('container','istio'):
            names={name+'.csv' for group in metric_settings['related_metrics'][resource].values() for name in group}
            used=path.name in names
        else:used=False
        return ['dao.metric_dao'] if used else []
    if parts[2]=='trace' and path.name=='trace_jaeger-span.csv':return ['dao.trace_dao']
    if parts[2]=='log' and path.name=='log_filebeat-testbed-log-service.csv':return ['dao.log_dao']
    return []


def run(run_dir):
    run_dir=Path(run_dir).resolve()
    records=[r for r in json.loads((run_dir/'stage_counts.json').read_text()) if r['role']!='configuration']
    config=json.loads((run_dir/'config.json').read_text())
    metric_settings=json.loads((ROOT/'code/data_filter/CCF_AIOps_challenge_2022/config/metric_setting.json').read_text())
    schemas=json.loads((run_dir/'stage_schemas.json').read_text())
    state=json.loads((run_dir/'pipeline_status.json').read_text())
    for module in MODULES:
        if state.get(module,{}).get('exit_code')!=0:raise ValueError('Preprocessing is not complete: '+module)
    backup=run_dir/'accounting_before_correction_20261005'
    if not backup.exists():
        backup.mkdir()
        for name in ('stage_counts.json','stage_counts.csv','stage_input_output_counts.csv','final_manifest.json'):
            shutil.copy2(run_dir/name,backup/name)
    unknown=[]
    for record in records:
        relative=Path(record['relative_path'])
        record['producing_stage']=producing_stage(relative) if record['role']=='output' else 'source'
        record['consuming_stages']=source_consumers(record,config,metric_settings)
        if record['role']=='output' and record['producing_stage']=='unknown':unknown.append(record['path'])
    if unknown:raise ValueError('Unresolved producer: '+str(unknown))
    # Every script constructs DataConfig. Topology has no raw observation input:
    # its entities/scopes come from these config files and relations from source.
    inputs=[run_dir/'config.json',ROOT/'code/data_filter/CCF_AIOps_challenge_2022/config/metric_setting.json',
            ROOT/'code/data_filter/CCF_AIOps_challenge_2022/config/service_knowledge.json']
    for path in inputs:
        value=json.loads(path.read_text(encoding='utf-8'))
        schemas[str(path)]=inspect_value(value)
        records.append(dict(role='configuration',path=str(path),relative_path=path.name,
            producing_stage='source',consuming_stages=list(MODULES),bytes=path.stat().st_size,
            sha256=sha256_file(path),schema_ref=str(path),status='inspected'))
    drain=ROOT/'code/data_filter/CCF_AIOps_challenge_2022/config/drain3.ini'
    schemas[str(drain)]={'kind':'file','unit':'configuration_files'}
    records.append(dict(role='configuration',path=str(drain),relative_path=drain.name,producing_stage='source',
        consuming_stages=['dao.log_dao'],bytes=drain.stat().st_size,sha256=sha256_file(drain),schema_ref=str(drain),status='inspected'))
    details=[]
    artifacts=defaultdict(set)
    totals=defaultdict(int)
    for record in records:
        measures=field_counts(schemas[record['schema_ref']])
        record['count_measures']=measures
        flows=[('input',module) for module in record['consuming_stages']]
        if record['role']=='output':flows.append(('output',record['producing_stage']))
        for direction,module in flows:
            artifacts[(module,direction)].add(record['path'])
            for measure in measures:
                row=dict(module=module,direction=direction,path=record['path'],role=record['role'],
                    schema_ref=record['schema_ref'],artifact_family=Path(record['path']).name,**measure)
                details.append(row)
                if measure['aggregate']:totals[(module,direction,row['artifact_family'],row['unit'])]+=row['count']
    summary=[dict(module=module,direction=direction,artifact_family=family,unit=unit,count=count)
             for (module,direction,family,unit),count in sorted(totals.items())]
    stages=[dict(module=module,input_files=len(artifacts[(module,'input')]),
        output_files=len(artifacts[(module,'output')]),duration_seconds=state[module]['duration_seconds'],exit_code=0,
        input_count_measures=[r for r in summary if r['module']==module and r['direction']=='input'],
        output_count_measures=[r for r in summary if r['module']==module and r['direction']=='output']) for module in MODULES]
    if any(not row['input_count_measures'] or not row['output_count_measures'] for row in stages):
        raise ValueError('A script still lacks numeric input/output measures')
    write_csv(run_dir/'stage_input_output_counts.csv',details)
    write_csv(run_dir/'stage_count_summary.csv',summary)
    write_json(run_dir/'stage_script_summary.json',stages)
    write_json(run_dir/'stage_counts.json',records)
    write_json(run_dir/'stage_schemas.json',schemas)
    write_csv(run_dir/'stage_counts.csv',records)
    manifest=json.loads((backup/'final_manifest.json').read_text())
    manifest.update(artifacts=records,accounting_revision='2026-10-05',unknown_producers=unknown,
        limitations='Unique dependency artifacts inferred from published source, not instrumented repeated reads. Same-stage reads are included once per file. Nested mapping/list/scalar counts remain explicit but are not added to observation totals. Aggregation separates unit and filename; different window sizes stay separate. Topology input is configuration, not invented raw events.')
    write_json(run_dir/'final_manifest.json',manifest)
    report=['# 前處理逐script輸入／輸出核對','',manifest['limitations'],'',
        '| Script | 輸入檔 | 輸出檔 | 秒 | Exit |','|---|---:|---:|---:|---:|']
    report.extend(f"| {r['module']} | {r['input_files']} | {r['output_files']} | {r['duration_seconds']:.3f} | 0 |" for r in stages)
    report+=['','具體數量與單位：stage_count_summary.csv；逐檔／欄位完整數量：stage_input_output_counts.csv；各script的成組數量：stage_script_summary.json。',
        '全部10scripts都有明確numeric input/output measures，unknown producer=0。舊表保留在accounting_before_correction_20261005；未重跑模型或前處理。']
    (run_dir/'stage_accounting.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(f'Accounted {len(stages)} scripts, {len(details)} field measures, 0 unknown producers')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    run(args.run)
