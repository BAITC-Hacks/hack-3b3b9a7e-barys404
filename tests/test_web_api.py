"""Regression tests for the web directory and waiting-result contracts."""
from datetime import date

import pandas as pd
import pytest
from fastapi import HTTPException

from backend.api import main as api
from backend.analytics.dashboard_data import hospital_directory


def test_directory_lists_small_hospitals_but_suppresses_unstable_rates(tmp_path):
    cohort = pd.DataFrame({
        "hospital_mo": ["Large"] * 10 + ["Small"],
        "region_origin_code": ["01"] * 11,
        "bed_profile": ["Cardiology"] * 10 + ["Allergy"],
        "registration_dt": pd.to_datetime(["2025-01-01"] * 11),
        "outcome": ["hospitalized"] * 11,
        "target_eligible": [True] * 11,
        "wait_days": [2.0] * 10 + [5.0],
    })
    path = tmp_path / "cohort.parquet"
    cohort.to_parquet(path)

    rows = hospital_directory({}, path).set_index("organization_or_region")
    assert set(rows.index) == {"Large", "Small"}
    assert rows.loc["Small", "referrals"] == 1
    assert pd.isna(rows.loc["Small", "median_wait_days"])
    assert rows.loc["Large", "median_wait_days"] == 2
    filtered = hospital_directory({"bed_profile": "Allergy"}, path)
    assert filtered.organization_or_region.tolist() == ["Small"]


def test_directory_search_and_pagination_apply_to_all_matches(monkeypatch):
    monkeypatch.setattr(api, "ready", lambda: {})
    monkeypatch.setattr(api.db, "hospital_directory", lambda filters: pd.DataFrame({
        "organization_or_region": ["Central A", "Other", "Central B"],
        "referrals": [20, 15, 1],
    }))
    result = api.hospitals(start=None, end=None, region=None, profile=None,
                           search="central", limit=1, offset=1)
    assert result["total"] == 2
    assert result["items"][0]["organization_or_region"] == "Central B"


@pytest.mark.parametrize("method,support", [("hospital_profile_median", 15), ("global_median", 0)])
def test_supported_wait_prediction_is_served_despite_negative_catboost(monkeypatch, method, support):
    monkeypatch.setattr(api, "ready", lambda: {})
    monkeypatch.setattr(api, "model_status", lambda: {"available": True})
    monkeypatch.setattr(api, "check_hospital", lambda hospital: None)
    monkeypatch.setattr(api, "resolve_hospital", lambda user, hospital_id, **kwargs: "H")
    monkeypatch.setattr(api, "load_metadata", lambda: {
        "feature_options": {key: [value] for key, value in {
            "hospital_mo": "H", "icd10_ref_diag_code": "I50.0",
            "bed_profile": "Cardiology", "territorial_type": "City",
            "referral_purpose": "Treatment", "finance_source": "Public",
        }.items()},
        "metrics": {"mae": 5.5}, "test_period": {"start": "2025-03-14", "end": "2025-03-31"},
    })
    monkeypatch.setattr(api, "explain_waiting", lambda record: {
        "prediction": 5.0, "raw_prediction": 5.0, "catboost_raw_prediction": -0.5,
        "method": method, "support": 15,
        "training_cutoff": "2025-03-14", "contributions": [],
    })
    result = api.predict_wait(api.WaitingRequest(
        hospital_id="H", icd10_ref_diag_code="I50.0", bed_profile="Cardiology",
        territorial_type="City", referral_purpose="Treatment",
        finance_source="Public", registration_dt=date(2025, 3, 31),
    ))
    assert result["clipped"] is False
    assert result["prediction"] == 5.0
    assert result["method"] == method
    assert result["support"] == support
    assert result["reference"] == {"median_wait_days": 5.0, "eligible": support}


@pytest.mark.parametrize("field,value", [("registration_dt", date(2026, 9, 26)),
                                        ("icd10_ref_diag_code", "UNKNOWN")])
def test_wait_api_refuses_unvalidated_dates_and_unknown_categories(monkeypatch, field, value):
    record = dict(hospital_id="H", icd10_ref_diag_code="I50.0", bed_profile="P",
                  territorial_type="City", referral_purpose="Treatment",
                  finance_source="Public", registration_dt=date(2025, 3, 31))
    fitted_options = {key: [item] for key, item in record.items() if key not in {"registration_dt", "hospital_id"}}
    monkeypatch.setattr(api, "ready", lambda: {})
    monkeypatch.setattr(api, "model_status", lambda: {"available": True})
    monkeypatch.setattr(api, "check_hospital", lambda hospital: None)
    monkeypatch.setattr(api, "resolve_hospital", lambda user, hospital_id, **kwargs: "H")
    monkeypatch.setattr(api, "load_metadata", lambda: {
        "feature_options": fitted_options,
        "test_period": {"start": "2025-03-14", "end": "2025-03-31"},
    })
    record[field] = value
    with pytest.raises(HTTPException) as error:
        api.predict_wait(api.WaitingRequest(**record))
    assert error.value.status_code == 422
