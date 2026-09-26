# Артефакты моделей — не исходный код

Генерируются командами обучения из `ml/` и остаются локальными:

- `waiting_time_catboost.cbm` + `model_metadata.json`: модель ожидания и обучающие агрегаты v3.
- `referral_load_7day_catboost.cbm` + `referral_load_7day_metadata.json`: поток направлений.
- `referral_load_7day_catboost.validation.parquet`: проверочные агрегаты потока.
- `temporal_validation.json`: проверка на нескольких периодах.

Не редактируйте и не удаляйте эти файлы для очистки проекта: без них прогнозы станут недоступны. Обновление: `python -m scripts.bootstrap`; принудительное переобучение: `python -m scripts.bootstrap --retrain`.

Файлы моделей и отчёты исключены из Git. Код и инструкции: [ml/README.md](../ml/README.md).
