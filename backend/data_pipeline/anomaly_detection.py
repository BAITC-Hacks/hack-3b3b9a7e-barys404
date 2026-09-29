"""Transparent historical signals; no capacity estimate or load forecast.

All reference windows end yesterday. Counts must be daily, including zero days,
so a seven-row window really represents seven calendar days.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PROTOTYPE_LABEL = (
    "Prototype risk indicator — not yet clinically/operationally validated."
)
SIGNAL_COLUMNS = ("referrals", "refusals", "reconstructed_open_cohort")
HISTORY_WINDOW = 28
MIN_HISTORY_DAYS = 14


def add_historical_signals(
    daily: pd.DataFrame,
    *,
    history_window: int = HISTORY_WINDOW,
    min_history: int = MIN_HISTORY_DAYS,
) -> pd.DataFrame:
    if not 1 <= min_history <= history_window:
        raise ValueError("Require 1 <= min_history <= history_window")

    result = _prepare_daily_counts(daily)
    _add_lagged_statistics(result, history_window, min_history)
    high, has_history = _set_pressure_levels(result, min_history)
    _add_anomaly_flags(result, high, has_history, history_window, min_history)
    return result


def _prepare_daily_counts(daily: pd.DataFrame) -> pd.DataFrame:
    required = {"hospital_mo", "date", *SIGNAL_COLUMNS}
    missing = required.difference(daily.columns)
    if missing:
        raise ValueError(f"Missing daily columns: {sorted(missing)}")
    result = daily.copy()
    result["date"] = pd.to_datetime(result["date"]).dt.normalize()
    if result[["hospital_mo", "date"]].isna().any().any():
        raise ValueError("Hospital and date must be present")
    if result.duplicated(["hospital_mo", "date"]).any():
        raise ValueError("Expected one row per hospital and calendar day")
    result = result.sort_values(["hospital_mo", "date"]).reset_index(drop=True)
    day_gaps = result.groupby("hospital_mo", sort=False)["date"].diff().dropna()
    if not day_gaps.dt.total_seconds().eq(86400).all():
        raise ValueError("Daily series must be dense; include zero-count calendar days")
    if result[list(SIGNAL_COLUMNS)].isna().any().any():
        raise ValueError("Daily count columns cannot contain missing values")
    return result


def _add_lagged_statistics(
    result: pd.DataFrame,
    history_window: int,
    min_history: int,
) -> None:
    groups = result.groupby("hospital_mo", sort=False)
    result["history_days"] = groups.cumcount().clip(upper=history_window)
    for column in (*SIGNAL_COLUMNS, "hospitalized"):
        if column not in result:
            continue
        result[f"{column}_lag7_mean"] = groups[column].transform(
            lambda values: values.shift(1).rolling(7, min_periods=7).mean()
        )
        result[f"{column}_lag7_sum"] = groups[column].transform(
            lambda values: values.shift(1).rolling(7, min_periods=7).sum()
        )
        if column in SIGNAL_COLUMNS:
            for percentile, quantile in ((75, 0.75), (95, 0.95)):
                result[f"{column}_history_p{percentile}"] = groups[column].transform(
                    lambda values, q=quantile: (
                        values.shift(1)
                        .rolling(history_window, min_periods=min_history)
                        .quantile(q)
                    )
                )


def _set_pressure_levels(
    result: pd.DataFrame,
    min_history: int,
) -> tuple[pd.DataFrame, pd.Series]:
    has_history = result["history_days"].ge(min_history)
    high = pd.DataFrame(
        {
            column: result[column].gt(result[f"{column}_history_p95"])
            for column in SIGNAL_COLUMNS
        }
    )
    medium = pd.DataFrame(
        {
            column: result[column].gt(result[f"{column}_history_p75"])
            for column in SIGNAL_COLUMNS
        }
    )
    result["prototype_pressure"] = np.select(
        [~has_history, high.any(axis=1), medium.any(axis=1)],
        ["INSUFFICIENT_HISTORY", "HIGH", "MEDIUM"],
        default="LOW",
    )
    result["pressure_reason"] = "Within the prior historical percentile range"
    result.loc[~has_history, "pressure_reason"] = (
        f"Fewer than {min_history} prior calendar days"
    )
    for level, exceedances, percentile in (("MEDIUM", medium, 75), ("HIGH", high, 95)):
        indices = result.index[result["prototype_pressure"].eq(level)]
        result.loc[indices, "pressure_reason"] = exceedances.loc[indices].apply(
            lambda row: (
                ", ".join(row.index[row]) + f" > prior {percentile}th percentile"
            ),
            axis=1,
        )
    return high, has_history


def _add_anomaly_flags(
    result: pd.DataFrame,
    high: pd.DataFrame,
    has_history: pd.Series,
    history_window: int,
    min_history: int,
) -> None:
    groups = result.groupby("hospital_mo", sort=False)
    result["anomaly_referrals"] = high["referrals"] & has_history
    result["anomaly_refusals"] = high["refusals"] & has_history

    result["open_cohort_growth"] = groups["reconstructed_open_cohort"].diff()
    growth_groups = result.groupby("hospital_mo", sort=False)["open_cohort_growth"]
    result["open_cohort_growth_history_p95"] = growth_groups.transform(
        lambda values: (
            values.shift(1)
            .rolling(history_window, min_periods=min_history)
            .quantile(0.95)
        )
    )
    result["anomaly_open_cohort_growth"] = result["open_cohort_growth"].gt(0) & result[
        "open_cohort_growth"
    ].gt(result["open_cohort_growth_history_p95"])


def indicator_metadata() -> dict:
    return {
        "label": PROTOTYPE_LABEL,
        "reference_window_days": HISTORY_WINDOW,
        "minimum_prior_days": MIN_HISTORY_DAYS,
        "windows": "Strictly before the scored day; dense calendar with zero counts",
        "pressure_rule": "HIGH: any count > prior p95; MEDIUM: any count > prior p75; otherwise LOW",
        "signals": list(SIGNAL_COLUMNS),
        "anomaly_rule": "Positive referrals/refusals exceed prior p95; positive open-cohort growth exceeds prior growth p95",
        "limitations": [
            "Descriptive heuristic with selected percentile thresholds, not calibrated operational risk",
            "Zero days mean no records in supplied files, not proof of no real activity",
            "Partial referral cohort; no measured bed capacity, occupancy or real-time queue",
            "End-of-day indicators are not predictions available at the start of that day",
        ],
    }
