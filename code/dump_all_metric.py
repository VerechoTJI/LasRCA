import os
import pickle
import pprint
from pathlib import Path

# Resolve paths relative to this script file so it works regardless of CWD
script_dir = Path(__file__).resolve().parent
pkl_path = (script_dir / '..' / 'temp_data' / '2022_CCF_AIOps_challenge' / 'dataset' / 'metric' / 'all_metric.pkl').resolve()
dump_path = (script_dir / '..' / 'temp_data' / '2022_CCF_AIOps_challenge' / 'dataset' / 'metric' / 'all_metric.dump').resolve()

print(f"Loading: {pkl_path}")
try:
    with open(pkl_path,'rb') as f:
        obj = pickle.load(f)
except Exception as e:
    # try loading with latin1 for numpy arrays pickled in py2/py3
    try:
        with open(pkl_path,'rb') as f:
            obj = pickle.load(f, encoding='latin1')
    except Exception as e2:
        print('Failed to load pickle:', e)
        raise

# Pretty format and write
try:
    text = pprint.pformat(obj, width=200, compact=False)
except Exception:
    text = repr(obj)

with open(dump_path, 'w', encoding='utf-8') as out:
    out.write(text)

print(f"Wrote dump to: {dump_path}")
