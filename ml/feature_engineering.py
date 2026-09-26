"""Shared, strictly registration-time features for training and inference.

The explicit allowlist prevents outcome columns or identifying composite keys
from accidentally becoming predictors when new source columns are added.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

CATEGORICAL_FEATURES = [
    "hospital_mo",
    "icd10_ref_diag_code",
    "bed_profile",
    "territorial_type",
    "referral_purpose",
    "finance_source",
]
CALENDAR_FEATURES = ["registration_day_of_week", "registration_day", "registration_month"]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + CALENDAR_FEATURES
MISSING_CATEGORY = "__MISSING__"


def make_features(records: pd.DataFrame | Mapping[str, Any]) -> pd.DataFrame:
    """Return CatBoost-ready features in an identical order at fit and predict.

    Missing categories have an explicit level. Dates are mandatory: imputing an
    arbitrary date would silently change the meaning of the prediction.
    """
    frame = pd.DataFrame([records]) if isinstance(records, Mapping) else records
    if "registration_dt" not in frame:
        raise ValueError("registration_dt is required for waiting-time prediction.")
    registration = pd.to_datetime(frame["registration_dt"], errors="coerce", format="mixed")
    if registration.isna().any():
        raise ValueError("registration_dt contains missing or invalid dates.")
    result = pd.DataFrame(index=frame.index)
    for column in CATEGORICAL_FEATURES:
        if column in frame:
            values = frame[column].astype("string").str.strip()
            result[column] = values.fillna(MISSING_CATEGORY).replace("", MISSING_CATEGORY).astype(str)
        else:
            result[column] = MISSING_CATEGORY
    result["registration_day_of_week"] = registration.dt.dayofweek.astype("int16")
    result["registration_day"] = registration.dt.day.astype("int16")
    result["registration_month"] = registration.dt.month.astype("int16")
    return result[FEATURE_COLUMNS]


def category_options(training_features: pd.DataFrame) -> dict[str, list[str]]:
    """Build demo options exclusively from fitted training categories."""
    return {column: sorted(training_features[column].unique().tolist()) for column in CATEGORICAL_FEATURES}
