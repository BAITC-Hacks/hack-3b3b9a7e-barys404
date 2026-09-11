"""Temporal accounting and future-invariance checks for historical analytics."""
import numpy as np
import pandas as pd
import pytest

from src.aggregation import aggregate_hospital_days, build_aggregations
from src.anomaly_detection import add_historical_signals


def _write_referrals(path, records):
    frame = pd.DataFrame(records)
    defaults = {"hospital_mo": "A", "region_origin_code": "01", "bed_profile": "surgery", "registration_dt": None, "hospitalization_dt": None, "refusal_dt": None, "wait_days": np.nan, "target_eligible": False, "outcome": "unresolved", "queue_reconstruction_eligible": True}
    for key, default in defaults.items():
        if key not in frame:
            frame[key] = default
        elif key not in {"hospitalization_dt", "refusal_dt", "registration_dt", "wait_days"}:
            frame[key] = frame[key].map(lambda value: default if pd.isna(value) else value)
    for key in ("registration_dt", "hospitalization_dt", "refusal_dt"):
        frame[key] = pd.to_datetime(frame[key])
    frame.to_parquet(path, index=False)


def test_events_are_counted_when_known_and_future_exits_do_not_extend_calendar(tmp_path):
    path = tmp_path / "analytical.parquet"
    _write_referrals(path, [
        {"registration_dt": "2025-01-01", "hospitalization_dt": "2025-01-03", "outcome": "hospitalized", "wait_days": 2.0, "target_eligible": True},
        {"registration_dt": "2025-01-01", "refusal_dt": "2025-01-02", "outcome": "refused"},
        {"registration_dt": "2025-01-03", "hospitalization_dt": "2099-01-01", "outcome": "hospitalized"},
    ])
    daily = aggregate_hospital_days(path)
    assert daily["date"].dt.strftime("%Y-%m-%d").tolist() == ["2025-01-01", "2025-01-02", "2025-01-03"]
    assert daily["referrals"].tolist() == [2, 0, 1]
    assert daily["hospitalized"].tolist() == [0, 0, 1]
    assert daily["refusals"].tolist() == [0, 1, 0]
    assert daily["reconstructed_open_cohort"].tolist() == [2, 1, 1]
    assert pd.isna(daily.loc[0, "average_wait_days"])
    assert daily.loc[2, "average_wait_days"] == 2.0


def test_invalid_or_conflicting_outcomes_are_not_assumed_open(tmp_path):
    path = tmp_path / "analytical.parquet"
    _write_referrals(path, [
        {"registration_dt": "2025-01-01", "outcome": "invalid_outcome", "queue_reconstruction_eligible": False},
        {"registration_dt": "2025-01-01", "hospitalization_dt": "2025-01-02", "refusal_dt": "2025-01-02", "outcome": "conflicting"},
        {"registration_dt": "2025-01-02", "hospitalization_dt": "2025-01-01", "outcome": "hospitalized"},
        {"registration_dt": "2025-01-03", "outcome": "unresolved"},
    ])
    daily = aggregate_hospital_days(path)
    assert daily["referrals"].sum() == 4
    assert daily["excluded_from_reconstruction"].sum() == 3
    assert daily["reconstructed_open_cohort"].tolist() == [0, 0, 1]
    assert daily["hospitalized"].sum() == 0


def test_zero_days_and_hospital_isolation(tmp_path):
    path = tmp_path / "analytical.parquet"
    _write_referrals(path, [{"hospital_mo": "A", "registration_dt": "2025-01-01"}, {"hospital_mo": "B", "registration_dt": "2025-01-03"}])
    daily = aggregate_hospital_days(path)
    assert len(daily) == 6
    assert daily.query("hospital_mo == 'A'")["reconstructed_open_cohort"].tolist() == [1, 1, 1]
    assert daily.query("hospital_mo == 'B'")["reconstructed_open_cohort"].tolist() == [0, 0, 1]


def _daily_series():
    frame = pd.DataFrame({"hospital_mo": "A", "date": pd.date_range("2025-01-01", periods=40), "referrals": 2, "hospitalized": 1, "refusals": 0, "reconstructed_open_cohort": 4})
    frame.loc[20, ["referrals", "refusals", "reconstructed_open_cohort"]] = [30, 6, 24]
    return frame


def test_signals_exclude_scored_day_and_future_rows():
    original = _daily_series()
    scored = add_historical_signals(original)
    assert scored.loc[20, "referrals_history_p95"] == 2
    assert scored.loc[20, "referrals_lag7_mean"] == 2
    assert scored.loc[20, "prototype_pressure"] == "HIGH"
    assert scored.loc[20, ["anomaly_referrals", "anomaly_refusals", "anomaly_open_cohort_growth"]].all()
    assert scored.loc[:13, "prototype_pressure"].eq("INSUFFICIENT_HISTORY").all()
    assert scored.loc[14, "prototype_pressure"] == "LOW"
    changed_future = original.copy()
    changed_future.loc[21:, ["referrals", "refusals", "reconstructed_open_cohort"]] = 100000
    pd.testing.assert_frame_equal(scored.iloc[:21], add_historical_signals(changed_future).iloc[:21])


def test_sparse_days_cannot_silently_become_daily_history():
    with pytest.raises(ValueError, match="dense"):
        add_historical_signals(_daily_series().drop(index=4))


def test_build_keeps_refusal_feed_separate(tmp_path):
    _write_referrals(tmp_path / "analytical.parquet", [{"registration_dt": "2025-01-01"}, {"registration_dt": "2025-01-03"}])
    pd.DataFrame({"org_in": ["A", "A"], "region_in": ["01", "01"], "refuse_dt": pd.to_datetime(["2025-01-02", "2025-01-02"])}).to_parquet(tmp_path / "refusals.parquet", index=False)
    summary = build_aggregations(tmp_path)
    assert not summary["refusal_feed"]["joined_to_referrals"]
    assert pd.read_parquet(tmp_path / "refusal_day.parquet")["refusals"].sum() == 2
    assert pd.read_parquet(tmp_path / "hospital_day.parquet")["refusals"].sum() == 0
    assert summary["forecast"]["status"] == "not_trained"


def test_empty_filtered_cohort_is_supported(tmp_path):
    _write_referrals(tmp_path / "analytical.parquet", [{"registration_dt": "2025-01-01"}])
    daily = aggregate_hospital_days(tmp_path / "analytical.parquet", {"hospital_mo": "absent"})
    assert daily.empty
    assert add_historical_signals(daily).empty


def test_missing_refusal_source_removes_stale_generated_daily_artifact(tmp_path):
    _write_referrals(tmp_path / "analytical.parquet", [{"registration_dt": "2025-01-01"}])
    stale = tmp_path / "refusal_day.parquet"
    pd.DataFrame({"org_in": ["Old hospital"], "region_in": ["01"], "date": pd.to_datetime(["2024-01-01"]), "refusals": [99]}).to_parquet(stale, index=False)
    summary = build_aggregations(tmp_path)
    assert not summary["refusal_feed"]["available"]
    assert summary["refusal_feed"]["stale_daily_artifact_removed"]
    assert not stale.exists()
