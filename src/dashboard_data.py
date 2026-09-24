"""Bounded, aggregate-only reads for the dashboard; never materialize referral rows."""
from pathlib import Path

import duckdb
import pandas as pd

from src.config import ANALYTICAL_PATH, DUCKDB_MEMORY_LIMIT, THREAD_COUNT


DIMENSIONS = {"region_origin_code", "hospital_mo", "bed_profile"}


def file_version(path):
    path = Path(path)
    if not path.exists():
        return (0, 0)
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def aggregate_query(path, sql, parameters=()):
    """SQL templates must be code-owned and aggregate/project before calling df()."""
    with duckdb.connect(config={"memory_limit": DUCKDB_MEMORY_LIMIT, "threads": THREAD_COUNT}) as con:
        return con.execute(sql, [str(path), *parameters]).df()


def dimensions(path=ANALYTICAL_PATH):
    result = {}
    for column in sorted(DIMENSIONS):
        result[column] = aggregate_query(
            path,
            f"SELECT DISTINCT {column} AS value FROM read_parquet(?) "
            f"WHERE {column} IS NOT NULL ORDER BY value",
        )["value"].astype(str).tolist()
    dates = aggregate_query(path, "SELECT min(registration_dt) AS first, max(registration_dt) AS last FROM read_parquet(?)")
    result["dates"] = dates.iloc[0].to_dict()
    return result


def cohort_where(filters):
    clauses, values = ["TRUE"], []
    for column in sorted(DIMENSIONS):
        value = filters.get(column)
        if value is not None:
            clauses.append(f"{column} = ?")
            values.append(value)
    if filters.get("start"):
        clauses.append("CAST(registration_dt AS DATE) >= CAST(? AS DATE)")
        values.append(str(filters["start"]))
    if filters.get("end"):
        clauses.append("CAST(registration_dt AS DATE) <= CAST(? AS DATE)")
        values.append(str(filters["end"]))
    return " AND ".join(clauses), values


def overview(filters, path=ANALYTICAL_PATH):
    where, params = cohort_where(filters)
    sql = f"""SELECT count(*) AS referrals,
        count(*) FILTER (WHERE outcome = 'hospitalized') AS hospitalized,
        count(*) FILTER (WHERE outcome = 'refused') AS refused,
        count(*) FILTER (WHERE outcome = 'unresolved') AS unresolved,
        count(*) FILTER (WHERE outcome = 'conflicting') AS conflicting,
        count(*) FILTER (WHERE outcome = 'invalid_outcome') AS invalid_outcome,
        count(*) FILTER (WHERE target_eligible) AS eligible,
        avg(wait_days) FILTER (WHERE target_eligible) AS mean_wait,
        median(wait_days) FILTER (WHERE target_eligible) AS median_wait,
        count(DISTINCT hospital_mo) AS hospitals
        FROM read_parquet(?) WHERE {where}"""
    return aggregate_query(path, sql, params).iloc[0].to_dict()


def historical_charts(filters, path=ANALYTICAL_PATH):
    where, params = cohort_where(filters)
    events = aggregate_query(path, f"""
        WITH cohort AS (SELECT registration_dt, hospitalization_dt, refusal_dt, outcome
            FROM read_parquet(?) WHERE {where}),
        events AS (
            SELECT CAST(registration_dt AS DATE) AS date, 'Referrals' AS event FROM cohort WHERE registration_dt IS NOT NULL
            UNION ALL
            SELECT CAST(hospitalization_dt AS DATE), 'Hospitalizations' FROM cohort WHERE outcome='hospitalized'
            UNION ALL
            SELECT CAST(refusal_dt AS DATE), 'Refusals' FROM cohort WHERE outcome='refused')
        SELECT date, event, count(*) AS records FROM events WHERE date IS NOT NULL GROUP BY ALL ORDER BY date
        """, params)
    waits = aggregate_query(path, f"""SELECT floor(wait_days)::INTEGER AS waiting_day,
        count(*) AS records FROM read_parquet(?) WHERE {where} AND target_eligible
        GROUP BY waiting_day ORDER BY waiting_day""", params)
    hospitals = aggregate_query(path, f"""SELECT hospital_mo AS hospital,
        count(*) AS referrals, count(*) FILTER (WHERE outcome='unresolved') AS unresolved,
        count(*) FILTER (WHERE outcome='hospitalized') AS hospitalized,
        count(*) FILTER (WHERE outcome='refused') AS refused,
        avg(wait_days) FILTER (WHERE target_eligible) AS mean_wait_days
        FROM read_parquet(?) WHERE {where} GROUP BY hospital_mo
        ORDER BY referrals DESC LIMIT 20""", params)
    return events, waits, hospitals


def pressure_rows(path, hospital=None, start=None, end=None):
    clauses, params = ["TRUE"], []
    if hospital:
        clauses.append("hospital_mo = ?")
        params.append(hospital)
    if start:
        clauses.append("date >= CAST(? AS DATE)")
        params.append(str(start))
    if end:
        clauses.append("date <= CAST(? AS DATE)")
        params.append(str(end))
    where = " AND ".join(clauses)
    # Already hospital/day aggregates; bounded projection never contains individual identifiers.
    return aggregate_query(path, f"""SELECT hospital_mo, date, referrals, hospitalized,
        refusals, reconstructed_open_cohort, prototype_pressure,
        pressure_reason, history_days, anomaly_referrals, anomaly_refusals,
        anomaly_open_cohort_growth
        FROM read_parquet(?) WHERE {where} ORDER BY date DESC, referrals DESC LIMIT 30000""", params)


def compare_groups(filters, group_by="hospital_mo", minimum=30, path=ANALYTICAL_PATH):
    """Descriptive comparisons, never a capacity or clinical-quality ranking."""
    if group_by not in {"hospital_mo", "region_origin_code"}:
        raise ValueError("Compare hospitals or origin regions only.")
    if minimum < 10:
        raise ValueError("At least ten referrals per comparison group are required.")
    where, params = cohort_where(filters)
    return _comparison_query(path, where, params, group_by, minimum)


def _comparison_query(path, where, params, group_by, minimum):
    # Keep the source parameter first; thresholds are validated integers.
    return aggregate_query(path, f"""
        WITH source AS (SELECT {group_by}, outcome, target_eligible, wait_days FROM read_parquet(?) WHERE {where})
        SELECT COALESCE({group_by}, 'Unknown') AS organization_or_region,
          count(*) AS referrals,
          count(*) FILTER(WHERE outcome='hospitalized') AS hospitalized,
          count(*) FILTER(WHERE outcome='refused') AS refused,
          count(*) FILTER(WHERE outcome='unresolved') AS unresolved,
          count(*) FILTER(WHERE outcome IN ('invalid_outcome','conflicting')) AS excluded_outcomes,
          count(*) FILTER(WHERE target_eligible) AS eligible_waits,
          CASE WHEN count(*) FILTER(WHERE target_eligible) >= {int(minimum)}
            THEN median(wait_days) FILTER(WHERE target_eligible) END AS median_wait_days,
          CASE WHEN count(*) FILTER(WHERE target_eligible) >= {int(minimum)}
            THEN quantile_cont(wait_days, .9) FILTER(WHERE target_eligible) END AS p90_wait_days,
          CASE WHEN count(*) FILTER(WHERE outcome IN ('hospitalized','refused')) >= {int(minimum)}
            THEN 100.0 * count(*) FILTER(WHERE outcome='refused') /
              count(*) FILTER(WHERE outcome IN ('hospitalized','refused')) END AS refusal_share_pct
        FROM source GROUP BY 1 HAVING count(*) >= {int(minimum)} ORDER BY referrals DESC, organization_or_region
        """, params)


def comparison_trends(filters, group_by, selected, minimum=10, path=ANALYTICAL_PATH):
    if group_by not in {"hospital_mo", "region_origin_code"} or not 1 <= len(selected) <= 6 or minimum < 10:
        raise ValueError("Select one to six hospitals/regions; minimum group size is ten.")
    where, params = cohort_where(filters)
    placeholders = ','.join('?' for _ in selected)
    return aggregate_query(path, f"""
        SELECT COALESCE({group_by}, 'Unknown') AS organization_or_region,
          CAST(date_trunc('week', registration_dt) AS DATE) AS week, count(*) AS referrals
        FROM read_parquet(?) WHERE {where} AND COALESCE({group_by}, 'Unknown') IN ({placeholders})
        GROUP BY 1, 2 HAVING count(*) >= {int(minimum)} ORDER BY week, organization_or_region
        """, [*params, *selected])


def weekly_activity(filters, selected=None, limit=15, minimum=10, path=ANALYTICAL_PATH):
    """Dense, bounded weekly grid. Suppressed small cells stay NaN, never zero."""
    if not 1 <= limit <= 30 or minimum < 10:
        raise ValueError("Use up to 30 organizations and a suppression threshold of at least 10.")
    where, params = cohort_where(filters)
    hospitals = aggregate_query(path, f"""SELECT hospital_mo AS hospital, count(*) AS referrals
        FROM read_parquet(?) WHERE {where} AND hospital_mo IS NOT NULL
        GROUP BY hospital_mo ORDER BY referrals DESC, hospital_mo""", params)
    if selected is not None:
        hospitals = hospitals.loc[hospitals.hospital.isin(selected)]
    names = hospitals.head(limit).hospital.tolist()
    if not names:
        return pd.DataFrame(columns=["hospital", "week", "referrals", "suppressed", "partial_week"])
    bounds = aggregate_query(path, "SELECT min(registration_dt) AS first, max(registration_dt) AS last FROM read_parquet(?)").iloc[0]
    if pd.isna(bounds["first"]) or pd.isna(bounds["last"]):
        return pd.DataFrame(columns=["hospital", "week", "referrals", "suppressed", "partial_week"])
    start = max(pd.Timestamp(bounds["first"]).normalize(), pd.Timestamp(filters.get("start") or bounds["first"]).normalize())
    end = min(pd.Timestamp(bounds["last"]).normalize(), pd.Timestamp(filters.get("end") or bounds["last"]).normalize())
    if start > end:
        return pd.DataFrame(columns=["hospital", "week", "referrals", "suppressed", "partial_week"])
    placeholders = ",".join("?" for _ in names)
    observed = aggregate_query(path, f"""SELECT hospital_mo AS hospital,
        CAST(date_trunc('week', registration_dt) AS DATE) AS week, count(*) AS referrals
        FROM read_parquet(?) WHERE {where} AND hospital_mo IN ({placeholders})
        GROUP BY 1, 2 ORDER BY week""", [*params, *names])
    weeks = pd.date_range(start - pd.Timedelta(days=start.weekday()), end, freq="W-MON")
    index = pd.MultiIndex.from_product([names, weeks], names=["hospital", "week"])
    grid = observed.set_index(["hospital", "week"]).reindex(index, fill_value=0).reset_index()
    grid["suppressed"] = grid.referrals.between(1, minimum - 1)
    grid.loc[grid.suppressed, "referrals"] = float("nan")
    grid["partial_week"] = (grid.week < start) | ((grid.week + pd.Timedelta(days=6)) > end)
    return grid


def recent_activity(filters, path=ANALYTICAL_PATH):
    """Compare two full consecutive 7-day windows within the selected source interval."""
    bounds = aggregate_query(path, "SELECT min(registration_dt) AS first, max(registration_dt) AS last FROM read_parquet(?)").iloc[0]
    if pd.isna(bounds["first"]) or pd.isna(bounds["last"]):
        return {}, pd.DataFrame()
    first = max(pd.Timestamp(bounds["first"]).normalize(), pd.Timestamp(filters.get("start") or bounds["first"]).normalize())
    end = min(pd.Timestamp(bounds["last"]).normalize(), pd.Timestamp(filters.get("end") or bounds["last"]).normalize())
    if (end - first).days < 13:
        return {}, pd.DataFrame()
    current_start, previous_start = end - pd.Timedelta(days=6), end - pd.Timedelta(days=13)
    narrowed = {**filters, "start": previous_start.date(), "end": end.date()}
    where, params = cohort_where(narrowed)
    # Keep the source placeholder first, then the period boundary and cohort filters.
    table = aggregate_query(path, f"""WITH source AS (
        SELECT hospital_mo, registration_dt, region_origin_code, bed_profile FROM read_parquet(?))
        SELECT hospital_mo AS hospital,
        count(*) FILTER(WHERE CAST(registration_dt AS DATE) >= CAST(? AS DATE)) AS current,
        count(*) FILTER(WHERE CAST(registration_dt AS DATE) < CAST(? AS DATE)) AS previous
        FROM source WHERE {where} GROUP BY hospital_mo ORDER BY current DESC, hospital_mo""",
        [str(current_start.date()), str(current_start.date()), *params])
    table["change_pct"] = 100 * (table.current - table.previous) / table.previous.replace(0, float("nan"))
    period = {"start": str(current_start.date()), "end": str(end.date()),
              "previous_start": str(previous_start.date()), "previous_end": str((current_start - pd.Timedelta(days=1)).date())}
    return period, table


def hospital_profiles(filters, path=ANALYTICAL_PATH):
    where, params = cohort_where(filters)
    return aggregate_query(path, f"""SELECT COALESCE(bed_profile, 'Не указан') AS profile,
        count(*) AS referrals, count(*) FILTER(WHERE target_eligible) AS eligible,
        CASE WHEN count(*) FILTER(WHERE target_eligible) >= 10
        THEN median(wait_days) FILTER(WHERE target_eligible) END AS median_wait
        FROM read_parquet(?) WHERE {where} GROUP BY 1 ORDER BY referrals DESC, profile LIMIT 8""", params)


def representative_profile(hospital, options, path=ANALYTICAL_PATH):
    """An observed common category combination, never an individual record."""
    columns = ["hospital_mo", "icd10_ref_diag_code", "bed_profile", "territorial_type", "referral_purpose", "finance_source"]
    names = ", ".join(columns)
    table = aggregate_query(path, f"""SELECT {names}, count(*) AS records FROM read_parquet(?)
        WHERE hospital_mo = ? AND target_eligible GROUP BY {names}
        HAVING count(*) >= 10 ORDER BY records DESC, {names} LIMIT 100""", [hospital])
    for row in table.to_dict(orient="records"):
        if all(row[name] in options.get(name, []) for name in columns):
            return {name: row[name] for name in columns}
    return {}
