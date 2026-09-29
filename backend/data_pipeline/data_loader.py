"""CSV discovery and disk-backed DuckDB ingestion; never materialize raw CSV in pandas."""
import csv
import hashlib
import json
import re
from pathlib import Path

import duckdb

from backend.core.config import (
    DATA_DIR,
    DUCKDB_MEMORY_LIMIT,
    MAX_DATE,
    MAX_WAIT_DAYS,
    MIN_DATE,
    MIN_WAIT_DAYS,
    MODELS_DIR,
    PROCESSED_DIR,
    THREAD_COUNT,
)
from backend.core.utils import sql_identifier, sql_literal
from backend.data_pipeline.deployment import deployment_fingerprint

SIGNATURES = {
    "waiting": {"region_origin_code", "mo_destination_code", "profile_code", "patient_seq_no", "registration_dt"},
    "referrals": {"hospitalization_code", "hospital_mo", "registration_dt", "hospitalization_dt", "refusal_dt"},
    "refusals": {"region_in", "org_in", "refuse_dt"},
    "treated": {"medicine_organization", "discharged_total", "bed_days"},
}

# Source exports are supplied in both English and Russian/Kazakh naming
# conventions (for example, ``part 2 of 3`` and ``Часть 2 из 3``).
PART_NUMBER_PATTERN = re.compile(
    r"(?:part|часть)[_\s-]*(\d+)[_\s-]*(?:of|из)[_\s-]*(\d+)", re.IGNORECASE
)

def csv_format(path):
    # Bounded sniff. A malformed row is an error, never silently skipped.
    with Path(      path).open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(65536)
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
        file.seek(0)
        columns = next(csv.reader(file, delimiter=delimiter))
    return delimiter, [col.strip().lstrip("\ufeff") for col in columns]

def discover_files(data_dir=DATA_DIR):
    found = {key: [] for key in SIGNATURES}
    root = Path(data_dir)
    candidates = sorted(set(root.glob("*.csv")) | set((root / "raw").glob("*.csv")))
    for path in candidates:
        _, columns = csv_format(path)
        for category, required in SIGNATURES.items():
            if required.issubset(columns):
                found[category].append(path)
                break
    return found

def source_fingerprint(files=None):
    files = discover_files() if files is None else files
    portable = deployment_fingerprint(files, fingerprint_policy(), PROCESSED_DIR, MODELS_DIR)
    if portable is not None:
        return portable

    payload = fingerprint_policy()
    payload["files"] = [
        (category, str(path.resolve()), path.stat().st_size, path.stat().st_mtime_ns)
        for category, paths in sorted(files.items())
        for path in paths
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def fingerprint_policy() -> dict:
    return {
        "pipeline_version": 3,
        "date_bounds": [MIN_DATE, MAX_DATE],
        "wait_days_range": [MIN_WAIT_DAYS, MAX_WAIT_DAYS],
    }

def coverage(files):
    result = {}
    for category, paths in files.items():
        parts, expected = set(), 3 if category == "referrals" else 6 if category == "refusals" else 1
        for path in paths:
            match = PART_NUMBER_PATTERN.search(path.name)
            if match:
                parts.add(int(match[1]))
                expected = max(expected, int(match[2]))
        if category in ("waiting", "treated") and paths:
            parts = {1}
        result[category] = {"available_parts": sorted(parts), "expected_parts": expected,
                            "complete": set(range(1, expected + 1)).issubset(parts),
                            "file_count": len(paths), "files": [p.name for p in paths]}
    return result

def connect(database=":memory:"):
    con = duckdb.connect(str(database))
    con.execute(f"SET memory_limit={sql_literal(DUCKDB_MEMORY_LIMIT)}")
    con.execute(f"SET threads={THREAD_COUNT}")
    con.execute("SET preserve_insertion_order=false")
    temp_dir = PROCESSED_DIR / ".duckdb_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory={sql_literal(temp_dir.as_posix())}")
    return con

def load_raw_table(con, category, paths):
    scans = []
    for path in paths:
        delimiter, columns = csv_format(path)
        column_types = "{" + ",".join(f"{sql_literal(c)}:'VARCHAR'" for c in columns) + "}"
        scans.append(f"SELECT * FROM read_csv({sql_literal(path.as_posix())}, header=true, delim={sql_literal(delimiter)}, "
                     f"columns={column_types}, auto_detect=false, strict_mode=true, ignore_errors=false)")
    con.execute(f"CREATE OR REPLACE TABLE raw_{category} AS " + " UNION ALL BY NAME ".join(scans))
    columns = [r[0] for r in con.execute(f"DESCRIBE raw_{category}").fetchall()]
    for col in columns:
        name = sql_identifier(col)
        con.execute(f"UPDATE raw_{category} SET {name}=NULLIF(TRIM({name}), '')")
    return columns
