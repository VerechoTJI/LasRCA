import argparse
import json
from pathlib import Path
import statistics
import csv
from experiments.evaluation_output import METRIC_FIELDS


def compare_records(before, after):
    def index(records):
        mapping = {(r['seed'],r['entity_type']):r for r in records}
        if len(mapping) != len(records):
            raise ValueError('Duplicate seed/entity metric record')
        return mapping
    b, a = index(before), index(after)
    if set(b) != set(a) or not b:
        raise ValueError('Before/after seed and entity sets must match exactly')
    rows, groups = [], {}
    for key in sorted(b):
        if b[key]['ground_truth_sha256'] != a[key]['ground_truth_sha256']:
            raise ValueError('Before/after ground truth differs')
        for metric in METRIC_FIELDS:
            if (metric in b[key]) != (metric in a[key]):
                raise ValueError('Before/after metric fields differ')
            if metric not in b[key]:
                continue
            x, y = float(b[key][metric]),float(a[key][metric])
            rows.append(dict(seed=key[0],entity_type=key[1],metric=metric,before=x,after=y,
                delta_percentage_points=100*(y-x),relative_percent=100*(y-x)/x if x else None))
            groups.setdefault((key[1],metric),[]).append((x,y))
    summary = []
    for (entity,metric), values in sorted(groups.items()):
        x, y = zip(*values)
        bx, ay = statistics.fmean(x),statistics.fmean(y)
        summary.append(dict(entity_type=entity,metric=metric,count=len(values),before_mean=bx,
            before_std=statistics.pstdev(x),after_mean=ay,after_std=statistics.pstdev(y),
            delta_percentage_points=100*(ay-bx),relative_percent=100*(ay-bx)/bx if bx else None))
    return rows, summary


def write_report(before_path, after_path, output):
    before = json.loads(Path(before_path).read_text(encoding='utf-8'))
    after = json.loads(Path(after_path).read_text(encoding='utf-8'))
    rows, summary = compare_records(before,after)
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    (output/'comparison.json').write_text(json.dumps(dict(per_seed=rows,summary=summary),indent=2),encoding='utf-8')
    for name,records in [('per_seed_comparison.csv',rows),('summary_comparison.csv',summary)]:
        with (output/name).open('x',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]))
            writer.writeheader();writer.writerows(records)
    lines = ['# k=0／k=1 成對比較','','同 seed／entity 配對；std 採母體標準差（ddof=0）。絕對差為百分點；baseline=0 時相對差為 N/A。',
        '',f'k=0: {Path(before_path).resolve()}',f'k=1: {Path(after_path).resolve()}',
        '','| Entity | Metric | k=0 mean ± std | k=1 mean ± std | 差（百分點） | 相對差 |',
        '|---|---|---|---|---|---|']
    for r in summary:
        relative = 'N/A' if r['relative_percent'] is None else f"{r['relative_percent']:.2f}%"
        lines.append(f"| {r['entity_type']} | {r['metric']} | {r['before_mean']:.4f} ± {r['before_std']:.4f} | {r['after_mean']:.4f} ± {r['after_std']:.4f} | {r['delta_percentage_points']:+.2f} | {relative} |")
    lines += ['','需另核對相同前處理及 split；本表不把替代模型條件當作原 GPT-4 重現，也不推定結果改善。論文數值須另由原表確認後比較。']
    (output/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--before',required=True)
    parser.add_argument('--after',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    write_report(args.before,args.after,args.output)
