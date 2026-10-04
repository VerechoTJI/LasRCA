"""Additional released-input encoder trial; execution support, not a new algorithm."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
import zipfile

from experiments.artifacts import sha256_file
from experiments.run_stage import capture_runtime_environment, execute_logged_command
from llm.run_labeling import ROOT, write_json


def inspect_public_inputs(source, temp_archive, model_archive):
    entry = 'temp_data/2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl'
    digest = hashlib.sha256()
    with zipfile.ZipFile(temp_archive) as archive, archive.open(entry) as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    actual = sha256_file(source)
    if digest.hexdigest() != actual:
        raise ValueError('Actual training input differs from the downloaded released archive')
    with zipfile.ZipFile(model_archive) as archive:
        entries = [name for name in archive.namelist() if not name.startswith('__MACOSX/')]
    return dict(dataset_path=str(source), archive_path=str(temp_archive), archive_entry=entry,
                archive_entry_sha256=digest.hexdigest(), actual_input_sha256=actual,
                input_matches_download=True, model_archive_path=str(model_archive),
                model_archive_entries=entries,
                ts2vec_weight_entries=[name for name in entries if any(
                    part in name.lower().split('/') for part in ('pretrain', 'ts2vec'))],
                comparison_reference='Author-provided embedding_600.pkl, not author TS2Vec weights')


def run(output, encoder_seed=406):
    output = Path(output).resolve()
    if (output/'status.json').exists():
        raise FileExistsError('Refusing to launch a duplicate recheck controller')
    output.mkdir(parents=True, exist_ok=True)
    state = dict(status='running', stage='input_verification', encoder_seed=encoder_seed,
                 downstream_seed=405, started_at=datetime.now(timezone.utc).isoformat())
    write_json(output/'status.json', state)
    try:
        source = ROOT/'temp_data/2022_CCF_AIOps_challenge/dataset/final/metric_trace_log.pkl'
        provenance = inspect_public_inputs(source, ROOT.parent/'temp_data.zip', ROOT.parent/'model.zip')
        write_json(output/'public_input_provenance.json', provenance)
        previous = json.loads((ROOT/'runs/lasrca/ts2vec_20261004/config.json').read_text())
        if previous['dataset_sha256'] != provenance['actual_input_sha256']:
            raise ValueError('Previous encoder used a different input; revise the protocol first')
        protocol = dict(entity='service', encoder_seed=encoder_seed, downstream_seed=405,
            previous_encoder_seed=previous['seed'], previous_input_sha256=previous['dataset_sha256'],
            input_matches_previous_trial=True, encoder_epochs=600, downstream_epochs=500,
            config=previous['config'], fit_splits=['normal','train_valid'], test_excluded_from_fit=True,
            source_sha256={name:sha256_file(ROOT/'code'/name) for name in (
                'pretrain.sh','pretrain/train.py','pretrain/data_loader.py','pretrain/data_encoder.py','pretrain/ts2vec.py')},
            relation_to_paper='Additional controlled trial; fixed seed and execution evidence are reproduction support',
            public_encoder_seed='Unavailable; the published training entry does not fix a recoverable seed')
        write_json(output/'protocol.json', protocol)
        encoder = output/f'ts2vec_seed{encoder_seed}'
        embeddings = output/'embeddings'
        downstream = output/'downstream'
        actions = [
            ('encoder_training', 'train', 'experiments.ts2vec_run',
             ['--output',encoder,'--seed',encoder_seed,'--entity','service','--epochs',600]),
            ('full_encoding', 'trace', 'experiments.encoder_downstream',
             ['encode','--output',embeddings,'--encoder-run',encoder]),
            ('paired_downstream', 'train', 'experiments.encoder_comparison',
             ['--output',downstream,'--own-embedding',embeddings/'service_replaced.pkl','--seed',405]),
        ]
        for stage, kind, module, args in actions:
            state.update(stage=stage)
            write_json(output/'status.json', state)
            # Preserve the uv interpreter; PATH resolves a different installation.
            directory = execute_logged_command(output/'execution',kind,
                [sys.executable,'-m',module]+list(map(str,args)),capture_runtime_environment(),
                working_directory=ROOT/'code',config=dict(stage=stage,protocol=str(output/'protocol.json')))
            state['last_execution'] = str(directory)
            manifest = json.loads((directory/'manifest.json').read_text())
            if manifest['exit_code'] != 0:
                raise RuntimeError(f'{stage} failed; inspect {directory}')
        encoded = json.loads((embeddings/'encoding_manifest.json').read_text())
        comparison = json.loads((downstream/'comparison.json').read_text())
        trained = json.loads((encoder/'summary.json').read_text())
        if encoded['replaced_sequences']!=150 or not comparison['split_labels_equal'] or trained['completed_epochs']!=600:
            raise ValueError('Encoding, training or downstream coverage is incomplete')
        state.update(status='completed',stage='finished',comparison=str(downstream/'comparison.json'),
                     completed_at=datetime.now(timezone.utc).isoformat())
        write_json(output/'status.json', state)
    except Exception as error:
        state.update(status='failed',error_type=type(error).__name__,message=str(error),
                     ended_at=datetime.now(timezone.utc).isoformat())
        write_json(output/'status.json', state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--encoder-seed', type=int, default=406)
    args = parser.parse_args()
    run(args.output, args.encoder_seed)
