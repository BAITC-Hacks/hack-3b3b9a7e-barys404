"""Auditable, disk-backed processing. Run: python -m backend.data_pipeline.preprocessing."""
import argparse
import logging
import os
from datetime import datetime, timezone

from backend.core.config import (PROCESSED_DIR, QUALITY_PATH, ANALYTICAL_PATH, MIN_WAIT_DAYS,
                     MAX_WAIT_DAYS, MIN_DATE, MAX_DATE, ensure_directories)
from .data_loader import discover_files, source_fingerprint, coverage, connect, load_raw_table
from .data_quality import inspect_table, valid_date_sql
from backend.core.utils import read_json, write_json, sql_literal, sql_identifier

LOGGER = logging.getLogger(__name__)

def export_table(con, table, name):
    path = PROCESSED_DIR / name
    temporary = path.with_suffix(".tmp.parquet")
    con.execute(f"COPY ({table if table.lstrip().upper().startswith('SELECT') else 'SELECT * FROM ' + table}) "
                f"TO {sql_literal(temporary.as_posix())} (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(temporary, path)

def clean_dates(con, category, columns):
    date_cols = [c for c in columns if c.endswith("_dt") or c == "sdu_load_date"]
    exprs = []
    for col in columns:
        ident = sql_identifier(col)
        if col not in date_cols:
            exprs.append(ident)
            continue
        valid = valid_date_sql(col)
        if col in ("hospitalization_dt", "refusal_dt") and category == "referrals":
            valid = f"CASE WHEN ({valid}) >= ({valid_date_sql('registration_dt')}) THEN ({valid}) END"
        if col == "planned_dt":
            # Plans are midnight dates, while registration contains a clock time.
            valid = f"CASE WHEN CAST(({valid}) AS DATE) >= CAST(({valid_date_sql('registration_dt')}) AS DATE) THEN ({valid}) END"
        exprs.append(f"{valid} AS {ident}")
    if category == "referrals":
        exprs.extend(["hospitalization_dt IS NOT NULL AS had_hospitalization", "refusal_dt IS NOT NULL AS had_refusal"])
    if category == "waiting":
        fields = ["region_origin_code", "mo_destination_code", "profile_code", "patient_seq_no"]
        exprs.append(" || '.' || ".join(sql_identifier(c) for c in fields) + " AS hospitalization_code_generated")
    # Preserve distinctions in source values: two different bad dates must not
    # collapse into an apparently identical record when both become NULL.
    if category in ("waiting", "referrals"):
        business_columns = sorted(c for c in columns if c != "sdu_load_date")
        values = ",".join(sql_identifier(c) for c in business_columns)
        exprs.append(f"sha256(to_json(list_value({values}))) AS _source_business_hash")
    con.execute(f"CREATE OR REPLACE TABLE clean_{category} AS SELECT " + ",".join(exprs) + f" FROM raw_{category}")

def deduplicate(con, category, report):
    # Ignore export timestamps when detecting repeated business records across parts.
    before = con.execute(f"SELECT count(*) FROM clean_{category}").fetchone()[0]
    con.execute("SET threads=1")
    con.execute(f"CREATE OR REPLACE TABLE unique_{category} AS SELECT DISTINCT * EXCLUDE(sdu_load_date) FROM clean_{category}")
    after = con.execute(f"SELECT count(*) FROM unique_{category}").fetchone()[0]
    report["cleaning"][f"{category}_exact_duplicates_removed"] = before - after
    return after

def create_analytical(con, report):
    waiting_rows = deduplicate(con, "waiting", report)
    referral_rows = deduplicate(con, "referrals", report)
    con.execute("CREATE OR REPLACE TABLE waiting_key_counts AS SELECT hospitalization_code_generated, count(*) n FROM unique_waiting GROUP BY 1")
    con.execute("CREATE OR REPLACE TABLE referral_key_counts AS SELECT hospitalization_code, count(*) n FROM unique_referrals GROUP BY 1")
    waiting_ambiguous = con.execute("SELECT count(*) FROM waiting_key_counts WHERE n>1").fetchone()[0]
    referral_conflicting = con.execute("SELECT count(*) FROM referral_key_counts WHERE n>1").fetchone()[0]
    matched_all = con.execute("SELECT count(*) FROM clean_referrals r SEMI JOIN unique_waiting w ON r.hospitalization_code=w.hospitalization_code_generated").fetchone()[0]
    invalid_referrals = con.execute("SELECT count(*) FROM unique_referrals r JOIN referral_key_counts c USING(hospitalization_code) WHERE c.n>1").fetchone()[0]
    missing_referral_keys = con.execute("SELECT count(*) FROM unique_referrals WHERE hospitalization_code IS NULL").fetchone()[0]
    report["cleaning"].update(referrals_conflicting_key_rows_excluded=invalid_referrals, referrals_missing_key_excluded=missing_referral_keys)
    con.execute("""CREATE OR REPLACE TABLE waiting_link AS
        SELECT w.* FROM unique_waiting w JOIN waiting_key_counts c USING(hospitalization_code_generated)
        WHERE c.n=1 AND hospitalization_code_generated IS NOT NULL""")
    con.execute("""CREATE OR REPLACE TABLE valid_referrals AS
        SELECT r.* FROM unique_referrals r JOIN referral_key_counts c USING(hospitalization_code)
        WHERE c.n=1 AND hospitalization_code IS NOT NULL""")
    con.execute("""CREATE OR REPLACE TABLE referral_quarantine AS
        SELECT r.* FROM unique_referrals r LEFT JOIN referral_key_counts c USING(hospitalization_code)
        WHERE c.n>1 OR hospitalization_code IS NULL""")
    export_table(con, "referral_quarantine", "referral_key_quarantine.parquet")
    con.execute("""CREATE OR REPLACE TABLE joined_referrals AS
        SELECT r.*, w.region_origin_code, w.mo_destination_code, w.profile_code,
               w.hospitalization_code_generated IS NOT NULL AS waiting_key_matched,
               CAST(r.registration_dt AS DATE) != CAST(w.registration_dt AS DATE) AS registration_date_mismatch,
               epoch(r.hospitalization_dt-r.registration_dt)/86400.0 AS wait_days,
               CASE WHEN had_hospitalization AND had_refusal THEN 'conflicting'
                    WHEN (had_hospitalization AND r.hospitalization_dt IS NULL)
                      OR (had_refusal AND r.refusal_dt IS NULL) THEN 'invalid_outcome'
                    WHEN r.hospitalization_dt IS NOT NULL THEN 'hospitalized'
                    WHEN r.refusal_dt IS NOT NULL THEN 'refused'
                    ELSE 'unresolved' END AS outcome
        FROM valid_referrals r LEFT JOIN waiting_link w ON r.hospitalization_code=w.hospitalization_code_generated""")
    con.execute(f"""CREATE OR REPLACE TABLE analytical AS SELECT *,
        COALESCE(outcome='hospitalized' AND registration_dt IS NOT NULL
            AND wait_days BETWEEN {MIN_WAIT_DAYS} AND {MAX_WAIT_DAYS}, false) AS target_eligible,
        COALESCE(registration_dt IS NOT NULL AND outcome IN ('hospitalized','refused','unresolved'), false)
            AS queue_reconstruction_eligible FROM joined_referrals""")
    raw_ref_rows = report["datasets"]["referrals"]["rows"]
    joined_rows, joined_matches, mismatches = con.execute("SELECT count(*), count(*) FILTER(WHERE waiting_key_matched), count(*) FILTER(WHERE registration_date_mismatch) FROM analytical").fetchone()
    report["join"] = {"referral_rows": raw_ref_rows, "matched_rows": matched_all,
                      "match_rate": matched_all / raw_ref_rows if raw_ref_rows else None,
                      "analytical_rows": joined_rows, "unambiguous_matched_rows": joined_matches,
                      "registration_date_mismatches": mismatches, "waiting_ambiguous_keys": waiting_ambiguous,
                      "referral_conflicting_keys": referral_conflicting}
    outcomes = dict(con.execute("SELECT outcome,count(*) FROM analytical GROUP BY outcome").fetchall())
    stats = con.execute("""SELECT count(*) FILTER(WHERE target_eligible), avg(wait_days) FILTER(WHERE target_eligible),
        median(wait_days) FILTER(WHERE target_eligible),count(DISTINCT hospital_mo),count(DISTINCT region_origin_code),
        min(registration_dt),max(registration_dt),count(*) FILTER(WHERE registration_dt IS NULL),
        count(*) FILTER(WHERE outcome='hospitalized' AND NOT target_eligible) FROM analytical""").fetchone()
    report["summary"] = {"waiting_records": waiting_rows, "referral_records": joined_rows,
                          **{k: outcomes.get(k, 0) for k in ("hospitalized", "refused", "unresolved", "conflicting", "invalid_outcome")},
                          "target_eligible": stats[0], "mean_wait_days": stats[1], "median_wait_days": stats[2],
                          "hospitals": stats[3], "regions": stats[4], "registration_min": stats[5], "registration_max": stats[6]}
    report["cleaning"].update(invalid_registration_rows=stats[7], hospitalized_outside_target_rules=stats[8],
                              target_excluded=joined_rows-stats[0])
    export_table(con, "unique_waiting", "waiting.parquet")
    export_table(con, "analytical", "analytical.parquet")

def clean_auxiliary(con, category, columns, report):
    clean_dates(con, category, columns)
    numeric = [c for c in columns if c not in ("medicine_organization", "sdu_load_date")] if category == "treated" else ["amount"]
    numeric = [c for c in numeric if c in columns]
    if numeric:
        for col in numeric:
            name = sql_identifier(col)
            converted = f"TRY_CAST(REPLACE(REPLACE({name}, ' ', ''), ',', '.') AS DOUBLE)"
            invalid = con.execute(f"SELECT count(*) FROM clean_{category} WHERE {name} IS NOT NULL AND {converted} IS NULL").fetchone()[0]
            report["cleaning"][f"{category}_{col}_invalid_numeric"] = invalid
        exprs = [f"TRY_CAST(REPLACE(REPLACE({sql_identifier(c)}, ' ', ''), ',', '.') AS DOUBLE) AS {sql_identifier(c)}" for c in numeric]
        con.execute(f"CREATE OR REPLACE TABLE numeric_{category} AS SELECT * EXCLUDE(" + ",".join(sql_identifier(c) for c in numeric) + ")," + ",".join(exprs) + f" FROM clean_{category}")
        export_table(con, f"numeric_{category}", f"{category}.parquet")
    else:
        export_table(con, f"clean_{category}", f"{category}.parquet")
    # These feeds lack a reliable event key: identical rows are reported, not silently removed.
    rows = report["datasets"][category]["rows"]
    con.execute("SET threads=1")
    unique = con.execute(f"SELECT count(*) FROM (SELECT DISTINCT * EXCLUDE(sdu_load_date) FROM clean_{category})").fetchone()[0]
    report["cleaning"][f"{category}_possible_duplicate_rows_retained"] = rows - unique

def run_pipeline(force=False):
    ensure_directories()
    files = discover_files()
    fingerprint = source_fingerprint(files)
    if not force and QUALITY_PATH.exists() and ANALYTICAL_PATH.exists():
        previous = read_json(QUALITY_PATH)
        if previous.get("source_fingerprint") == fingerprint and previous.get("pipeline_complete"):
            return previous
    missing = [c for c in ("waiting", "referrals") if not files[c]]
    if missing:
        raise FileNotFoundError("Place waiting and referral CSV files in data/ or data/raw/. Missing: " + ", ".join(missing))
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "source_fingerprint": fingerprint,
              "coverage": coverage(files), "datasets": {}, "cleaning": {}, "pipeline_complete": False,
              "policy": {"min_date": MIN_DATE, "max_date": MAX_DATE, "wait_days_range": [MIN_WAIT_DAYS, MAX_WAIT_DAYS]},
              "limitations": ["Partial source files are not a national census or a live queue.",
                              "Waiting data is a historical record, not today's active waiting list.",
                              "Refusals and treated cases remain separate; no unverified hospital-name joins.",
                              "The 2026 treated-case extract is not used as a 2025 model feature.",
                              "No bed inventory: cohort pressure is not occupancy or validated overload."]}
    write_json(QUALITY_PATH, report)
    # Removed optional sources must not leave an old feed visible in the UI.
    report["removed_stale_artifacts"] = []
    for category, artifacts in {"refusals": ("refusals.parquet", "refusal_day.parquet"), "treated": ("treated.parquet",)}.items():
        if not files[category]:
            for artifact in artifacts:
                stale_path = PROCESSED_DIR / artifact
                if stale_path.exists():
                    stale_path.unlink()
                    report["removed_stale_artifacts"].append(artifact)
                    LOGGER.info("Removed stale derived artifact for absent %s feed: %s", category, artifact)
    with connect(PROCESSED_DIR / "pipeline.duckdb") as con:
        for category, paths in files.items():
            if not paths:
                continue
            LOGGER.info("Reading %s (%d files)", category, len(paths))
            columns = load_raw_table(con, category, paths)
            report["datasets"][category] = inspect_table(con, category, columns)
            if category in ("waiting", "referrals"):
                clean_dates(con, category, columns)
            else:
                clean_auxiliary(con, category, columns, report)
                con.execute(f"DROP TABLE clean_{category}")
                con.execute(f"DROP TABLE IF EXISTS numeric_{category}")
            con.execute(f"DROP TABLE raw_{category}")
            con.execute("CHECKPOINT")
        create_analytical(con, report)
        # No raw patient tables remain in the scratch database after processing.
        for (name,) in con.execute("SHOW TABLES").fetchall():
            con.execute(f"DROP TABLE {sql_identifier(name)}")
        con.execute("CHECKPOINT")
    from backend.analytics.aggregation import build_aggregations
    report["aggregation"] = build_aggregations(PROCESSED_DIR)
    report["pipeline_complete"] = True
    for reason, count in report["cleaning"].items():
        LOGGER.info("Cleaning %s: %s", reason, count)
    LOGGER.info("Join: %s", report["join"])
    LOGGER.info("Summary: %s", report["summary"])
    write_json(QUALITY_PATH, report)
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline(force=args.force)
