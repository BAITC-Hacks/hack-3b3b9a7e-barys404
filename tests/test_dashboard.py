"""Dashboard cohort semantics and an empty-state smoke test."""
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.dashboard_data import historical_charts, overview, compare_groups, comparison_trends


@pytest.fixture
def dashboard_cohort(tmp_path):
    rows = pd.DataFrame({
        "hospital_mo": ["Hospital 'A'", "Hospital 'A'", "Other"],
        "region_origin_code": ["01", "01", "02"],
        "bed_profile": ["321", "321", "400"],
        "registration_dt": pd.to_datetime(["2025-01-02", "2025-01-03", "2025-02-01"]),
        "hospitalization_dt": pd.to_datetime(["2025-01-12", None, "2025-02-02"]),
        "refusal_dt": pd.to_datetime([None, None, None]),
        "outcome": ["hospitalized", "unresolved", "hospitalized"],
        "wait_days": [10.0, None, 1.0],
        "target_eligible": [True, False, True],
        "hospitalization_code": ["test-only-id-1", "test-only-id-2", "test-only-id-3"],
    })
    path = tmp_path / "analytical.parquet"
    rows.to_parquet(path, index=False)
    return path


def test_filters_are_parameterized_and_wait_denominator_excludes_unresolved(dashboard_cohort):
    filters = {"hospital_mo": "Hospital 'A'", "start": date(2025, 1, 1), "end": date(2025, 1, 5)}
    values = overview(filters, dashboard_cohort)
    assert values["referrals"] == 2
    assert values["unresolved"] == 1
    assert values["hospitalized"] == 1
    assert values["eligible"] == 1
    assert values["mean_wait"] == 10.0
    assert overview({"hospital_mo": "' OR 1=1 --"}, dashboard_cohort)["referrals"] == 0


def test_events_use_actual_outcome_dates_and_outputs_have_no_identifiers(dashboard_cohort):
    events, waits, hospitals = historical_charts({"start": date(2025, 1, 1), "end": date(2025, 1, 5)}, dashboard_cohort)
    admissions = events.loc[events["event"].eq("Hospitalizations")]
    assert admissions["date"].dt.date.tolist() == [date(2025, 1, 12)]
    assert admissions["records"].sum() == 1
    assert waits["records"].sum() == 1
    for output in (events, waits, hospitals):
        assert "hospitalization_code" not in output.columns
        assert not any(output.astype(str).apply(lambda column: column.str.contains("test-only-id")).any())


def test_streamlit_empty_state_never_fabricates_metrics(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    import src.ui as ui

    monkeypatch.setattr(ui, "ANALYTICAL_PATH", tmp_path / "absent.parquet")
    monkeypatch.setattr(ui, "QUALITY_PATH", tmp_path / "absent.json")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert not app.metric
    assert "Your data, ready for decisions." in [heading.value for heading in app.title]


def test_comparison_suppresses_small_groups_and_uses_known_outcome_denominator(dashboard_cohort):
    source = pd.read_parquet(dashboard_cohort)
    source = pd.concat([source] * 10, ignore_index=True)
    source.loc[source["hospital_mo"].eq("Other"), "outcome"] = "refused"
    source.loc[source["hospital_mo"].eq("Other"), "target_eligible"] = False
    source.to_parquet(dashboard_cohort, index=False)
    table = compare_groups({}, minimum=10, path=dashboard_cohort).set_index("organization_or_region")
    assert table.loc["Hospital 'A'", "referrals"] == 20
    assert table.loc["Hospital 'A'", "median_wait_days"] == 10
    assert table.loc["Other", "refusal_share_pct"] == 100
    assert pd.isna(table.loc["Other", "median_wait_days"])
    assert compare_groups({}, minimum=30, path=dashboard_cohort).empty
    assert compare_groups({"hospital_mo": "' OR 1=1 --"}, minimum=10, path=dashboard_cohort).empty
    trends = comparison_trends({}, "hospital_mo", ["Hospital 'A'"], path=dashboard_cohort)
    assert trends["referrals"].sum() == 20
    assert "hospitalization_code" not in table.columns
    with pytest.raises(ValueError):
        compare_groups({}, group_by="hospitalization_code", path=dashboard_cohort)
