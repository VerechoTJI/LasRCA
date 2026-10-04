import numpy as np


def _base_entity_name(entity_name):
    return (
        entity_name.replace("2-0", "")
        .replace("-0", "")
        .replace("-1", "")
        .replace("-2", "")
    )


def _statistic_key(feature_template, entity_name):
    parts = feature_template.split(";")
    if len(parts) != 3:
        raise ValueError(f"unexpected trace feature name: {feature_template}")
    return f"{parts[0]}; cmdb_id: {_base_entity_name(entity_name)};{parts[2]}"


def _trace_statistics_in_feature_order(meta_data, statistics):
    ordered_statistics = []
    for entity_type in meta_data["ent_types"]:
        feature_count = meta_data["ent_feature_num"][entity_type]["trace"]
        if feature_count == 0:
            continue
        templates = meta_data["o11y_names"][entity_type]["trace"]
        if len(templates) != feature_count:
            raise ValueError(
                f"trace feature metadata mismatch for {entity_type}: "
                f"expected {feature_count}, found {len(templates)}"
            )
        start, end = meta_data["ent_type_index"][entity_type]
        for entity_index in range(start, end):
            entity_name = meta_data["ent_names"][entity_index]
            for template in templates:
                key = _statistic_key(template, entity_name)
                if key not in statistics:
                    raise KeyError(f"missing trace statistic: {key}")
                ordered_statistics.append((key, statistics[key]))
    return ordered_statistics




def _feature_axis(trace_values, feature_count):
    if trace_values.shape[-2] == feature_count:
        return -2
    if trace_values.shape[-1] == feature_count:
        return -1
    raise ValueError(
        "trace feature count does not match metadata: "
        f"shape={trace_values.shape}, expected={feature_count}"
    )




def apply_stored_percentile_clipping(dataset, statistics):
    """Clip trace inputs to the stored 1st/99th percentile boundaries.

    Values with non-zero IQR are already represented as ``(x - median) / IQR``
    by the source preprocessor. Zero-IQR features retain their raw coordinates.
    """

    bounds = []
    for _key, statistic in _trace_statistics_in_feature_order(
        dataset["meta_data"], statistics
    ):
        iqr = float(statistic["q3"] - statistic["q1"])
        if iqr != 0:
            scale = iqr
        else:
            scale = 1.0
        median = float(statistic["median"]) if iqr != 0 else 0.0
        lower = (float(statistic["percentile_1"]) - median) / scale
        upper = (float(statistic["percentile_99"]) - median) / scale
        bounds.append((lower, upper))

    clipped_value_count = 0
    for split in dataset["data"].values():
        if "x_trace" not in split:
            continue
        for sample_index, sample in enumerate(split["x_trace"]):
            trace_values = np.asarray(sample)
            feature_axis = _feature_axis(trace_values, len(bounds))
            for feature_index, (lower, upper) in enumerate(bounds):
                selection = [slice(None)] * trace_values.ndim
                selection[feature_axis] = feature_index
                selection = tuple(selection)
                values = trace_values[selection]
                clipped_value_count += int(
                    np.count_nonzero((values < lower) | (values > upper))
                )
                trace_values[selection] = np.clip(values, lower, upper)
            split["x_trace"][sample_index] = trace_values
    return clipped_value_count
