"""Run source preprocessing stages against explicitly isolated input/output paths."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from experiments.artifacts import collect_artifacts

MODULES = [
 'dao.topology_dao','service.ent_edge_index_generator','service.time_interval_label_generator',
 'dao.metric_dao','service.metric_generator','dao.trace_dao','service.trace_generator',
 'dao.log_dao','service.log_generator','service.dataset_generator',
]


def run(config, output, stages):
    output = Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    config = Path(config).resolve()
    settings = json.loads(config.read_text(encoding='utf-8'))
    storage = Path(settings['temp_data_storage']).resolve()
    if output not in storage.parents:
        raise ValueError('Preprocessing storage must stay inside the isolated output directory')
    environment = dict(os.environ,LASRCA_PREPROCESS_CONFIG=str(config),PYTHONUTF8='1')
    statuses = {}
    state = output/'pipeline_status.json'
    if state.exists():
        statuses = json.loads(state.read_text(encoding='utf-8'))
    for module in stages:
        if module not in MODULES:
            raise ValueError('Unknown preprocessing module')
        if statuses.get(module,{}).get('exit_code') == 0:
            continue
        start = time.monotonic()
        command = [sys.executable,'-m','data_filter.CCF_AIOps_challenge_2022.'+module]
        with (output/(module.replace('.','_')+'.log')).open('w',encoding='utf-8') as log:
            result = subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
        statuses[module] = dict(command=command,exit_code=result.returncode,duration_seconds=time.monotonic()-start)
        state.write_text(json.dumps(statuses,indent=2),encoding='utf-8')
        print(f'{module}: exit {result.returncode}',flush=True)
        if result.returncode:
            raise RuntimeError(f'Preprocessing failed at {module}; inspect its log')
    (output/'artifact_manifest.json').write_text(json.dumps(collect_artifacts(storage),indent=2),encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--stages',nargs='+',default=MODULES)
    args = parser.parse_args()
    run(args.config,args.output,args.stages)
