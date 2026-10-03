"""Arrange only already-extracted files within the isolated raw sample run."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]/'runs/lasrca/raw_20261004'


def prepare():
    routes = [
        (ROOT/'normal/cloudbed-1', ROOT/'inputs/normal/2022-03-19/cloudbed-1'),
        (ROOT/'extracted/training_data_with_faults/training_data_with_faults/tar/2022-03-20-cloudbed1',
         ROOT/'inputs/train_valid/2022-03-20/cloudbed-1'),
    ]
    for source, destination in routes:
        for path in (source,destination):
            if not path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('Raw staging path escapes isolated run')
        if not destination.exists():
            destination.parent.mkdir(parents=True,exist_ok=True)
            source.rename(destination)
    train_gt = ROOT/'inputs/groundtruth/train_valid'
    test_gt = ROOT/'inputs/groundtruth/test'
    train_gt.mkdir(parents=True,exist_ok=True)
    test_gt.mkdir(parents=True,exist_ok=True)
    original = ROOT/'extracted/training_data_with_faults/training_data_with_faults/groundtruth/groundtruth-k8s-1-2022-03-20.csv'
    shutil.copyfile(original,train_gt/original.name)
    config = dict(file={
        'normal':dict(base_folder=(ROOT/'inputs/normal').as_posix(),date=['2022-03-19'],cloud_bed=['cloudbed-1']),
        'train_valid':dict(base_folder=(ROOT/'inputs/train_valid').as_posix(),date=['2022-03-20'],cloud_bed=['cloudbed-1']),
        'test':dict(base_folder=(ROOT/'inputs/test').as_posix(),date=[],cloud_bed=['cloudbed'])},
        ground_truth={'train_valid':train_gt.as_posix(),'test':test_gt.as_posix()},
        temp_data_storage=(ROOT/'generated').as_posix())
    (ROOT/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print((ROOT/'config.json').as_posix())


if __name__=='__main__':
    prepare()
