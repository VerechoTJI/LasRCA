from llm.common import *
import os
import json
import numpy as np


with open(f'{prompt_base_path}/iteration-{k}/explanation/record.json', encoding="utf-8") as f:
    record = json.load(f)


time_count = dict()
for i in range(len(record['sample_indices'])):
    start = time.time()

    print(f'{i}: start')
    sample_index, ent_index, prompt_type = record['sample_indices'][i], record['ent_indices'][i], record['prompt_types'][i]
    with open(f'{prompt_base_path}/explanation/{sample_index}/{ent_index}/{prompt_type}.txt', encoding="utf-8") as r:
        prompt = r.read()
    response_text = client.complete(prompt)
    save_dir = f'{response_base_path}/explanation/{sample_index}/{ent_index}'
    os.makedirs(save_dir, exist_ok=True)
    with open(f'{save_dir}/{prompt_type}.txt', 'w', encoding="utf-8") as w:
        w.write(response_text)

    end = time.time()
    time_count[f'{sample_index}-{ent_index}-{prompt_type}'] = end - start
    print(f'{i}: end')

with open(f'{base_path}/llm/time_count.json', 'w', encoding="utf-8") as f:
    json.dump(time_count, f, indent=2)

with open(f'{base_path}/llm/time_count.json', encoding="utf-8") as f:
    time_count = json.load(f)
print(np.average(list(time_count.values())))
