"""Verify source case indices before attaching Ground Truth time locators."""
import numpy as np


def locate_cases(dataset, example_indices, ground_truth):
    full=dataset['data']['train_valid']
    unlabeled=dataset['data']['unlabeled']
    # Reconstruct the public loader's exact index operation, then verify contents.
    indices=list(set(range(len(full['y'])))-set(example_indices))
    if len(indices)!=len(unlabeled['y']):
        raise ValueError('Unlabeled case count differs from source index reconstruction')
    result={}
    for case,index in enumerate(indices):
        if full['y_marker'][index]!=unlabeled['y_marker'][case] or not np.array_equal(full['y'][index],unlabeled['y'][case]):
            raise ValueError('Reconstructed case labels do not match actual prepared dataset')
        left,right=full['raw_data'][index],unlabeled['raw_data'][case]
        if len(left)!=len(right) or any(not np.array_equal(np.asarray(a),np.asarray(b),equal_nan=True) for a,b in zip(left,right)):
            raise ValueError('Reconstructed case observations differ from actual prepared dataset')
        interval=ground_truth['time_interval']['train_valid'][index]
        result[case]=dict(prepared_split='unlabeled',prepared_case_index=case,
            source_split='train_valid',source_case_index=index,date=interval[0],cloud_bed=interval[1],
            start_timestamp=int(interval[2]),end_timestamp=int(interval[3]),
            injected_entity=ground_truth['cmdb_id']['train_valid'][index],
            source_entity_type=ground_truth['entity_type']['train_valid'][index],
            source_root_cause_type=ground_truth['root_cause_type']['train_valid'][index],
            mapping_verified_by='source index operation plus all labels, markers and raw observation arrays')
    return result
