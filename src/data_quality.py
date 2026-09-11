"""Full-data counts and date checks performed in SQL, without printing patient rows."""
import argparse
import logging
from datetime import datetime, timezone

from .config import MIN_DATE, MAX_DATE, QUALITY_PATH, PROCESSED_DIR, ensure_directories
from .data_loader import discover_files, source_fingerprint, coverage, connect, load_raw_table
from .utils import sql_identifier, sql_literal, write_json

LOGGER = logging.getLogger(__name__)

def date_sql(column):
    return f"TRY_CAST({sql_identifier(column)} AS TIMESTAMP)"

def valid_date_sql(column):
    expr = date_sql(column)
    return f"CASE WHEN {expr} >= TIMESTAMP '{MIN_DATE}' AND {expr} < TIMESTAMP '{MAX_DATE}' + INTERVAL 1 DAY THEN {expr} END"

def inspect_table(con, category, columns):
    table = f"raw_{category}"
    count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    miss = con.execute(f"SELECT " + ",".join(f"count(*) FILTER (WHERE {sql_identifier(c)} IS NULL)" for c in columns) + f" FROM {table}").fetchone()
    report = {"rows": count, "columns": columns, "missing_values": dict(zip(columns, miss)), "dates": {}}
    for col in columns:
        if not (col.endswith("_dt") or col == "sdu_load_date"):
            continue
        raw, parsed = sql_identifier(col), date_sql(col)
        before = f"count(*) FILTER (WHERE {parsed} < {date_sql('registration_dt')})" if "registration_dt" in columns and col not in ("registration_dt", "sdu_load_date") else "0"
        if col == "planned_dt" and "registration_dt" in columns:
            before = f"count(*) FILTER (WHERE CAST({parsed} AS DATE) < CAST({date_sql('registration_dt')} AS DATE))"
        row = con.execute(f"SELECT min({parsed}), max({parsed}), count(*) FILTER(WHERE {raw} IS NULL), "
                          f"count(*) FILTER(WHERE {raw} IS NOT NULL AND {parsed} IS NULL), "
                          f"count(*) FILTER(WHERE {parsed} < TIMESTAMP '{MIN_DATE}' OR {parsed} >= TIMESTAMP '{MAX_DATE}' + INTERVAL 1 DAY), {before} FROM {table}").fetchone()
        report["dates"][col] = dict(zip(["min", "max", "missing", "parse_invalid", "out_of_range", "before_registration"], row))
    mappings = {
        "waiting": ("mo_destination_code", "region_origin_code", "icd10_ref_diag_code"),
        "referrals": ("hospital_mo", None, "icd10_ref_diag_code"),
        "refusals": ("org_in", "region_in", "icd10"),
        "treated": ("medicine_organization", None, None),
    }
    for label, col in zip(("hospitals", "regions", "diagnoses"), mappings[category]):
        report["unique_" + label] = con.execute(f"SELECT count(DISTINCT {sql_identifier(col)}) FROM {table}").fetchone()[0] if col else None
    LOGGER.info("%s: rows=%s, columns=%s, hospitals=%s", category, count, len(columns), report["unique_hospitals"])
    for col, stats in report["dates"].items():
        LOGGER.info("  %s: %s..%s, missing=%s, parse_invalid=%s, out_of_range=%s, before_registration=%s", col, *stats.values())
    return report

def inspect_data():
    ensure_directories()
    files = discover_files()
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "source_fingerprint": source_fingerprint(files),
              "coverage": coverage(files), "datasets": {}, "pipeline_complete": False}
    with connect(PROCESSED_DIR / "inspection.duckdb") as con:
        for category, paths in files.items():
            if paths:
                columns = load_raw_table(con, category, paths)
                report["datasets"][category] = inspect_table(con, category, columns)
                con.execute(f"DROP TABLE raw_{category}")
    write_json(PROCESSED_DIR / "inspection_report.json", report)
    return report

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    inspect_data()
