"""Training-only cohort calibration for a bounded, nonnegative wait estimate.

The temporal validation prefers supported local medians to the pooled CatBoost
median. CatBoost is retained for sparse known hospitals; invalid pooled outputs
fall back to supported profile history, never to an invented positive floor.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

VERSION = "waiting-cohort-calibration-v1"
MIN_SUPPORT = 10
LEVELS = {
    "hospital_profile": ["hospital_mo", "bed_profile"],
    "hospital": ["hospital_mo"],
    "profile": ["bed_profile"],
}


def fit_calibration(features: pd.DataFrame, target) -> dict:
    values = np.asarray(target, dtype=float)
    if len(features) != len(values) or not len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Calibration requires finite nonnegative training labels.")
    frame = features.reset_index(drop=True).assign(wait=values)
    result = {"version": VERSION, "minimum_support": MIN_SUPPORT,
              "trained_hospitals": sorted(features.hospital_mo.unique().tolist()),
              "global": {"median": float(np.median(values)), "count": len(values)}, "levels": {}}
    for name, keys in LEVELS.items():
        groups = frame.groupby(keys, dropna=False).wait.agg(["median", "count"]).reset_index()
        groups = groups.loc[groups["count"] >= MIN_SUPPORT]
        result["levels"][name] = [
            {"key": [str(row[key]) for key in keys], "median": float(row["median"]), "count": int(row["count"])}
            for row in groups.to_dict(orient="records")
        ]
    return result


def calibrated_predictions(features: pd.DataFrame, raw_predictions, calibration: dict | None):
    """Same inference boundary for training evaluation, API and batch use."""
    raw = np.asarray(raw_predictions, dtype=float).reshape(-1)
    if len(raw) != len(features) or not np.isfinite(raw).all():
        raise ValueError("Waiting model returned invalid values.")
    prediction = raw.copy()
    method = np.full(len(raw), "catboost", dtype=object)
    support = np.zeros(len(raw), dtype=int)
    if calibration is None:
        raise ValueError("Missing waiting calibration; retrain the model.")
    if calibration.get("version") != VERSION:
        raise ValueError("Unsupported waiting calibration version; retrain the model.")
    fallback = (raw <= 0) | ~features.hospital_mo.isin(calibration["trained_hospitals"]).to_numpy()
    prediction[fallback] = calibration["global"]["median"]
    method[fallback] = "global_median"
    support[fallback] = calibration["global"]["count"]
    # Supported hospital history always takes precedence; profile/global only
    # handle invalid CatBoost outputs when a hospital has insufficient history.
    for name in ("profile", "hospital", "hospital_profile"):
        lookup = {tuple(row["key"]): row for row in calibration["levels"].get(name, [])}
        for i, key in enumerate(features[LEVELS[name]].itertuples(index=False, name=None)):
            row = lookup.get(tuple(str(value) for value in key))
            if row and (name != "profile" or fallback[i]):
                prediction[i], method[i], support[i] = row["median"], f"{name}_median", row["count"]
    if not np.isfinite(prediction).all() or (prediction < 0).any():
        raise ValueError("Invalid calibrated waiting estimate.")
    return prediction, method, support
