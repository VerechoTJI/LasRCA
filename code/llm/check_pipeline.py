"""Run one released subgraph through unchanged stage scripts in a temporary folder."""
import argparse
import ast
import json
import os
from pathlib import Path
import pickle
import runpy
import shutil
import sys
import tempfile
import time
from types import ModuleType
from unittest.mock import patch

from .luna_oauth import LunaClient

ROOT = Path(__file__).resolve().parents[2]
LLM = Path(__file__).resolve().parent


def run_pipeline(client):
    base = ROOT / 'temp_data/A'
    with (base/'selected_samples/selected_samples_k_0.pkl').open('rb') as f:
        samples = pickle.load(f)
    pairs = {'node':(0,6),'service':(6,16),'pod':(16,56)}
    files = {'node':['cpu','disk','memory'],'pod':['cpu','disk','memory','network','process']}
    def calls(sample):
        return sum(4 if i < 6 else 6 if i >= 16 else 0 for i in sample['ent_indices'])
    sample = min((s for s in samples if calls(s)),key=calls)
    with tempfile.TemporaryDirectory(prefix='lasrca-luna-') as tmp:
        prompts, responses = Path(tmp)/'prompts', Path(tmp)/'response'
        shutil.copytree(base/f'llm/prompts/iteration-0/stage-1/{sample["sample_index"]}',
            prompts/f'stage-1/{sample["sample_index"]}')
        common = ModuleType('common')
        common.__dict__.update(os=os,time=time,selected_samples=[sample],client=client,
            ent_pair_dict=pairs,ent_files=files,prompt_base_path=str(prompts),response_base_path=str(responses))
        with patch.dict(sys.modules,{'common':common}), patch.object(sys,'path',[str(LLM)]+sys.path):
            for stage in ['first_stage','second_stage','third_stage','summarization_stage']:
                runpy.run_path(str(LLM/(stage+'.py')))
        result = (responses/f'summarization/{sample["sample_index"]}.txt').read_text()
        # Use exactly the original downstream extraction logic, without writing dataset labels.
        source = ast.parse((LLM/'update_dataset.py').read_text())
        fn = next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='extract_json_blobs')
        scope = {'json':json}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<original parser>','exec'),scope)
        labels = scope['extract_json_blobs'](result.replace("'",'"'))
        if not isinstance(labels,dict) or set(labels) != set(sample['ent_names']):
            raise ValueError('Summary entities do not match the selected subgraph.')
        with (base/'metric_trace_log/dataset/narrow_few_shot_train_size_1.pkl').open('rb') as f:
            dataset = pickle.load(f)
        allowed = set(dataset['meta_data']['en_fault_type_list']) | {'No Fault','Node Disk Space IO Consumption'}
        for value in labels.values():
            fault = value.get('exact_fault_type')
            if not isinstance(fault,str) or (fault not in allowed and fault.lower() != 'no fault'):
                raise ValueError('Summary fault type cannot be consumed by the original label mapping.')
        return {'sample_index':int(sample['sample_index']),'stages':4,
            'requests':calls(sample)+2,'entities':len(labels),'compatible':True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(run_pipeline(LunaClient())))
