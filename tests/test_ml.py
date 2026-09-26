"""Small artificial fixtures exclusively test leakage and model invariants."""
import numpy as np
import pandas as pd
import pytest

from ml.feature_engineering import CATEGORICAL_FEATURES, FEATURE_COLUMNS, make_features
from ml.train_waiting_model import aggregate_predictions, chronological_split, regression_metrics
from ml.waiting_estimator import calibrated_predictions, fit_calibration


def test_feature_allowlist_excludes_identifiers_and_all_outcomes():
    frame = pd.DataFrame({"registration_dt": ["2025-01-06"], "hospital_mo": [None], "wait_days": [12], "hospitalization_dt": ["2025-01-18"], "hospitalization_code": ["sensitive-key"], "planned_dt": ["2025-01-17"], "refusal_dt": ["2025-02-01"]})
    features = make_features(frame)
    assert features.columns.tolist() == FEATURE_COLUMNS
    assert features.loc[0, "registration_day_of_week"] == 0
    assert features.loc[0, "registration_day"] == 6
    assert features.loc[0, "hospital_mo"] == "__MISSING__"
    changed_outcomes = frame.assign(wait_days=90, hospitalization_dt="2025-03-01", hospitalization_code="other", planned_dt="2025-04-01")
    pd.testing.assert_frame_equal(features, make_features(changed_outcomes))


def test_invalid_registration_does_not_silently_impute():
    with pytest.raises(ValueError, match="invalid dates"):
        make_features({"registration_dt": "not a date"})


def _temporal_fixture():
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    return pd.DataFrame({"registration_dt": dates, "hospitalization_dt": dates + pd.Timedelta(hours=1), "wait_days": 1 / 24, "target_eligible": True})


def test_whole_date_split_purges_future_labels_and_uses_unlabeled_dates():
    frame = _temporal_fixture()
    # A train-window referral whose outcome is unavailable at the Jan 9 cutoff.
    frame.loc[1, "hospitalization_dt"] = pd.Timestamp("2025-01-09 00:00")
    frame.loc[1, "wait_days"] = 7
    # Jan 8 stays in the calendar although it has no usable outcome.
    frame.loc[7, "target_eligible"] = False
    frame = pd.concat([frame, frame.iloc[[8]].assign(registration_dt=pd.Timestamp("2025-01-09 14:00"), hospitalization_dt=pd.Timestamp("2025-01-10"))], ignore_index=True)
    train, test, info = chronological_split(frame)
    assert info["test_start"] == "2025-01-09T00:00:00"
    assert info["exclusions"]["early_labels_unavailable_at_cutoff"] == 1
    assert len(train) == 6
    assert len(test) == 3
    assert train["hospitalization_dt"].max() < pd.Timestamp(info["test_start"])
    assert set(train["registration_dt"].dt.date).isdisjoint(test["registration_dt"].dt.date)


def test_contradictory_outcomes_and_out_of_bounds_targets_cannot_train():
    frame = _temporal_fixture()
    frame["refusal_dt"] = pd.NaT
    frame.loc[1, "refusal_dt"] = pd.Timestamp("2025-01-02")
    frame.loc[2, "wait_days"] = -1
    frame.loc[3, "wait_days"] = 91
    train, _, info = chronological_split(frame)
    assert not {1, 2, 3}.intersection(train.index)
    assert info["exclusions"]["early_rows_without_eligible_target"] == 3


def test_too_little_history_fails_instead_of_random_split():
    with pytest.raises(ValueError, match="two distinct"):
        chronological_split(_temporal_fixture().iloc[[0]])


def test_metrics_are_computed_and_negative_improvement_is_reported():
    metrics = regression_metrics([0, 2], [10, 10], median_prediction=1)
    assert metrics["mae"] == 9
    assert metrics["baseline_mae"] == 1
    assert metrics["improvement_pct"] == -800
    assert metrics["rmse"] == pytest.approx(np.sqrt(82))


def test_aggregate_artifact_suppresses_small_groups_and_has_no_patient_rows():
    actual = [0.5] * 12 + [5.0] * 2
    predicted = [1.5] * 12 + [3.0] * 2
    result = aggregate_predictions(actual, predicted)
    assert len(result) == 1
    assert result[0]["count"] == 12
    assert result[0]["actual_mean"] == 0.5
    assert result[0]["predicted_mean"] == 1.5
    assert set(result[0]) == {"actual_bin", "count", "actual_mean", "predicted_mean"}


def test_persisted_model_inference_matches_evaluation_and_refuses_stale_data(tmp_path, monkeypatch):
    from catboost import CatBoostRegressor
    from backend.core import config
    from ml import predict
    from backend.core.utils import write_json

    # This local toy model validates serialization, not predictive performance.
    frame = pd.DataFrame({"registration_dt": pd.date_range("2025-01-01", periods=12), "hospital_mo": ["test-hospital"] * 12})
    features = make_features(frame)
    fitted = CatBoostRegressor(iterations=3, depth=2, verbose=False, allow_writing_files=False, thread_count=1)
    fitted.fit(features, np.arange(12, dtype=float), cat_features=CATEGORICAL_FEATURES)
    monkeypatch.setattr(config, "MODEL_PATH", tmp_path / "model.cbm")
    monkeypatch.setattr(config, "METADATA_PATH", tmp_path / "metadata.json")
    monkeypatch.setattr(config, "QUALITY_PATH", tmp_path / "quality.json")
    monkeypatch.setattr(predict, "source_fingerprint", lambda: "current")
    fitted.save_model(str(config.MODEL_PATH))
    calibration = fit_calibration(features, np.arange(12, dtype=float))
    write_json(config.METADATA_PATH, {"source_fingerprint": "current", "model_version": config.WAITING_MODEL_VERSION, "calibration": calibration})
    write_json(config.QUALITY_PATH, {"source_fingerprint": "current", "pipeline_complete": True})
    expected, _, _ = calibrated_predictions(features, fitted.predict(features), calibration)
    np.testing.assert_allclose(predict.predict_batch(frame), expected)
    assert predict.predict_waiting_time(frame.iloc[0].to_dict()) == pytest.approx(expected[0])
    write_json(config.QUALITY_PATH, {"source_fingerprint": "current", "pipeline_complete": False})
    assert predict.model_status()["available"] is False
    write_json(config.QUALITY_PATH, {"source_fingerprint": "current", "pipeline_complete": True})
    monkeypatch.setattr(predict, "source_fingerprint", lambda: "new-part-added")
    assert predict.model_status()["stale"] is True
    with pytest.raises(FileNotFoundError, match="changed"):
        predict.predict_waiting_time(frame.iloc[0].to_dict())


def test_supported_cohort_estimate_overrides_invalid_pooled_prediction():
    train = make_features(pd.DataFrame({"hospital_mo": ["H"] * 10, "bed_profile": ["P"] * 10, "registration_dt": "2025-01-01"}))
    calibration = fit_calibration(train, [5.] * 10)
    result, method, support = calibrated_predictions(train.iloc[:1], [-0.5], calibration)
    assert result.tolist() == [5.]
    assert method.tolist() == ["hospital_profile_median"]
    assert support.tolist() == [10]
    # Only provided training labels enter the artifact; no held-out rows needed.
    assert calibration["global"] == {"median": 5., "count": 10}


def test_sparse_and_unseen_groups_have_explicit_data_based_fallbacks():
    train = make_features(pd.DataFrame({"hospital_mo": ["H"] * 10 + ["Sparse"], "bed_profile": ["P"] * 11, "registration_dt": "2025-01-01"}))
    calibration = fit_calibration(train, [4.] * 10 + [2.])
    rows = make_features(pd.DataFrame({"hospital_mo": ["Sparse", "Unseen", "Sparse", "H", "Unseen"], "bed_profile": ["P", "P", "P", "Q", "Q"], "registration_dt": "2025-03-31"}, index=[9, 2, 7, 4, 1]))
    result, method, support = calibrated_predictions(rows, [3., 9., -1., 8., -3.], calibration)
    assert result.tolist() == [3., 4., 4., 4., 4.]
    assert method.tolist() == ["catboost", "profile_median", "profile_median", "hospital_median", "global_median"]
    assert support.tolist() == [0, 11, 11, 10, 11]


def test_real_same_day_median_is_not_replaced_with_arbitrary_floor():
    train = make_features(pd.DataFrame({"hospital_mo": ["H"] * 10, "bed_profile": ["P"] * 10, "registration_dt": "2025-01-01"}))
    calibration = fit_calibration(train, np.zeros(10))
    result, method, _ = calibrated_predictions(train.iloc[:1], [-1.], calibration)
    assert result[0] == 0
    assert method[0] == "hospital_profile_median"
    with pytest.raises(ValueError, match="invalid values"):
        calibrated_predictions(train.iloc[:1], [np.nan], calibration)
    with pytest.raises(ValueError, match="Missing waiting calibration"):
        calibrated_predictions(train.iloc[:1], [-1.], None)
    with pytest.raises(ValueError, match="nonnegative"):
        fit_calibration(train, [-1.] * 10)


def test_cohort_explanation_does_not_invent_shap_contributions(monkeypatch):
    from ml import explanations
    train = make_features(pd.DataFrame({"hospital_mo": ["H"] * 10, "bed_profile": ["P"] * 10, "registration_dt": "2025-01-01"}))
    monkeypatch.setattr(explanations, "load_metadata", lambda: {"calibration": fit_calibration(train, [5.] * 10), "split": {"test_start": "2025-03-14"}})
    class NegativeModel:
        def predict(self, features):
            return [-0.5]
    monkeypatch.setattr(explanations, "load_model", lambda: NegativeModel())
    result = explanations.explain_waiting({"hospital_mo": "H", "bed_profile": "P", "registration_dt": "2025-03-31"})
    assert result["prediction"] == 5.
    assert result["catboost_raw_prediction"] == -0.5
    assert result["contributions"] == []
    assert result["support"] == 10
