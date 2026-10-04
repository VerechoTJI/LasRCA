"""Compare actual paired means to visually verified paper reference tables."""
import argparse
import json
from pathlib import Path
from experiments.artifacts import sha256_file
from llm.export_evidence import write_csv
from llm.run_labeling import ROOT,write_json


def direction(value):
    return 'increase' if value>1e-10 else 'decrease' if value< -1e-10 else 'unchanged'


def compare(summary,reference):
    rows=[]
    fields=reference['metric_fields']
    for row in summary:
        kind,metric=row['entity_type'],row['metric']
        result=dict(row)
        if metric in fields:
            index=fields.index(metric)
            values=reference['classification'][kind]
            a,b=values['k0'][index],values['k1'][index]
            result.update(paper_k0=a,paper_k1=b,paper_delta_percentage_points=100*(b-a),
                paper_direction=direction(b-a),local_direction=direction(row['after_mean']-row['before_mean']),
                same_direction=direction(b-a)==direction(row['after_mean']-row['before_mean']),
                local_k1_minus_paper_percentage_points=100*(row['after_mean']-b),source_table='Table 4 V2/V1')
        elif metric in ('AC@1','AC@3','AC@5'):
            b=reference['localization_k1'][kind][metric]
            result.update(paper_k0=None,paper_k1=b,paper_delta_percentage_points=None,
                paper_direction=None,local_direction=direction(row['after_mean']-row['before_mean']),
                same_direction=None,local_k1_minus_paper_percentage_points=100*(row['after_mean']-b),
                source_table='Table 2 V1 only; paired k0 direction unavailable')
        else:
            continue # AC2/4/Avg5 are additional checks, absent from the required paper comparison.
        rows.append(result)
    return rows


def run(comparison,output):
    reference_path=ROOT/'docs/paper_reference_values.json'
    reference=json.loads(reference_path.read_text(encoding='utf-8'))
    value=json.loads(Path(comparison).read_text(encoding='utf-8'))
    rows=compare(value['summary'],reference)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'paper_comparison.json',dict(source=reference,source_pdf_sha256=sha256_file(reference['source']),
        comparison_path=str(Path(comparison).resolve()),rows=rows))
    write_csv(output/'paper_comparison.csv',rows)
    lines=['# Luna補標後指標與論文比較','',
        '本次k0／k1採相同五seeds與前處理；論文參照GPT-4、Table 4 V2／V1（無SRE correction）。Luna與clipping屬條件差異，不能把數值差全部歸因於模型替換。',
        '論文表只提供五次mean，未提供std，不能填0。',
        'Table 4可核對分類的提升方向；Table 2只列k1定位，沒有可直接核對的k0定位方向。',
        'MacroF1沿用公開程式sklearn逐類F1平均；論文Eq.9的macro P／R調和平均描述並非相同公式。',
        '',f"來源：[論文]({reference['source']})，PDF第9／10頁、印刷頁939／940。",'',
        '| Entity | Metric | 本次k0 mean ± std | 本次k1 mean ± std | 本次差(pp) | 論文k0→k1 | 分類方向一致 |',
        '|---|---|---|---|---|---|---|']
    for row in rows:
        original='N/A' if row['paper_k0'] is None else f"{row['paper_k0']:.4f} → {row['paper_k1']:.4f}"
        if row['paper_k0'] is None:original+=f"；k1={row['paper_k1']:.4f}"
        match='N/A' if row['same_direction'] is None else '是' if row['same_direction'] else '否'
        lines.append(f"| {row['entity_type']} | {row['metric']} | {row['before_mean']:.4f} ± {row['before_std']:.4f} | {row['after_mean']:.4f} ± {row['after_std']:.4f} | {row['delta_percentage_points']:+.2f} | {original} | {match} |")
    (output/'paper_comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--comparison',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    run(args.comparison,args.output)
