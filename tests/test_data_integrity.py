"""Regression checks for truthful aggregates, period coverage and model evidence."""
from datetime import date
from functools import partial
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.analytics import dashboard_data as db
from backend.api import main as api
from backend.api.auth import current_user
from backend.auth.store import Principal


def save_cohort(tmp_path, eligible=10):
    # Many referrals must not be mistaken for enough eligible waiting labels.
    outcomes = ['hospitalized'] * eligible + ['unresolved'] * 30 + ['refused', 'conflicting', 'invalid_outcome']
    rows = pd.DataFrame({
        'hospital_mo': 'H', 'region_origin_code': '01', 'bed_profile': 'P',
        'registration_dt': pd.Timestamp('2025-03-20'),
        'hospitalization_dt': pd.Timestamp('2025-03-24'), 'refusal_dt': pd.NaT,
        'outcome': outcomes, 'target_eligible': [True] * eligible + [False] * 33,
        'wait_days': [4.] * eligible + [None] * 33,
    })
    path = tmp_path / 'cohort.parquet'
    rows.to_parquet(path)
    return path


@pytest.mark.parametrize('eligible', [0, 1, 9, 10])
def test_waiting_statistics_use_eligible_denominator_consistently(tmp_path, eligible):
    path = save_cohort(tmp_path, eligible)
    overview = db.overview({}, path)
    directory = db.hospital_directory({}, path).iloc[0]
    comparison = db.compare_groups({}, minimum=10, path=path).iloc[0]
    profile = db.hospital_profiles({}, path).iloc[0]
    _, histogram, hospitals = db.historical_charts({}, path)
    assert overview['eligible'] == eligible
    assert overview['referrals'] == eligible + 33
    values = [overview['mean_wait'], overview['median_wait'], directory.median_wait_days,
              directory.p90_wait_days, comparison.median_wait_days, comparison.p90_wait_days,
              profile.median_wait, hospitals.iloc[0].mean_wait_days]
    if eligible == 10:
        assert all(value == 4. for value in values)
    else:
        assert all(pd.isna(value) for value in values)
    assert histogram.records.sum() == (10 if eligible == 10 else 0)
    # The denominator for refusals is known outcomes, not eligible waiting labels.
    if eligible < 9:
        assert pd.isna(directory.refusal_share_pct)
    else:
        assert directory.refusal_share_pct == pytest.approx(100 / (eligible + 1))


def test_overview_http_accounts_for_all_outcomes_and_suppresses_single_wait(tmp_path, monkeypatch):
    path = save_cohort(tmp_path, eligible=1)
    monkeypatch.setattr(api, 'ready', lambda: {})
    monkeypatch.setattr(api, 'ANALYTICAL_PATH', path)
    for name in ('overview', 'recent_activity'):
        monkeypatch.setattr(db, name, partial(getattr(db, name), path=path))
    user = Principal('review', 'review', 'Review', 'government_analyst', None, None)
    monkeypatch.setitem(api.app.dependency_overrides, current_user, lambda: user)
    with TestClient(api.app) as client:
        response = client.get('/api/overview')
    assert response.status_code == 200
    payload = response.json()
    stats = payload['stats']
    assert sum(stats[key] for key in ('hospitalized', 'refused', 'unresolved', 'conflicting', 'invalid_outcome')) == stats['referrals']
    assert stats['conflicting'] + stats['invalid_outcome'] == 2
    assert stats['mean_wait'] is None and stats['median_wait'] is None
    assert payload['metric_minimum'] == 10
    assert payload['trend'][0]['days_in_period'] == 1
    assert payload['trend'][0]['partial_week'] is True


@pytest.fixture
def weekly_source(tmp_path):
    rows = pd.DataFrame({
        'hospital_mo': ['H'] * 3 + ['Other'] * 2,
        'region_origin_code': ['01'] * 3 + ['02'] * 2,
        'bed_profile': ['P'] * 5,
        'registration_dt': pd.to_datetime(['2025-03-19', '2025-03-24', '2025-03-31', '2025-01-01', '2025-04-30']),
    })
    path = tmp_path / 'weekly.parquet'
    rows.to_parquet(path)
    return path


def test_week_coverage_uses_selected_hospital_and_marks_both_edges(weekly_source):
    result = db.weekly_trend({'hospital_mo': 'H'}, weekly_source)
    assert result.week.dt.date.tolist() == [date(2025, 3, 17), date(2025, 3, 24), date(2025, 3, 31)]
    assert result.days_in_period.tolist() == [5, 7, 1]
    assert result.partial_week.tolist() == [True, False, True]
    assert result.referrals.tolist() == [1, 1, 1]
    assert result.period_start.dt.date.iloc[0] == date(2025, 3, 19)
    assert result.period_end.dt.date.iloc[-1] == date(2025, 3, 31)


def test_changing_dates_recomputes_week_coverage_and_keeps_interior_zero(weekly_source):
    result = db.weekly_trend({'hospital_mo': 'H', 'start': '2025-03-25', 'end': '2025-03-31'}, weekly_source)
    assert result.days_in_period.tolist() == [6, 1]
    assert result.referrals.tolist() == [0, 1]
    assert result.partial_week.all()
    assert db.weekly_trend({'hospital_mo': 'unknown'}, weekly_source).empty
    assert db.weekly_trend({'hospital_mo': 'H', 'start': '2025-04-01'}, weekly_source).empty
    extended = db.weekly_trend({'hospital_mo': 'Other'}, weekly_source)
    assert extended.referrals.sum() == 2
    assert not extended.loc[extended.week.eq(pd.Timestamp('2025-03-24')), 'partial_week'].item()
    assert extended.loc[extended.week.eq(pd.Timestamp('2025-03-24')), 'referrals'].item() == 0


@pytest.fixture
def evidence_files(tmp_path, monkeypatch):
    metadata = {'model_version': 'test-v3', 'metrics': {'mae': 5.2, 'baseline_mae': 7.1, 'rmse': 12.},
                'test_period': {'start': '2025-03-14T01:00:00', 'end': '2025-03-31T23:00:00'},
                'calibration': {'private_learned_values': 'never expose'}, 'rows': {'train': 100}}
    for attribute, name in [('METADATA_PATH', 'waiting.json'), ('FORECAST_METADATA_PATH', 'flow.json')]:
        path = tmp_path / name
        path.write_text(json.dumps(metadata), encoding='utf8')
        monkeypatch.setattr(api, attribute, path)
    monkeypatch.setattr(api, 'model_status', lambda: {'available': True, 'stale': False, 'reason': 'Ready'})
    monkeypatch.setattr(api, 'forecast_status', lambda: {'available': True, 'stale': False, 'reason': 'Ready'})
    user = Principal('h', 'h', 'Hospital', 'hospital_analyst', 'one', 'H')
    monkeypatch.setitem(api.app.dependency_overrides, current_user, lambda: user)
    return metadata


@pytest.mark.parametrize('available', [True, False])
def test_methodology_http_shows_only_current_versioned_metrics(evidence_files, monkeypatch, available):
    monkeypatch.setattr(api, 'model_status', lambda: {'available': available, 'stale': not available, 'reason': 'Status'})
    with TestClient(api.app) as client:
        response = client.get('/api/methodology')
    assert response.status_code == 200
    result = response.json()
    assert result['waiting']['status']['available'] is available
    assert result['waiting']['model_version'] == 'test-v3'
    assert result['waiting']['test_period'] == {'start': '2025-03-14', 'end': '2025-03-31'}
    assert result['waiting']['metrics'] == (evidence_files['metrics'] if available else None)
    assert result['waiting_mae'] == (5.2 if available else None)
    assert result['flow']['metrics']['mae'] == 5.2
    assert 'calibration' not in response.text and 'rows' not in response.text and 'private_learned_values' not in response.text


def test_numeric_forecast_version_has_same_string_contract_as_waiting(evidence_files):
    evidence_files['model_version'] = 2
    api.FORECAST_METADATA_PATH.write_text(json.dumps(evidence_files), encoding='utf8')
    assert api.methodology()['flow']['model_version'] == '2'


@pytest.mark.parametrize('failure', ['missing', 'invalid_json', 'invalid_shape', 'nan', 'missing_period', 'read_error'])
def test_methodology_fails_closed_without_hiding_other_model(evidence_files, monkeypatch, failure):
    path = api.METADATA_PATH
    metadata = evidence_files
    if failure == 'missing':
        path.unlink()
    elif failure == 'invalid_json':
        path.write_text('{broken', encoding='utf8')
    elif failure == 'invalid_shape':
        path.write_text('[]', encoding='utf8')
    elif failure == 'read_error':
        def broken_status():
            raise ValueError('Broken source report')
        monkeypatch.setattr(api, 'model_status', broken_status)
    else:
        if failure == 'nan':
            metadata['metrics']['mae'] = float('nan')
        else:
            metadata.pop('test_period')
        path.write_text(json.dumps(metadata), encoding='utf8')
    with TestClient(api.app) as client:
        response = client.get('/api/methodology')
    assert response.status_code == 200
    result = response.json()
    assert result['waiting']['status']['available'] is False
    assert result['waiting']['metrics'] is None and result['waiting_mae'] is None
    assert result['flow']['status']['available'] is True
