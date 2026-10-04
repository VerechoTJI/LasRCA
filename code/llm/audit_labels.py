"""Offline diagnostic audit. Ground truth never enters the labeling prompts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import pickle

from llm.build_labeled_dataset import parse_summary, update_labels
from llm.run_labeling import ROOT, write_json
from llm.case_locators import locate_cases


def audit(run_directory):
    run_directory = Path(run_directory)
    base = ROOT/'temp_data/A'
    with (base/'selected_samples/selected_samples_k_0.pkl').open('rb') as f:
        samples = pickle.load(f)
    with (base/'metric_trace_log/dataset/narrow_few_shot_train_size_1.pkl').open('rb') as f:
        dataset = pickle.load(f)
    gt_path=ROOT/'temp_data/2022_CCF_AIOps_challenge/dataset/time_interval_and_label/time_interval_window_size_9.pkl'
    with gt_path.open('rb') as f: ground_truth=pickle.load(f)
    examples=json.loads((base/'example_selection/example_1.json').read_text(encoding='utf-8'))
    locators=locate_cases(dataset,examples['final_batch_indices'],ground_truth)
    write_json(run_directory/'audit/case_locators.json',dict(ground_truth_path=str(gt_path),cases=locators))
    statuses = json.loads((run_directory/'status.json').read_text(encoding='utf-8'))
    completed = [s for s in samples if statuses.get(str(s['sample_index']),{}).get('status')=='completed']
    summaries, parse_errors = {}, []
    for sample in completed:
        index = int(sample['sample_index'])
        try:
            summaries[index] = parse_summary((run_directory/f'responses/summarization/{index}.txt').read_text(encoding='utf-8'))
        except ValueError as error:
            parse_errors.append(dict(case=index,error_type='parse_error',message=str(error)))
    _, rows = update_labels(dataset,completed,summaries)
    actual_path=run_directory/'dataset/label_changes.json'
    actual=json.loads(actual_path.read_text(encoding='utf-8')) if actual_path.exists() else None
    if actual is not None:
        actual_by_key={(r['case'],r['entity']):r for r in actual}
        if any(actual_by_key.get((r['case'],r['entity']))!=r for r in rows):
            raise ValueError('Audit simulation differs from recorded formal update')
    for row in rows:
        row['case_locator']=locators[row['case']]
        row['dataset_update_verified']=actual is not None
    errors = []
    for row in rows:
        kinds = []
        if row['status']!='applied':
            kinds.append(row['status'])
        elif row['y_after'] != row['ground_truth']:
            kinds.append('label_disagrees_with_ground_truth')
        if kinds:
            name = row['entity']
            gt = row.get('ground_truth')
            row['ground_truth_name'] = 'No Fault' if gt==0 else dataset['meta_data']['en_fault_type_list'][gt-1] if gt else None
            row['error_types'] = kinds
            response = run_directory/f'responses/summarization/{row["case"]}.txt'
            row['response_path'] = str(response.resolve())
            row['raw_response'] = response.read_text(encoding='utf-8') if response.exists() else None
            row['explanation_path'] = str((run_directory/f'responses/stage-3/{row["case"]}.txt').resolve())
            errors.append(row)
    output = run_directory/'audit'
    write_json(output/'errors.json',dict(parse_errors=parse_errors,entity_errors=errors,all_label_changes=rows))
    counts = Counter(kind for row in errors for kind in row['error_types'])
    write_json(output/'summary.json',dict(selected_cases=len(samples),completed_cases=len(completed),
        entity_denominator=len(rows),error_entities=len(errors),error_cases=len({e['case'] for e in errors}),
        parse_errors=len(parse_errors),error_type_counts=dict(counts),dataset_written=actual is not None,
        update_evidence_path=str(actual_path) if actual is not None else None))
    lines = ['# Luna 補標錯誤分析（離線）','',
        f'公開選取 {len(samples)} 案例，目前完整完成 {len(completed)} 案例。以下僅分析完成部分，不能推估全部100案例錯誤率。',
        f'分母為完成案例中的 {len(rows)} 個 entity；{len(errors)} 個 entity 與 Ground Truth 不一致或格式異常。',
        '多個錯誤 entity 可來自同一案例；不足10個不同錯誤案例時全部列出，不製造案例。',
        ('已逐項核對正式 Dataset 更新紀錄；Ground Truth 僅用於分析。' if actual is not None else '本分析模擬 Dataset 更新，未寫入正式 Dataset。Ground Truth 僅用於分析。'),'',
        '| Case | Entity | Ground Truth | Luna label | 錯誤 | y/mask 更新 |', '|---|---|---|---|---|---|']
    for row in errors[:20]:
        lines.append(f"| {row['case']} | {row['entity']} | {row['ground_truth_name']} | {row.get('llm_label')} | {', '.join(row['error_types'])} | {row.get('y_before')}/{row.get('mask_before')} → {row.get('y_after')}/{row.get('mask_after')} |")
    lines += ['','原始 response、stage-3 explanation 路徑及全部逐entity差異保存在同目錄 errors.json。',
        'LLM 與 Ground Truth 不一致是可觀察結果，尚不能僅由最終回答判定第一階段／整合階段／摘要階段哪一步造成；需對照原始階段回答。']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(completed_cases=len(completed),entity_denominator=len(rows),error_entities=len(errors))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir',required=True)
    args = parser.parse_args()
    audit(args.run_dir)
