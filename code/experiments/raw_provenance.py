import csv
import hashlib
import io
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path


def _merge_line_ranges(intervals):
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _record_evidence(row, ordinal, physical_start, physical_end):
    value = row.get("value", "")
    evidence = {
        "record_ordinal": ordinal,
        "physical_line_start": physical_start,
        "physical_line_end": physical_end,
        "timestamp": row.get("timestamp"),
        "cmdb_id": row.get("cmdb_id"),
    }
    for field in (
        "kpi_name",
        "log_name",
        "span_id",
        "trace_id",
        "duration",
        "type",
        "status_code",
        "operation_name",
        "parent_span",
    ):
        if field in row:
            evidence[field] = row[field]
    if value:
        evidence.update(
            {
                "value": value if len(value) <= 256 else None,
                "value_preview": value[:256],
                "value_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
            }
        )
    return evidence


def scan_csv_stream(
    stream,
    *,
    start_timestamp,
    end_timestamp,
    timestamp_divisor=1,
    root_entity=None,
):
    reader = csv.DictReader(stream)
    case_intervals = []
    root_intervals = []
    root_records = []
    case_count = 0
    root_count = 0
    minimum_timestamp = None
    maximum_timestamp = None
    previous_physical_end = 1

    for ordinal, row in enumerate(reader, start=1):
        physical_start = previous_physical_end + 1
        physical_end = reader.line_num
        previous_physical_end = physical_end
        raw_timestamp = int(float(row["timestamp"]))
        normalized_timestamp = raw_timestamp / timestamp_divisor
        if not start_timestamp <= normalized_timestamp < end_timestamp:
            continue

        case_count += 1
        case_intervals.append([physical_start, physical_end])
        minimum_timestamp = (
            raw_timestamp
            if minimum_timestamp is None
            else min(minimum_timestamp, raw_timestamp)
        )
        maximum_timestamp = (
            raw_timestamp
            if maximum_timestamp is None
            else max(maximum_timestamp, raw_timestamp)
        )
        cmdb_id = row.get("cmdb_id", "")
        if root_entity and root_entity in cmdb_id:
            root_count += 1
            root_intervals.append([physical_start, physical_end])
            root_records.append(
                _record_evidence(row, ordinal, physical_start, physical_end)
            )

    return {
        "header": reader.fieldnames or [],
        "timestamp_unit_divisor": timestamp_divisor,
        "window_start_inclusive": start_timestamp,
        "window_end_exclusive": end_timestamp,
        "case_record_count": case_count,
        "case_physical_line_ranges": _merge_line_ranges(case_intervals),
        "root_entity": root_entity,
        "root_record_count": root_count,
        "root_physical_line_ranges": _merge_line_ranges(root_intervals),
        "root_records": root_records,
        "minimum_timestamp": minimum_timestamp,
        "maximum_timestamp": maximum_timestamp,
    }


def source_member_for_metric(prefix, feature_name):
    try:
        _category, raw_name = feature_name.split("/", 1)
    except ValueError as error:
        raise ValueError(f"unsupported metric feature: {feature_name}") from error
    raw_name = raw_name.removesuffix(".source").removesuffix(".destination")
    if raw_name.startswith("kpi_container_"):
        resource_type = "container"
    elif raw_name.startswith("kpi_istio_"):
        resource_type = "istio"
    else:
        raise ValueError(f"unsupported metric feature: {feature_name}")
    return f"{prefix}/metric/{resource_type}/{raw_name}.csv"


@contextmanager
def open_archive_member(seven_zip, archive_path, member_path):
    command = [
        str(seven_zip),
        "e",
        "-so",
        "-bd",
        "-sccUTF-8",
        str(archive_path),
        str(member_path).replace("/", "\\"),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stream = io.TextIOWrapper(
        process.stdout, encoding="utf-8-sig", errors="replace", newline=""
    )
    try:
        yield stream
    finally:
        stream.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace")
        return_code = process.wait()
        process.stderr.close()
        if return_code != 0:
            raise RuntimeError(
                f"7-Zip failed for {member_path}: exit={return_code}: {stderr.strip()}"
            )


def scan_archive_csv(
    seven_zip,
    archive_path,
    member_path,
    *,
    start_timestamp,
    end_timestamp,
    timestamp_divisor=1,
    root_entity=None,
):
    with open_archive_member(seven_zip, archive_path, member_path) as stream:
        result = scan_csv_stream(
            stream,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            timestamp_divisor=timestamp_divisor,
            root_entity=root_entity,
        )
    result["archive_path"] = str(Path(archive_path).resolve())
    result["member_path"] = member_path
    return result


def read_archive_json(seven_zip, archive_path, member_path):
    with open_archive_member(seven_zip, archive_path, member_path) as stream:
        return json.load(stream)
