"""Presentation labels only; raw artifacts retain stable machine-readable keys."""
LABELS = {
    "hospital_mo": "Стационар", "hospital": "Стационар", "organization": "Организация",
    "region_origin_code": "Регион происхождения", "bed_profile": "Профиль койки",
    "referrals": "Направления", "refusals": "Отказы", "hospitalized": "Госпитализации",
    "reconstructed_open_cohort": "Открытая когорта", "date": "Дата",
    "anomaly_referrals": "Отклонение направлений", "anomaly_refusals": "Отклонение отказов",
    "anomaly_open_cohort_growth": "Отклонение роста когорты",
    "horizon": "День горизонта", "n": "Наблюдения", "count": "Наблюдения",
    "mae": "MAE модели", "rmse": "RMSE модели", "baseline_mae": "MAE простого прогноза",
    "baseline_rmse": "RMSE простого прогноза", "seasonal_baseline_mae": "MAE того же дня прошлой недели",
    "improvement_pct": "Снижение MAE, %", "median_absolute_error": "Медиана ошибки",
    "p90_absolute_error": "P90 ошибки", "fold": "Окно", "test_start": "Начало теста",
    "test_end": "Конец теста", "train_end": "Конец обучения", "train_start": "Начало обучения",
    "train_rows": "Обучающих записей", "test_rows": "Тестовых записей",
    "purged_labels": "Поздние исходы исключены", "purged_train_labels": "Поздние исходы исключены",
    "forecast_origin": "Дата начала прогноза", "group": "Группа", "value": "Значение",
    "source_records": "Записи источника", "reported_discharges": "Указанные выписки",
    "reported_bed_days": "Указанные койко-дни",
    "waiting": "Ожидающие", "referrals_source": "Направления", "treated": "Пролеченные случаи",
}


def display_frame(frame):
    return frame.rename(columns=LABELS)
