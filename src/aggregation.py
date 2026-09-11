"""Out-of-core hospital/day aggregation over the observed referral cohort.

Registration dates delimit the timeline. Future exits never extend it. Open
cohort is reconstructed at each end of day and is NOT the hospital's full queue.
Unlinked refusal records are aggregated separately, without invented joins.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from src.anomaly_detection import add_historical_signals, indicator_metadata
from src.config import DUCKDB_MEMORY_LIMIT, PROCESSED_DIR, THREAD_COUNT
from src.utils import sql_literal, write_json


COUNT_COLUMNS = [
    "referrals", "hospitalized", "refusals", "eligible_incoming",
    "excluded_from_reconstruction", "reconstructed_open_cohort", "completed_wait_count",
]


def _connection() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(f"SET memory_limit={sql_literal(DUCKDB_MEMORY_LIMIT)}")
    connection.execute(f"SET threads={THREAD_COUNT}")
    return connection


def _aggregate(analytical_path: Path, filters: dict[str, str] | None = None) -> tuple[pd.DataFrame, dict]:
    if not analytical_path.exists():
        raise FileNotFoundError(f"Run preprocessing first: missing {analytical_path}")
    allowed_filters = {"hospital_mo", "region_origin_code", "bed_profile"}
    filters = filters or {}
    if set(filters).difference(allowed_filters):
        raise ValueError(f"Filters must use {sorted(allowed_filters)}")
    connection = _connection()
    try:
        conditions = " AND ".join(f"{key}={sql_literal(value)}" for key, value in filters.items()) or "TRUE"
        connection.execute(f"""
            CREATE VIEW source AS SELECT *,
              COALESCE(CAST(hospital_mo AS VARCHAR), 'Unknown hospital') AS hospital,
              CAST(registration_dt AS DATE) AS registered_day,
              CAST(hospitalization_dt AS DATE) AS hospitalized_day,
              CAST(refusal_dt AS DATE) AS refused_day
            FROM read_parquet({sql_literal(analytical_path)}) WHERE {conditions}
        """)
        columns = {row[0] for row in connection.execute("DESCRIBE source").fetchall()}
        # Explicit preprocessing flag retains invalid original dates after cleaning.
        # Older artifacts can still be read when their outcome enum is reliable.
        eligibility = "COALESCE(queue_reconstruction_eligible, FALSE)" if "queue_reconstruction_eligible" in columns else "outcome IN ('hospitalized', 'refused', 'unresolved')"
        connection.execute(f"""
            CREATE VIEW records AS SELECT *,
              ({eligibility}) AND registration_dt IS NOT NULL
              AND NOT (hospitalization_dt IS NOT NULL AND refusal_dt IS NOT NULL)
              AND (hospitalization_dt IS NULL OR hospitalization_dt >= registration_dt)
              AND (refusal_dt IS NULL OR refusal_dt >= registration_dt)
              AS queue_eligible
            FROM source
        """)
        stats_row = connection.execute("""
            SELECT count(*) AS source_rows,
              count(*) FILTER (WHERE registered_day IS NULL) AS missing_registration_rows,
              count(*) FILTER (WHERE NOT COALESCE(queue_eligible, FALSE)) AS excluded_queue_rows,
              min(registered_day) AS start_date, max(registered_day) AS end_date,
              count(DISTINCT hospital) FILTER (WHERE registered_day IS NOT NULL) AS hospitals
            FROM records
        """).fetchone()
        stats = dict(zip(["source_rows", "missing_registration_rows", "excluded_queue_rows", "start_date", "end_date", "hospitals"], stats_row))
        if stats["start_date"] is None:
            frame = pd.DataFrame({"hospital_mo": pd.Series(dtype="str"), "date": pd.Series(dtype="datetime64[ns]"), **{name: pd.Series(dtype="int64") for name in COUNT_COLUMNS}, "average_wait_days": pd.Series(dtype="float64")})
            stats.update({"daily_rows": 0, "exits_after_observation_end": 0, "excluded_event_rows": 0})
            return frame, stats
        start, end = sql_literal(stats["start_date"]), sql_literal(stats["end_date"])
        # All source rows remain in incoming counts. Only valid, unambiguous
        # records enter reconstruction; outcomes occur on their event dates.
        frame = connection.execute(f"""
            WITH calendar AS (
              SELECT CAST(day AS DATE) AS date FROM generate_series(
                CAST({start} AS TIMESTAMP), CAST({end} AS TIMESTAMP), INTERVAL 1 DAY
              ) AS days(day)
            ), hospitals AS (
              SELECT DISTINCT hospital FROM records WHERE registered_day IS NOT NULL
            ), incoming AS (
              SELECT hospital, registered_day AS date, count(*) AS referrals,
                count(*) FILTER (WHERE queue_eligible) AS eligible_incoming,
                count(*) FILTER (WHERE NOT COALESCE(queue_eligible, FALSE)) AS excluded_from_reconstruction
              FROM records WHERE registered_day IS NOT NULL GROUP BY hospital, registered_day
            ), admissions AS (
              SELECT hospital, hospitalized_day AS date, count(*) AS hospitalized,
                count(*) FILTER (WHERE target_eligible AND wait_days IS NOT NULL) AS completed_wait_count,
                avg(wait_days) FILTER (WHERE target_eligible) AS average_wait_days
              FROM records WHERE queue_eligible AND hospitalized_day IS NOT NULL
              GROUP BY hospital, hospitalized_day
            ), refusals AS (
              SELECT hospital, refused_day AS date, count(*) AS refusals
              FROM records WHERE queue_eligible AND refused_day IS NOT NULL
              GROUP BY hospital, refused_day
            ), daily AS (
              SELECT h.hospital AS hospital_mo, c.date,
                COALESCE(i.referrals, 0)::BIGINT AS referrals,
                COALESCE(a.hospitalized, 0)::BIGINT AS hospitalized,
                COALESCE(r.refusals, 0)::BIGINT AS refusals,
                COALESCE(i.eligible_incoming, 0)::BIGINT AS eligible_incoming,
                COALESCE(i.excluded_from_reconstruction, 0)::BIGINT AS excluded_from_reconstruction,
                COALESCE(a.completed_wait_count, 0)::BIGINT AS completed_wait_count,
                a.average_wait_days
              FROM hospitals h CROSS JOIN calendar c
              LEFT JOIN incoming i ON i.hospital=h.hospital AND i.date=c.date
              LEFT JOIN admissions a ON a.hospital=h.hospital AND a.date=c.date
              LEFT JOIN refusals r ON r.hospital=h.hospital AND r.date=c.date
            )
            SELECT *, CAST(sum(eligible_incoming-hospitalized-refusals)
              OVER (PARTITION BY hospital_mo ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
              AS BIGINT) AS reconstructed_open_cohort
            FROM daily ORDER BY hospital_mo, date
        """).fetchdf()
        if (frame["reconstructed_open_cohort"] < 0).any():
            raise ValueError("Negative reconstructed cohort indicates inconsistent event accounting")
        stats["daily_rows"] = len(frame)
        stats["exits_after_observation_end"] = connection.execute(f"""
            SELECT count(*) FROM records WHERE queue_eligible
            AND (hospitalized_day > CAST({end} AS DATE) OR refused_day > CAST({end} AS DATE))
        """).fetchone()[0]
        stats["excluded_event_rows"] = connection.execute("""
            SELECT count(*) FROM records WHERE NOT COALESCE(queue_eligible, FALSE)
            AND (hospitalization_dt IS NOT NULL OR refusal_dt IS NOT NULL)
        """).fetchone()[0]
        return frame, stats
    finally:
        connection.close()


def aggregate_hospital_days(analytical_path: str | Path, filters: dict[str, str] | None = None) -> pd.DataFrame:
    """Return hospital-day counts; optional filters select a referral cohort.

    Filters are exact values of hospital_mo, region_origin_code, or bed_profile.
    Do not trim registration dates before reconstructing the historical queue:
    apply display date filters after aggregation instead.
    """
    return _aggregate(Path(analytical_path), filters)[0]


def _aggregate_refusal_feed(processed_dir: Path) -> dict:
    source = processed_dir / "refusals.parquet"
    if not source.exists():
        stale_output = processed_dir / "refusal_day.parquet"
        removed = stale_output.exists()
        stale_output.unlink(missing_ok=True)
        return {"available": False, "reason": "No standalone refusal feed", "stale_daily_artifact_removed": removed}
    connection = _connection()
    try:
        frame = connection.execute(f"""
            SELECT COALESCE(CAST(org_in AS VARCHAR), 'Unknown organization') AS org_in,
              COALESCE(CAST(region_in AS VARCHAR), 'Unknown region') AS region_in,
              CAST(refuse_dt AS DATE) AS date, count(*)::BIGINT AS refusals
            FROM read_parquet({sql_literal(source)}) WHERE refuse_dt IS NOT NULL
            GROUP BY org_in, region_in, CAST(refuse_dt AS DATE)
            ORDER BY org_in, region_in, date
        """).fetchdf()
        missing = connection.execute(f"SELECT count(*) FROM read_parquet({sql_literal(source)}) WHERE refuse_dt IS NULL").fetchone()[0]
        frame.to_parquet(processed_dir / "refusal_day.parquet", index=False)
        return {"available": True, "daily_rows": len(frame), "refusals": int(frame["refusals"].sum()), "missing_date_rows": missing, "joined_to_referrals": False, "calendar": "Sparse observed event days; independent feed"}
    finally:
        connection.close()


def build_aggregations(processed_dir: str | Path = PROCESSED_DIR) -> dict:
    """Build real aggregates and descriptive indicators from cleaned parquet."""
    processed_dir = Path(processed_dir)
    daily, stats = _aggregate(processed_dir / "analytical.parquet")
    daily = add_historical_signals(daily)
    daily.to_parquet(processed_dir / "hospital_day.parquet", index=False)
    summary = {
        "hospital_day": stats,
        "refusal_feed": _aggregate_refusal_feed(processed_dir),
        "indicator": indicator_metadata(),
        "semantics": {
            "referrals": "Registered referrals in available parts, attributed to registration day",
            "hospitalized_refusals": "Unambiguous valid outcomes attributed to actual event day; invalid/conflicting records excluded",
            "reconstructed_open_cohort": "End-of-day eligible incoming minus cumulative valid exits, within the observed partial referral cohort",
            "average_wait_days": "Mean eligible completed wait, attributed to hospitalization day when the outcome is observed",
            "calendar": "Global minimum through maximum valid referral registration day; zero-fill absent days",
            "scope": "Retrospective partial-cohort analysis, not a current waiting list or hospital occupancy",
        },
        "forecast": {"status": "not_trained", "reason": "Complete longitudinal coverage, operational capacity and temporal backtesting required before 7/30/90-day forecasts"},
    }
    write_json(processed_dir / "aggregation_summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build historical hospital-day artifacts")
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    arguments = parser.parse_args()
    print(json.dumps(build_aggregations(arguments.processed_dir), ensure_ascii=False, indent=2, default=str))
