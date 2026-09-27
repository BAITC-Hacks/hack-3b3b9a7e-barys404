"""Signals retain earlier reference history and isolate the requested cohort."""
import pandas as pd
import pytest

from backend.analytics.aggregation import aggregate_hospital_days
from backend.analytics.anomaly_detection import add_historical_signals
from backend.analytics.monitoring import signal_feed


@pytest.fixture
def sources(tmp_path):
    rows = []
    for hospital, region, profile in [('A', '01', 'surgery'), ('B', '02', 'therapy')]:
        for index, day in enumerate(pd.date_range('2025-01-01', periods=30)):
            for _ in range(20 if index == 20 else 1):
                rows.append({'hospital_mo': hospital, 'region_origin_code': region, 'bed_profile': profile,
                             'registration_dt': day, 'hospitalization_dt': pd.NaT, 'refusal_dt': pd.NaT,
                             'outcome': 'unresolved', 'queue_reconstruction_eligible': True,
                             'target_eligible': False, 'wait_days': float('nan')})
    analytical = tmp_path / 'analytical.parquet'
    daily = tmp_path / 'hospital_day.parquet'
    pd.DataFrame(rows).to_parquet(analytical)
    add_historical_signals(aggregate_hospital_days(analytical)).to_parquet(daily)
    return analytical, daily


@pytest.mark.parametrize('scope', [{'hospital_mo': 'A'}, {'hospital_mo': 'A', 'bed_profile': 'surgery'}, {'region_origin_code': '01'}])
def test_one_day_view_keeps_history_and_exact_scope(sources, scope):
    result = signal_feed({**scope, 'start': '2025-01-21', 'end': '2025-01-21'}, *sources, kind='referrals')
    assert result['total'] == result['hospital_days'] == 1
    assert result['insufficient_history_days'] == 0
    alert = result['items'][0]
    assert alert['hospital'] == 'A'
    assert alert['reference_start'] == pd.Timestamp('2025-01-01')
    assert alert['reference_end'] == pd.Timestamp('2025-01-20')
    assert alert['reasons'][0]['value'] == 20
    assert alert['reasons'][0]['threshold'] == 1  # Scored day never contributes.


def test_empty_history_and_pagination(sources):
    empty = signal_feed({'bed_profile': 'unknown', 'start': '2025-01-01'}, *sources)
    assert empty['items'] == [] and empty['total'] == empty['hospital_days'] == 0
    first = signal_feed({'hospital_mo': 'A', 'end': '2025-01-15'}, *sources, kind='open_growth')
    assert first['insufficient_history_days'] == 15  # First difference is missing.
    first = signal_feed({'hospital_mo': 'A', 'end': '2025-01-15'}, *sources, kind='referrals')
    assert first['insufficient_history_days'] == 14
    result = signal_feed({}, *sources, kind='referrals', limit=1, offset=1)
    assert result['total'] == 2 and len(result['items']) == 1
    assert result['items'][0]['hospital'] == 'B'


def test_missing_daily_artifact_rebuilds_aggregate_in_memory(sources):
    analytical, daily = sources
    daily.unlink()
    result = signal_feed({'hospital_mo': 'A'}, analytical, daily, kind='referrals')
    assert result['total'] == 1
