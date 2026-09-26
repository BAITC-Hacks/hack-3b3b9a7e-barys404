import json

from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
import pytest

import ml.load_forecast as forecast
from backend.core.utils import write_json


def hospital_days(days=52):
    calendar = pd.date_range("2025-01-01", periods=days, freq="D")
    return pd.DataFrame([
        {"hospital_mo": hospital, "date": day, "referrals": 4 + offset + (index % 7)}
        for hospital, offset in [("Hospital A", 0), ("Hospital B", 3)]
        for index, day in enumerate(calendar)
    ])


def test_fixed_origin_holdout_has_no_future_features_or_training_labels():
    frame = hospital_days()
    train, test, split = forecast.temporal_holdout(frame)
    origin = pd.Timestamp(split["forecast_origin"])
    assert train["target_date"].max() <= origin < test["target_date"].min()
    assert test["origin"].eq(origin).all()
    assert len(test) == 2 * forecast.HORIZON_DAYS
    assert not test.duplicated(["hospital_mo", "target_date"]).any()
    assert test.groupby("hospital_mo")["horizon"].apply(list).tolist() == [list(range(1, 8))] * 2
    changed = frame.copy()
    changed.loc[changed["date"] > origin, "referrals"] = 100000
    new_train, new_test, _ = forecast.temporal_holdout(changed)
    pd.testing.assert_frame_equal(train, new_train)
    pd.testing.assert_frame_equal(test.drop(columns="target"), new_test.drop(columns="target"))
    assert not test["target"].equals(new_test["target"])


def test_training_cutoff_and_features_match_inference():
    frame = hospital_days(45)
    cutoff = pd.Timestamp("2025-02-10")
    rows = forecast.make_training_rows(frame, target_before=cutoff)
    assert not rows.empty
    assert (rows["target_date"] < cutoff).all()
    assert (rows["target_date"] > rows["origin"]).all()
    origin = pd.Timestamp("2025-01-30")
    training_origin = rows.loc[rows["origin"].eq(origin)].reset_index(drop=True)
    inference = forecast.make_forecast_rows(frame, origin)
    pd.testing.assert_frame_equal(
        training_origin[forecast.FEATURE_COLUMNS], inference[forecast.FEATURE_COLUMNS])
    pd.testing.assert_series_equal(training_origin["seasonal_baseline"], inference["seasonal_baseline"])


def test_origin_day_is_observed_and_used_for_all_direct_horizons():
    frame = hospital_days(35).query("hospital_mo == 'Hospital A'").copy()
    origin = frame["date"].max()
    before = forecast.make_forecast_rows(frame, origin)
    frame.loc[frame["date"].eq(origin), "referrals"] += 70
    after = forecast.make_forecast_rows(frame, origin)
    np.testing.assert_allclose(after["lag_1"] - before["lag_1"], 70)
    np.testing.assert_allclose(after["mean_7"] - before["mean_7"], 10)
    np.testing.assert_allclose(after["mean_28"] - before["mean_28"], 2.5)
    np.testing.assert_allclose(after["lag_7"], before["lag_7"])
    assert after["mean_7"].nunique() == 1
    expected_seasonal = frame.set_index("date")["referrals"].reindex(after["target_date"] - np.timedelta64(7, "D"))
    np.testing.assert_allclose(after["seasonal_baseline"], expected_seasonal)


@pytest.mark.parametrize("problem", ["gap", "duplicate", "negative", "infinity", "missing", "bad_date"])
def test_invalid_history_is_rejected_instead_of_silently_changed(problem):
    frame = hospital_days()
    if problem == "gap":
        frame = frame.drop(index=4)
    elif problem == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif problem == "negative":
        frame.loc[0, "referrals"] = -1
    elif problem == "infinity":
        frame["referrals"] = frame["referrals"].astype(float)
        frame.loc[0, "referrals"] = np.inf
    elif problem == "missing":
        frame.loc[0, "hospital_mo"] = None
    else:
        frame.loc[0, "date"] = pd.NaT
    with pytest.raises(ValueError):
        forecast.temporal_holdout(frame)


def test_short_history_and_incomplete_hospital_are_handled_explicitly():
    with pytest.raises(ValueError, match="42"):
        forecast.temporal_holdout(hospital_days(41))
    train, test, _ = forecast.temporal_holdout(hospital_days(42))
    assert len(test) == 14
    assert train["horizon"].nunique() == 7
    frame = hospital_days()
    # One hospital stops before the end of the final week.
    frame = frame.loc[~(frame["hospital_mo"].eq("Hospital B") & frame["date"].eq(frame["date"].max()))]
    _, test, split = forecast.temporal_holdout(frame)
    assert len(test) == 7
    assert split["excluded_test_hospitals"] == 1


@pytest.fixture
def trained(tmp_path, monkeypatch):
    source = tmp_path / "hospital_day.parquet"
    model = tmp_path / "forecast.cbm"
    metadata = tmp_path / "forecast.json"
    quality = tmp_path / "data_quality_report.json"
    hospital_days().to_parquet(source, index=False)
    report = {"pipeline_complete": True, "source_fingerprint": "test-version"}
    write_json(quality, report)
    monkeypatch.setattr(forecast, "MODEL_PATH", model)
    monkeypatch.setattr(forecast, "METADATA_PATH", metadata)
    monkeypatch.setattr(forecast, "QUALITY_PATH", quality)
    monkeypatch.setattr(forecast, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr(forecast, "source_fingerprint", lambda: "test-version")
    result = forecast.train_load_forecast(source, model, metadata, fingerprint="test-version")
    return source, model, metadata, quality, result


def test_saved_model_metrics_and_seven_day_inference_are_reproducible(trained):
    source, model_path, _, _, result = trained
    assert result["test_period"]["end"].startswith("2025-02-21")
    assert result["rows"]["test"] == 14
    assert not result["split"]["refit_on_holdout"]
    test = pd.read_parquet(model_path.with_suffix(".validation.parquet"))
    model = CatBoostRegressor()
    model.load_model(str(model_path))
    predictions = np.maximum(0, model.predict(test[forecast.FEATURE_COLUMNS]))
    np.testing.assert_allclose(predictions, test["predicted_referrals"], rtol=0, atol=1e-12)
    assert np.mean(np.abs(test["target"] - predictions)) == pytest.approx(result["metrics"]["mae"])
    assert result["metrics"]["seasonal_baseline_mae"] == 0
    assert len(result["metrics_by_horizon"]) == 7
    assert forecast.forecast_status()["available"]
    future = forecast.forecast_next_week("Hospital A", source)
    assert future["date"].tolist() == pd.date_range("2025-02-22", periods=7).tolist()
    assert np.isfinite(future["predicted_referrals"]).all()
    assert (future["predicted_referrals"] >= 0).all()
    rows = forecast.make_forecast_rows(hospital_days(), pd.Timestamp("2025-02-21"))
    expected = np.maximum(0, model.predict(rows.loc[rows["hospital_mo"].eq("Hospital A"), forecast.FEATURE_COLUMNS]))
    np.testing.assert_allclose(future["predicted_referrals"], expected)
    explanation = forecast.explain_next_week("Hospital A", 3, source)
    assert explanation["prediction"] == pytest.approx(future.iloc[2]["predicted_referrals"])
    with pytest.raises(ValueError, match="28"):
        forecast.forecast_next_week("Unknown", source)


def test_changed_data_old_method_and_incomplete_preparation_block_inference(trained, monkeypatch):
    source, model_path, metadata_path, quality_path, metadata = trained
    report = json.loads(quality_path.read_text())
    with monkeypatch.context() as context:
        context.setattr(forecast, "source_fingerprint", lambda: "changed-files")
        assert not forecast.forecast_status(report)["available"]
        with pytest.raises(FileNotFoundError):
            forecast.forecast_next_week("Hospital A", source)
    write_json(quality_path, {**report, "pipeline_complete": False})
    assert not forecast.forecast_status(report)["available"]  # stale caller report cannot override disk
    with pytest.raises(ValueError, match="incomplete"):
        forecast.train_load_forecast()
    write_json(quality_path, report)
    write_json(metadata_path, [])
    assert not forecast.forecast_status()["available"]
    write_json(quality_path, [])
    write_json(metadata_path, metadata)
    assert not forecast.forecast_status()["available"]
    write_json(quality_path, report)
    write_json(metadata_path, {**metadata, "model_version": 1})
    assert not forecast.forecast_status()["available"]
    write_json(metadata_path, metadata)
    original_model = model_path.read_bytes()
    model_path.write_bytes(b"not the validated model")
    assert not forecast.forecast_status()["available"]
    model_path.write_bytes(original_model)
    changed = hospital_days()
    changed.loc[0, "referrals"] += 1
    changed.to_parquet(source, index=False)
    assert not forecast.forecast_status()["available"]
    with pytest.raises(FileNotFoundError):
        forecast.forecast_next_week("Hospital A", source)
