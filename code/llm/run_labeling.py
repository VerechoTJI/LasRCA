"""Resume released-subgraph labeling without overwriting released artifacts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pickle
import runpy
import shutil
import sys
import time
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import patch

from llm.luna_oauth import LunaClient, MODEL

ROOT = Path(__file__).resolve().parents[2]
LLM = Path(__file__).resolve().parent
STAGES = ['first_stage','second_stage','third_stage','summarization_stage']


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


class ResumingClient:
    def __init__(self, directory, client):
        self.directory = Path(directory)
        self.client = client
        self.directory.mkdir(parents=True,exist_ok=True)

    def complete(self, prompt):
        digest = hashlib.sha256((MODEL+'\0'+prompt).encode()).hexdigest()
        path = self.directory/(digest+'.json')
        if path.exists():
            cached = json.loads(path.read_text(encoding='utf-8'))
            if cached['model'] != MODEL or cached['prompt'] != prompt:
                raise ValueError('Request cache mismatch')
            return cached['response']
        started = time.monotonic()
        response = self.client.complete(prompt)
        write_json(path,dict(model=MODEL,prompt=prompt,response=response,
            duration_seconds=time.monotonic()-started,metadata=getattr(self.client,'last_metadata',{})))
        return response


def run(output, limit=None):
    output = Path(output).resolve()
    base = ROOT/'temp_data/A'
    selected = base/'selected_samples/selected_samples_k_0.pkl'
    with selected.open('rb') as f:
        samples = pickle.load(f)
    fingerprint = hashlib.sha256(selected.read_bytes()).hexdigest()
    manifest = output/'manifest.json'
    if manifest.exists():
        old = json.loads(manifest.read_text(encoding='utf-8'))
        if old['selection_sha256'] != fingerprint or old['model'] != MODEL:
            raise ValueError('Cannot resume with changed selection/model')
    write_json(manifest,dict(model=MODEL,selection_path=str(selected),selection_sha256=fingerprint,
        total_cases=len(samples),selection_policy='released 100 cases/subgraphs'))
    client = ResumingClient(output/'requests',LunaClient())
    statuses = {}
    status_path = output/'status.json'
    if status_path.exists():
        statuses = json.loads(status_path.read_text(encoding='utf-8'))
    for sample in samples[:limit]:
        index = str(sample['sample_index'])
        if statuses.get(index,{}).get('status') == 'completed':
            continue
        common = ModuleType('common')
        common.__dict__.update(os=os,time=time,selected_samples=[sample],client=client,
            ent_pair_dict={'node':(0,6),'service':(6,16),'pod':(16,56)},
            ent_files={'node':['cpu','disk','memory'],'pod':['cpu','disk','memory','network','process']},
            prompt_base_path=str(output/'prompts'),response_base_path=str(output/'responses'))
        source = base/f'llm/prompts/iteration-0/stage-1/{index}'
        target = output/f'prompts/stage-1/{index}'
        stage = 'prompt_copy'
        try:
            if source.exists():
                shutil.copytree(source,target,dirs_exist_ok=True)
            with patch.dict(sys.modules,{'common':common}),patch.object(sys,'path',[str(LLM)]+sys.path):
                for stage in STAGES:
                    runpy.run_path(str(LLM/(stage+'.py')))
            statuses[index] = {'status':'completed'}
            print(f'case {index}: four stages completed',flush=True)
        except Exception as error:
            statuses[index] = dict(status='failed',stage=stage,error_type=type(error).__name__,message=str(error))
            # Reproduction-only attempt history; never replaces a successful answer.
            error_path = output/'errors/execution_attempts.jsonl'
            error_path.parent.mkdir(parents=True,exist_ok=True)
            category = 'missing_prompt_or_path' if isinstance(error,FileNotFoundError) else 'oauth_or_api' if type(error).__name__=='OAuthError' else 'other'
            attempt = dict(case_index=int(index),stage=stage,error_category=category,
                error_type=type(error).__name__,message=str(error),http_status=getattr(error,'status_code',None),
                observed_at=datetime.now(timezone.utc).isoformat(),status='failed')
            with error_path.open('a',encoding='utf-8') as f:
                f.write(json.dumps(attempt,ensure_ascii=False)+'\n')
            print(f'case {index}: failed at {stage} ({type(error).__name__})',flush=True)
            # Authentication/quota/network failures can affect every case; stop to avoid request storms.
            if type(error).__name__ == 'OAuthError':
                write_json(status_path,statuses)
                raise
        write_json(status_path,statuses)
    write_json(output/'summary.json',dict(total_cases=len(samples),completed=sum(
        s['status']=='completed' for s in statuses.values()),failed=sum(s['status']=='failed' for s in statuses.values())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--limit',type=int)
    args = parser.parse_args()
    run(args.output,args.limit)
