"""Offline reproduction evidence; not part of the paper's labeling algorithm."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import pickle

from llm.build_labeled_dataset import parse_summary, update_labels
from llm.run_labeling import ROOT, MODEL, write_json


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_usage(requests):
    total = dict(successful_unique_requests=len(requests), missing_usage=0,
                 input_tokens=0, output_tokens=0, total_tokens=0)
    returned = Counter()
    for request in requests:
        metadata = request.get('metadata', {})
        returned[str(metadata.get('returned_model'))] += 1
        usage = metadata.get('usage')
        if usage is None:
            total['missing_usage'] += 1
            continue
        for field in ('input_tokens', 'output_tokens', 'total_tokens'):
            if field not in usage:
                raise ValueError('Usage missing ' + field)
            total[field] += int(usage[field])
    total['returned_models'] = dict(returned)
    total['counting_policy'] = 'unique successful request hashes; cached reuse is not a new request'
    return total


def api_equivalent_cost(requests):
    """Public Standard API price benchmark, never an OAuth subscription charge."""
    price=0.0
    missing=0
    for request in requests:
        usage=request.get('metadata',{}).get('usage')
        if not usage:
            missing+=1
            continue
        inputs=int(usage['input_tokens'])
        outputs=int(usage['output_tokens'])
        cached=int((usage.get('input_tokens_details') or {}).get('cached_tokens',0))
        if not 0<=cached<=inputs:
            raise ValueError('Cached tokens exceed input tokens')
        long_context=inputs>272000
        price+=((inputs-cached)*.10+cached*.01)*(2 if long_context else 1)/1e6
        price+=outputs*.50*(1.5 if long_context else 1)/1e6
    return dict(cost_kind='public_standard_API_equivalent_estimate_not_actual_OAuth_charge',currency='USD',
        estimated_api_equivalent_cost=price,actual_oauth_charge=None,missing_usage_requests=missing,
        pricing_date='2026-10-04',pricing_source='https://developers.openai.com/api/docs/models/gpt-6-luna',
        oauth_billing_source='https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions',
        rates_per_million=dict(input=.10,cached_input=.01,output=.50),
        assumptions='Standard API-equivalent text price; >272K prompt multipliers applied. No regional/Flex/Batch/Fast premium assumed; no separately reported cache writes.',
        actual_charge_limitation='OAuth uses ChatGPT plan/credits; actual account usage or charges require ChatGPT Settings Usage. API-equivalent estimate is not the user bill.')


def export(run):
    run = Path(run).resolve()
    with (ROOT/'temp_data/A/selected_samples/selected_samples_k_0.pkl').open('rb') as f:
        samples = pickle.load(f)
    with (ROOT/'temp_data/A/metric_trace_log/dataset/narrow_few_shot_train_size_1.pkl').open('rb') as f:
        dataset = pickle.load(f)
    states = json.loads((run/'status.json').read_text(encoding='utf-8'))
    summaries, parse_errors = {}, []
    explanations, associations, usage_rows = [], [], []
    requests = {}
    for path in sorted((run/'requests').glob('*.json')):
        requests[path.stem] = json.loads(path.read_text(encoding='utf-8'))
    for path in sorted((run/'prompts').rglob('*.txt')):
        relative = path.relative_to(run/'prompts').parts
        stage, case = relative[0], relative[1].split('.')[0]
        prompt = path.read_text(encoding='utf-8')
        digest = hashlib.sha256((MODEL+'\0'+prompt).encode()).hexdigest()
        associations.append(dict(case_index=int(case), stage=stage,
            entity_index=int(relative[2].split('.')[0]) if stage in ('stage-1','stage-2') else None,
            observation_category=path.stem if stage=='stage-1' else None,
            prompt_path=str(path), request_hash=digest, request_saved=digest in requests))
    for sample in samples:
        case = int(sample['sample_index'])
        if states.get(str(case), {}).get('status') != 'completed':
            continue
        path = run/f'responses/summarization/{case}.txt'
        try:
            summaries[case] = parse_summary(path.read_text(encoding='utf-8'))
        except (ValueError, FileNotFoundError) as error:
            parse_errors.append(dict(case_index=case, response_path=str(path),error_type=type(error).__name__,message=str(error)))
        explanation_path = run/f'responses/stage-3/{case}.txt'
        text = explanation_path.read_text(encoding='utf-8') if explanation_path.exists() else None
        for name in sample['ent_names']:
            explanations.append(dict(case_index=case,entity_name=name,explanation_text=text,
                source_stage='stage-3',source_path=str(explanation_path),
                extraction_status='case_level_original_response' if text else 'missing'))
    completed_samples = [s for s in samples if states.get(str(s['sample_index']),{}).get('status')=='completed']
    _, labels = update_labels(dataset, completed_samples, summaries)
    faults=dataset['meta_data']['en_fault_type_list']
    for row in labels:
        row['case_index'] = row['case']
        row['raw_exact_fault_type'] = row.get('llm_label')
        row['label_id'] = row.get('y_after') if row['status']=='applied' else None
        row['parse_status'] = 'failed' if row['case'] not in summaries else 'parsed'
        row['response_path'] = str(run/f'responses/summarization/{row["case"]}.txt')
        row['normalization_status'] = row['status']
        if row['status']=='applied':
            row['normalized_fault_type'] = 'No fault' if row['y_after']==0 else faults[row['y_after']-1]
    errors = [r for r in labels if r['status']!='applied']
    write_json(run/'labels/parsed_labels.json',labels)
    write_csv(run/'labels/parsed_labels.csv', labels)
    write_json(run/'labels/explanations.json',explanations)
    write_json(run/'labels/validation_errors.json',dict(parse_errors=parse_errors,entity_errors=errors))
    write_csv(run/'usage/request_associations.csv', associations)
    for digest, request in requests.items():
        metadata = request.get('metadata',{})
        usage = metadata.get('usage') or {}
        usage_rows.append(dict(request_hash=digest, requested_model=request['model'],
            returned_model=metadata.get('returned_model'),duration_seconds=request['duration_seconds'],
            input_tokens=usage.get('input_tokens'),output_tokens=usage.get('output_tokens'),total_tokens=usage.get('total_tokens'),
            usage_details=json.dumps(usage)))
    write_csv(run/'usage/request_usage.csv', usage_rows)
    write_json(run/'usage/summary.json',summarize_usage(list(requests.values())))
    write_json(run/'usage/cost.json',api_equivalent_cost(list(requests.values())))
    execution_errors = [dict(case_index=int(case),**state,observed_time=None,
        record_kind='latest_failed_case_status_not_additional_attempt',
        historical_fields_limitation='Older status has no attempt timestamp or HTTP status')
        for case,state in states.items() if state['status']=='failed']
    history=[]
    attempts = run/'errors/execution_attempts.jsonl'
    if attempts.exists():
        history.extend(json.loads(line) for line in attempts.read_text(encoding='utf-8').splitlines() if line)
    historical=run/'errors/historical_inspection_failures.json'
    if historical.exists():history.extend(json.loads(historical.read_text(encoding='utf-8')))
    execution_errors.extend(history)
    write_json(run/'errors/execution_errors.json',execution_errors)
    n=len(completed_samples)
    expected=sum(len(s['ent_names']) for s in samples)
    valid=sum(r['status']=='applied' for r in labels)
    failed_cases=sum(states.get(str(s['sample_index']),{}).get('status')=='failed' for s in samples)
    report=dict(total_cases=len(samples),completed_cases=n,failed_cases=failed_cases,
        pending_cases=len(samples)-n-failed_cases,execution_completion_rate=n/len(samples),
        parseable_cases=len(summaries),parse_errors=len(parse_errors),total_expected_entity_occurrences=expected,
        completed_entity_occurrences=sum(len(s['ent_names']) for s in completed_samples),valid_entity_labels=valid,
        valid_label_rate=valid/expected,entity_validation_counts=dict(Counter(r['status'] for r in labels)),
        recorded_failed_attempts=len(history),execution_failure_counts=dict(Counter(r.get('error_category','unknown') for r in history)),
        historical_failure_coverage='Old runner has incomplete attempt history; recovered failures are reported separately from currently failed cases',
        dataset_written_by_export=False,formal_dataset_exists=(run/'dataset/k1_luna.pkl').exists(),
        explanation_scope='Case-level original stage-3 text, not independently extracted entity reasons',
        partial=n!=len(samples),files_are_current_snapshot=True)
    write_json(run/'labeling_report.json',report)
    (run/'labeling_report.md').write_text('# Luna 標註紀錄（非論文演算法）\n\n'+
        f'完成 {n}/{len(samples)} cases；可解析 {len(summaries)} cases；有效標籤 {valid}/{expected} entity occurrences。\n\n'+
        f'目前失敗案例 {failed_cases}；已保存歷史失敗紀錄 {len(history)}。舊runner歷史覆蓋不完整，兩者不能當同一分母。\n\n'+
        'parsed_labels、explanations、validation_errors、request usage／關聯與原始四階段文字另存。理由保留第三階段case層級原文，不假造entity理由。本匯出不修改dataset；正式補標檔是否存在另記formal_dataset_exists。cost.json提供公開Standard API等值成本估算，OAuth帳號實際計費仍不可得，不把估算當實付或填零。\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',required=True)
    export(parser.parse_args().run_dir)
