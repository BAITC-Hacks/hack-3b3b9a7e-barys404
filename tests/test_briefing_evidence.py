"""Versioned model metrics included in reviewed PDF reports."""
import json
import pytest
from backend.api import main as api


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
    return metadata


@pytest.mark.parametrize('available', [True, False])
def test_briefing_evidence_shows_only_current_versioned_metrics(evidence_files, monkeypatch, available):
    monkeypatch.setattr(api, 'model_status', lambda: {'available': available, 'stale': not available, 'reason': 'Status'})
    result = {'waiting': api.model_evidence(api.METADATA_PATH, api.model_status),
              'flow': api.model_evidence(api.FORECAST_METADATA_PATH, api.forecast_status)}
    assert result['waiting']['status']['available'] is available
    assert result['waiting']['model_version'] == 'test-v3'
    assert result['waiting']['test_period'] == {'start': '2025-03-14', 'end': '2025-03-31'}
    assert result['waiting']['metrics'] == (evidence_files['metrics'] if available else None)
    assert result['flow']['metrics']['mae'] == 5.2
    serialized = json.dumps(result)
    assert 'calibration' not in serialized and 'rows' not in serialized and 'private_learned_values' not in serialized


def test_numeric_forecast_version_has_same_string_contract_as_waiting(evidence_files):
    evidence_files['model_version'] = 2
    api.FORECAST_METADATA_PATH.write_text(json.dumps(evidence_files), encoding='utf8')
    assert api.model_evidence(api.FORECAST_METADATA_PATH, api.forecast_status)['model_version'] == '2'


@pytest.mark.parametrize('failure', ['missing', 'invalid_json', 'invalid_shape', 'nan', 'missing_period', 'read_error'])
def test_briefing_evidence_fails_closed_without_hiding_other_model(evidence_files, monkeypatch, failure):
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
    result = {'waiting': api.model_evidence(api.METADATA_PATH, api.model_status),
              'flow': api.model_evidence(api.FORECAST_METADATA_PATH, api.forecast_status)}
    assert result['waiting']['status']['available'] is False
    assert result['waiting']['metrics'] is None
    assert result['flow']['status']['available'] is True
