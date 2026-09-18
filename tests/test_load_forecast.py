from pathlib import Path

import pandas as pd

from src.load_forecast import HORIZON_DAYS, forecast_next_week, make_training_rows, train_load_forecast


def hospital_days(days=52):
    calendar = pd.date_range("2025-01-01", periods=days, freq="D")
    rows = []
    for hospital, offset in [("Hospital A", 0), ("Hospital B", 3)]:
        for index, day in enumerate(calendar):
            rows.append({"hospital_mo": hospital, "date": day, "referrals": 4 + offset + (index % 7)})
    return pd.DataFrame(rows)


def test_training_rows_do_not_use_future_target_before_cutoff():
    frame = hospital_days(45)
    cutoff = pd.Timestamp("2025-02-10")
    rows = make_training_rows(frame, target_before=cutoff)
    assert not rows.empty
    assert (rows["target_date"] < cutoff).all()
    assert (rows["target_date"] > rows["origin"]).all()


def test_forecast_trains_on_chronological_holdout_and_returns_seven_days(tmp_path, monkeypatch):
    source = tmp_path / "hospital_day.parquet"
    model = tmp_path / "forecast.cbm"
    metadata = tmp_path / "forecast.json"
    hospital_days().to_parquet(source, index=False)
    result = train_load_forecast(source, model, metadata, fingerprint="test-version")
    assert result["forecast_target"] == "daily referral count received by hospital"
    assert result["test_period"]["end"].startswith("2025-02-21")
    # Seven target dates × seven valid forecast origins × two hospitals.
    assert result["rows"]["test"] == 98
    import src.load_forecast as forecast_module
    monkeypatch.setattr(forecast_module, "MODEL_PATH", model)
    monkeypatch.setattr(forecast_module, "METADATA_PATH", metadata)
    future = forecast_next_week("Hospital A", source)
    assert len(future) == HORIZON_DAYS
    assert future["date"].min() == pd.Timestamp("2025-02-22")
    assert (future["predicted_referrals"] >= 0).all()
