"""Auditable, disk-backed processing. Run: python -m backend.data_pipeline.preprocessing."""

import argparse
import logging
import os
from datetime import datetime, timezone

from backend.core.config import (
    ANALYTICAL_PATH,
    MAX_DATE,
    MAX_WAIT_DAYS,
    MIN_DATE,
    MIN_WAIT_DAYS,
    PROCESSED_DIR,
    QUALITY_PATH,
    ensure_directories,
)
from backend.core.utils import read_json, sql_identifier, sql_literal, write_json

from .data_loader import (
    connect,
    coverage,
    discover_files,
    load_raw_table,
    source_fingerprint,
)
from .data_quality import inspect_table, valid_date_sql

LOGGER = logging.getLogger(__name__)


def export_table(con, table, name):
    path = PROCESSED_DIR / name
    temporary = path.with_suffix(".tmp.parquet")
    con.execute(
        f"COPY ({table if table.lstrip().upper().startswith('SELECT') else 'SELECT * FROM ' + table}) "
        f"TO {sql_literal(temporary.as_posix())} (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    os.replace(temporary, path)


def clean_dates(con, category, columns):
    expressions = [_clean_date_expression(column, category) for column in columns]
    expressions.extend(_source_tracking_expressions(category, columns))

    con.execute(
        f"CREATE OR REPLACE TABLE clean_{category} AS SELECT "
        + ",".join(expressions)
        + f" FROM raw_{category}"
    )


def _clean_date_expression(column, category) -> str:
    name = sql_identifier(column)
    if not column.endswith("_dt") and column != "sdu_load_date":
        return name

    valid = valid_date_sql(column)
    if column in ("hospitalization_dt", "refusal_dt") and category == "referrals":
        valid = f"CASE WHEN ({valid}) >= ({valid_date_sql('registration_dt')}) THEN ({valid}) END"
    if column == "planned_dt":
        # Planned dates have no clock time.
        valid = f"CASE WHEN CAST(({valid}) AS DATE) >= CAST(({valid_date_sql('registration_dt')}) AS DATE) THEN ({valid}) END"
    return f"{valid} AS {name}"


def _source_tracking_expressions(category, columns) -> list[str]:
    expressions = []
    if category == "referrals":
        expressions.extend(
            [
                "hospitalization_dt IS NOT NULL AS had_hospitalization",
                "refusal_dt IS NOT NULL AS had_refusal",
            ]
        )
    if category == "waiting":
        fields = [
            "region_origin_code",
            "mo_destination_code",
            "profile_code",
            "patient_seq_no",
        ]
        expressions.append(
            " || '.' || ".join(sql_identifier(c) for c in fields)
            + " AS hospitalization_code_generated"
        )
    # Hash raw values so distinct invalid dates do not collapse during deduplication.
    if category in ("waiting", "referrals"):
        business_columns = sorted(c for c in columns if c != "sdu_load_date")
        values = ",".join(sql_identifier(c) for c in business_columns)
        expressions.append(
            f"sha256(to_json(list_value({values}))) AS _source_business_hash"
        )
    return expressions


def deduplicate(con, category, report):
    # Ignore export timestamps when detecting repeated business records across parts.
    before = con.execute(f"SELECT count(*) FROM clean_{category}").fetchone()[0]
    con.execute("SET threads=1")
    con.execute(
        f"CREATE OR REPLACE TABLE unique_{category} AS SELECT DISTINCT * EXCLUDE(sdu_load_date) FROM clean_{category}"
    )
    after = con.execute(f"SELECT count(*) FROM unique_{category}").fetchone()[0]
    report["cleaning"][f"{category}_exact_duplicates_removed"] = before - after
    return after


def create_analytical(con, report):
    waiting_rows = deduplicate(con, "waiting", report)
    deduplicate(con, "referrals", report)

    key_counts = _inspect_link_keys(con, report)
    _create_link_tables(con)
    _join_referrals(con)
    _write_join_report(con, report, key_counts)
    _write_analytical_summary(con, report, waiting_rows)

    export_table(con, "unique_waiting", "waiting.parquet")
    export_table(con, "analytical", "analytical.parquet")


def _inspect_link_keys(con, report) -> dict:
    con.execute(
        "CREATE OR REPLACE TABLE waiting_key_counts AS SELECT hospitalization_code_generated, count(*) n FROM unique_waiting GROUP BY 1"
    )
    con.execute(
        "CREATE OR REPLACE TABLE referral_key_counts AS SELECT hospitalization_code, count(*) n FROM unique_referrals GROUP BY 1"
    )
    waiting_ambiguous = con.execute(
        "SELECT count(*) FROM waiting_key_counts WHERE n>1"
    ).fetchone()[0]
    referral_conflicting = con.execute(
        "SELECT count(*) FROM referral_key_counts WHERE n>1"
    ).fetchone()[0]
    matched_all = con.execute(
        "SELECT count(*) FROM clean_referrals r SEMI JOIN unique_waiting w ON r.hospitalization_code=w.hospitalization_code_generated"
    ).fetchone()[0]
    invalid_referrals = con.execute(
        "SELECT count(*) FROM unique_referrals r JOIN referral_key_counts c USING(hospitalization_code) WHERE c.n>1"
    ).fetchone()[0]
    missing_referral_keys = con.execute(
        "SELECT count(*) FROM unique_referrals WHERE hospitalization_code IS NULL"
    ).fetchone()[0]
    report["cleaning"].update(
        referrals_conflicting_key_rows_excluded=invalid_referrals,
        referrals_missing_key_excluded=missing_referral_keys,
    )
    return {
        "matched_all": matched_all,
        "waiting_ambiguous": waiting_ambiguous,
        "referral_conflicting": referral_conflicting,
    }


def _create_link_tables(con) -> None:
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


def _join_referrals(con) -> None:
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


def _write_join_report(con, report, key_counts) -> None:
    matched_all = key_counts["matched_all"]
    waiting_ambiguous = key_counts["waiting_ambiguous"]
    referral_conflicting = key_counts["referral_conflicting"]
    raw_ref_rows = report["datasets"]["referrals"]["rows"]
    joined_rows, joined_matches, mismatches = con.execute(
        "SELECT count(*), count(*) FILTER(WHERE waiting_key_matched), count(*) FILTER(WHERE registration_date_mismatch) FROM analytical"
    ).fetchone()
    report["join"] = {
        "referral_rows": raw_ref_rows,
        "matched_rows": matched_all,
        "match_rate": matched_all / raw_ref_rows if raw_ref_rows else None,
        "analytical_rows": joined_rows,
        "unambiguous_matched_rows": joined_matches,
        "registration_date_mismatches": mismatches,
        "waiting_ambiguous_keys": waiting_ambiguous,
        "referral_conflicting_keys": referral_conflicting,
    }


def _write_analytical_summary(con, report, waiting_rows) -> None:
    joined_rows = report["join"]["analytical_rows"]
    outcomes = dict(
        con.execute(
            "SELECT outcome,count(*) FROM analytical GROUP BY outcome"
        ).fetchall()
    )
    stats = con.execute("""SELECT count(*) FILTER(WHERE target_eligible), avg(wait_days) FILTER(WHERE target_eligible),
        median(wait_days) FILTER(WHERE target_eligible),count(DISTINCT hospital_mo),count(DISTINCT region_origin_code),
        min(registration_dt),max(registration_dt),count(*) FILTER(WHERE registration_dt IS NULL),
        count(*) FILTER(WHERE outcome='hospitalized' AND NOT target_eligible) FROM analytical""").fetchone()
    report["summary"] = {
        "waiting_records": waiting_rows,
        "referral_records": joined_rows,
        **{
            k: outcomes.get(k, 0)
            for k in (
                "hospitalized",
                "refused",
                "unresolved",
                "conflicting",
                "invalid_outcome",
            )
        },
        "target_eligible": stats[0],
        "mean_wait_days": stats[1],
        "median_wait_days": stats[2],
        "hospitals": stats[3],
        "regions": stats[4],
        "registration_min": stats[5],
        "registration_max": stats[6],
    }
    report["cleaning"].update(
        invalid_registration_rows=stats[7],
        hospitalized_outside_target_rules=stats[8],
        target_excluded=joined_rows - stats[0],
    )


def clean_auxiliary(con, category, columns, report):
    clean_dates(con, category, columns)
    numeric = _numeric_columns(category, columns)

    if numeric:
        _record_invalid_numbers(con, category, numeric, report)
        _convert_numeric_columns(con, category, numeric)
        export_table(con, f"numeric_{category}", f"{category}.parquet")
    else:
        export_table(con, f"clean_{category}", f"{category}.parquet")

    _record_retained_duplicates(con, category, report)


def _numeric_columns(category, columns) -> list[str]:
    if category == "treated":
        return [
            c for c in columns if c not in ("medicine_organization", "sdu_load_date")
        ]
    return ["amount"] if "amount" in columns else []


def _numeric_expression(column) -> str:
    name = sql_identifier(column)
    return f"TRY_CAST(REPLACE(REPLACE({name}, ' ', ''), ',', '.') AS DOUBLE)"


def _record_invalid_numbers(con, category, columns, report) -> None:
    for column in columns:
        name = sql_identifier(column)
        converted = _numeric_expression(column)
        invalid = con.execute(
            f"SELECT count(*) FROM clean_{category} WHERE {name} IS NOT NULL AND {converted} IS NULL"
        ).fetchone()[0]
        report["cleaning"][f"{category}_{column}_invalid_numeric"] = invalid


def _convert_numeric_columns(con, category, columns) -> None:
    names = ",".join(sql_identifier(column) for column in columns)
    expressions = ",".join(
        f"{_numeric_expression(column)} AS {sql_identifier(column)}"
        for column in columns
    )
    con.execute(
        f"CREATE OR REPLACE TABLE numeric_{category} AS SELECT * EXCLUDE({names}),"
        + expressions
        + f" FROM clean_{category}"
    )


def _record_retained_duplicates(con, category, report) -> None:
    # Without a reliable event key, identical rows are retained.
    rows = report["datasets"][category]["rows"]
    con.execute("SET threads=1")
    unique = con.execute(
        f"SELECT count(*) FROM (SELECT DISTINCT * EXCLUDE(sdu_load_date) FROM clean_{category})"
    ).fetchone()[0]
    report["cleaning"][f"{category}_possible_duplicate_rows_retained"] = rows - unique


def run_pipeline(force=False):
    ensure_directories()
    files = discover_files()
    fingerprint = source_fingerprint(files)

    cached_report = _cached_pipeline_report(force, fingerprint)
    if cached_report is not None:
        return cached_report

    _ensure_required_sources(files)
    report = _new_pipeline_report(files, fingerprint)
    write_json(QUALITY_PATH, report)
    _remove_stale_artifacts(files, report)

    with connect(PROCESSED_DIR / "pipeline.duckdb") as con:
        _process_sources(con, files, report)
        create_analytical(con, report)
        _clear_scratch_tables(con)

    _complete_pipeline(report)
    return report


def _cached_pipeline_report(force, fingerprint) -> dict | None:
    if force or not QUALITY_PATH.exists() or not ANALYTICAL_PATH.exists():
        return None

    previous = read_json(QUALITY_PATH)
    if previous.get("source_fingerprint") == fingerprint and previous.get(
        "pipeline_complete"
    ):
        return previous
    return None


def _ensure_required_sources(files) -> None:
    missing = [category for category in ("waiting", "referrals") if not files[category]]
    if not missing:
        return

    raise FileNotFoundError(
        "Place waiting and referral CSV files in data/ or data/raw/. Missing: "
        + ", ".join(missing)
    )


def _new_pipeline_report(files, fingerprint) -> dict:
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_fingerprint": fingerprint,
        "coverage": coverage(files),
        "datasets": {},
        "cleaning": {},
        "pipeline_complete": False,
        "policy": {
            "min_date": MIN_DATE,
            "max_date": MAX_DATE,
            "wait_days_range": [MIN_WAIT_DAYS, MAX_WAIT_DAYS],
        },
        "limitations": [
            "Partial source files are not a national census or a live queue.",
            "Waiting data is a historical record, not today's active waiting list.",
            "Refusals and treated cases remain separate; no unverified hospital-name joins.",
            "The 2026 treated-case extract is not used as a 2025 model feature.",
            "No bed inventory: cohort pressure is not occupancy or validated overload.",
        ],
    }
    return report


def _remove_stale_artifacts(files, report) -> None:
    report["removed_stale_artifacts"] = []
    for category, artifacts in {
        "refusals": ("refusals.parquet", "refusal_day.parquet"),
        "treated": ("treated.parquet",),
    }.items():
        if not files[category]:
            for artifact in artifacts:
                stale_path = PROCESSED_DIR / artifact
                if stale_path.exists():
                    stale_path.unlink()
                    report["removed_stale_artifacts"].append(artifact)
                    LOGGER.info(
                        "Removed stale derived artifact for absent %s feed: %s",
                        category,
                        artifact,
                    )


def _process_sources(con, files, report) -> None:
    for category, paths in files.items():
        if paths:
            _process_source(con, category, paths, report)


def _process_source(con, category, paths, report) -> None:
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


def _clear_scratch_tables(con) -> None:
    for (name,) in con.execute("SHOW TABLES").fetchall():
        con.execute(f"DROP TABLE {sql_identifier(name)}")
    con.execute("CHECKPOINT")


def _complete_pipeline(report) -> None:
    from backend.data_pipeline.aggregation import build_aggregations

    report["aggregation"] = build_aggregations(PROCESSED_DIR)
    report["pipeline_complete"] = True
    for reason, count in report["cleaning"].items():
        LOGGER.info("Cleaning %s: %s", reason, count)
    LOGGER.info("Join: %s", report["join"])
    LOGGER.info("Summary: %s", report["summary"])
    write_json(QUALITY_PATH, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline(force=args.force)
