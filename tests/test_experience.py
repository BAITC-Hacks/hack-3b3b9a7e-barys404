"""Weekly gaps, full-period comparisons and aggregate-only briefing exports."""
from io import BytesIO

import pandas as pd
import pytest
from pypdf import PdfReader

from backend.analytics.dashboard_data import weekly_activity, recent_activity
from backend.analytics.briefing import build_briefing_pdf


@pytest.fixture
def activity_source(tmp_path):
    values = [("Hospital 'A'", "2025-01-06", 12), ("Hospital 'A'", "2025-01-13", 3),
              ("Hospital 'A'", "2025-01-27", 20), ("Other", "2025-01-06", 20),
              ("Other", "2025-01-20", 10), ("Other", "2025-01-27", 20)]
    rows = [{"hospital_mo": name, "registration_dt": pd.Timestamp(day), "region_origin_code": "01", "bed_profile": "321"}
            for name, day, count in values for _ in range(count)]
    path = tmp_path / "activity.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_heatmap_distinguishes_suppression_from_zero_and_marks_partial_weeks(activity_source):
    grid = weekly_activity({"start": "2025-01-06", "end": "2025-01-27"}, path=activity_source)
    assert len(grid) == 8
    a = grid.loc[grid.hospital.eq("Hospital 'A'")].set_index("week")
    assert a.loc["2025-01-06", "referrals"] == 12
    assert pd.isna(a.loc["2025-01-13", "referrals"])
    assert a.loc["2025-01-13", "suppressed"]
    assert a.loc["2025-01-20", "referrals"] == 0
    assert not a.loc["2025-01-20", "suppressed"]
    assert a.loc["2025-01-27", "partial_week"]
    assert not a.loc["2025-01-20", "partial_week"]
    assert weekly_activity({"hospital_mo": "' OR 1=1 --"}, path=activity_source).empty


def test_activity_compares_two_full_windows_and_respects_scope(activity_source):
    period, table = recent_activity({"start": "2025-01-06", "end": "2025-01-19", "hospital_mo": "Hospital 'A'"}, activity_source)
    assert period == {"start": "2025-01-13", "end": "2025-01-19", "previous_start": "2025-01-06", "previous_end": "2025-01-12"}
    assert len(table) == 1
    assert table.iloc[0]["current"] == 3
    assert table.iloc[0]["previous"] == 12
    assert table.iloc[0]["change_pct"] == -75
    period, table = recent_activity({"start": "2025-01-07", "end": "2025-01-19"}, activity_source)
    assert not period and table.empty


def briefing_payload(groups=6):
    return {"review_status": "reviewed_for_discussion", "source_fingerprint": "test-source-version",
            "created_at": "2026-09-24T12:00:00+00:00", "group_dimension": "hospital_mo", "minimum_group_size": 100,
            "filters": {"start": "2025-01-01", "end": "2025-03-31", "bed_profile": "321", "region_origin_code": "01"},
            "review_question": "Почему различаются сроки ожидания?",
            "aggregates": [{"organization_or_region": f'Городская многопрофильная больница № {i + 1} <Север & Юг>',
                            "referrals": 1200 + i, "median_wait_days": 2.5 if i else None,
                            "p90_wait_days": 12, "refusal_share_pct": 4.2} for i in range(groups)]}


def test_pdf_is_one_page_with_cyrillic_provenance_and_explicit_metric_scope():
    pdf = build_briefing_pdf(briefing_payload(), {"waiting": {"mae": 6.5133, "baseline_mae": 7.1198, "period": "2025-03-14 - 2025-03-31"}})
    parsed = PdfReader(BytesIO(pdf))
    assert len(parsed.pages) == 1
    text = parsed.pages[0].extract_text()
    for value in ["Сводка", "Север & Юг", "6,51", "7,12", "test-source-vers", "не к выбранным группам", "недоступны"]:
        assert value in text
    assert "Медиана" in text


def test_pdf_requires_review_and_bounds_comparison_size():
    payload = briefing_payload()
    payload["review_status"] = "pending"
    with pytest.raises(ValueError, match="Confirm"):
        build_briefing_pdf(payload, {})
    with pytest.raises(ValueError, match="one to six"):
        build_briefing_pdf(briefing_payload(7), {})
