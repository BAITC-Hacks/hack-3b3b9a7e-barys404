from pathlib import Path

import pandas as pd

from backend.core.config import ANALYTICAL_PATH
from backend.modules.analytics import dashboard_data as db

WAITING_FEATURES = (
    "icd10_ref_diag_code",
    "bed_profile",
    "territorial_type",
    "referral_purpose",
    "finance_source",
)


def hospital_exists(hospital: str, path: Path = ANALYTICAL_PATH) -> bool:
    result = db.aggregate_query(
        path,
        "SELECT count(*) AS n FROM read_parquet(?) WHERE hospital_mo = ?",
        [hospital],
    )
    return bool(result.iloc[0]["n"])


def referral_trend(filters: dict, path: Path = ANALYTICAL_PATH) -> pd.DataFrame:
    where, parameters = db.cohort_where(filters)
    return db.aggregate_query(
        path,
        f"""
        SELECT CAST(date_trunc('week', registration_dt) AS DATE) AS week,
               count(*) AS referrals
        FROM read_parquet(?) WHERE {where}
        GROUP BY 1 ORDER BY 1
        """,
        parameters,
    )


def waiting_feature_values(
    hospital: str,
    feature: str,
    profile: str | None = None,
    path: Path = ANALYTICAL_PATH,
) -> list[str]:
    if feature not in WAITING_FEATURES:
        raise ValueError("Unknown waiting feature")
    filter_profile = bool(profile) and feature != "bed_profile"
    profile_clause = "AND bed_profile = ?" if filter_profile else ""
    parameters = [hospital, *([profile] if filter_profile else [])]
    values = db.aggregate_query(
        path,
        f"""
        SELECT DISTINCT {feature} AS value FROM read_parquet(?)
        WHERE hospital_mo = ? {profile_clause}
          AND {feature} IS NOT NULL ORDER BY value
        """,
        parameters,
    )
    return values["value"].astype(str).tolist()
