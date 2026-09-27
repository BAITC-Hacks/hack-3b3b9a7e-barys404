"""Scoped monitoring over institutional aggregates; no individual rows leave SQL."""
from functools import lru_cache
from pathlib import Path

import pandas as pd

from backend.analytics import dashboard_data as db
from backend.analytics.aggregation import aggregate_hospital_days
from backend.analytics.anomaly_detection import add_historical_signals, HISTORY_WINDOW, MIN_HISTORY_DAYS


SIGNALS = {
    'referrals': ('Входящие направления', 'referrals', 'referrals_history_p95', 'anomaly_referrals'),
    'refusals': ('Отказы в связанной когорте', 'refusals', 'refusals_history_p95', 'anomaly_refusals'),
    'open_growth': ('Рост открытой когорты', 'open_cohort_growth', 'open_cohort_growth_history_p95', 'anomaly_open_cohort_growth'),
}


@lru_cache(maxsize=2)
def _history(path, daily_path, version, daily_version, scope):
    filters = dict(scope)
    if Path(daily_path).exists() and not filters.get('region_origin_code') and not filters.get('bed_profile'):
        columns = ['hospital_mo', 'date', 'history_days']
        for _, value, threshold, flag in SIGNALS.values():
            columns.extend([value, threshold, flag])
        where, params = ('WHERE hospital_mo = ?', [filters['hospital_mo']]) if filters.get('hospital_mo') else ('', [])
        return db.aggregate_query(daily_path, f"SELECT {','.join(columns)} FROM read_parquet(?) {where}", params)
    daily = aggregate_hospital_days(Path(path), filters)
    return add_historical_signals(daily) if not daily.empty else daily


def signal_feed(filters, path, daily_path, *, kind='all', limit=30, offset=0):
    scope = tuple(sorted((key, value) for key, value in filters.items() if key in db.DIMENSIONS))
    daily = _history(str(path), str(daily_path), db.file_version(path), db.file_version(daily_path), scope)
    visible = daily
    # Preserve earlier history when the user narrows the display period.
    if filters.get('start'):
        visible = visible.loc[visible.date >= pd.Timestamp(filters['start'])]
    if filters.get('end'):
        visible = visible.loc[visible.date <= pd.Timestamp(filters['end'])]
    rules = SIGNALS if kind == 'all' else {kind: SIGNALS[kind]}
    flags = [rule[3] for rule in rules.values()]
    alerts = visible.loc[visible[flags].any(axis=1)].sort_values(['date', 'hospital_mo'], ascending=[False, True]) if not visible.empty else visible
    items = []
    for row in alerts.iloc[offset:offset + limit].to_dict(orient='records'):
        scored = pd.Timestamp(row['date'])
        reasons = [{'kind': key, 'label': label, 'value': row[value], 'threshold': row[threshold]}
                   for key, (label, value, threshold, flag) in rules.items() if row[flag]]
        items.append({'hospital': row['hospital_mo'], 'date': scored,
                      'history_days': int(row['history_days']), 'reasons': reasons,
                      'reference_start': scored - pd.Timedelta(days=int(row['history_days'])),
                      'reference_end': scored - pd.Timedelta(days=1)})
    return {'items': items, 'total': len(alerts), 'hospital_days': len(visible),
            'insufficient_history_days': int(visible[[rule[2] for rule in rules.values()]].isna().any(axis=1).sum()) if not visible.empty else 0,
            'history_window': HISTORY_WINDOW, 'minimum_history': MIN_HISTORY_DAYS}
