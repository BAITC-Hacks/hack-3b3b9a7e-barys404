# Данные — исходные файлы и результаты подготовки

`raw/` содержит исходные CSV, `processed/` — очищенные Parquet, SQL-агрегаты и отчёты качества. Python-код подготовки находится в `backend/data_pipeline/`, код моделей — в `ml/`, обученные артефакты — в `models/`.

Из корня: `python -m scripts.bootstrap`. Эта команда обновляет только устаревшие данные и модели. Обычный запуск API не обрабатывает исходные CSV.

Place source CSV files in this directory or in `raw/`. They are intentionally excluded from Git because they are large project data and may contain sensitive fields.

The loader detects datasets by their CSV columns and automatically combines newly added referral/refusal parts. Expected initial files are the waiting list, referral parts, refusal parts, and treated-case aggregate described in the project README.

Generated Parquet files and quality reports are written to `processed/` and are also excluded from Git. Each teammate must obtain the authorized source files through the team's approved data-sharing channel, then run:

```powershell
python -m scripts.bootstrap
```

For temporal validation evidence, use `python -m scripts.bootstrap --validate` before presenting; check readiness with `python -m scripts.demo_check`. Inspect local source coverage with `python -m scripts.inspect_data`. Oncology and vaccination files are not model inputs. Laboratory research data (EIP) has not yet been provided; no laboratory forecast is claimed.
