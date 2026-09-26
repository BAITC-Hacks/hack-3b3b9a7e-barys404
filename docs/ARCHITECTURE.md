# Границы проекта

```text
frontend (React)
    └─ HTTP /api → backend/api
                       ├─ backend/auth → PostgreSQL (аккаунты, сессии, права)
                       ├─ backend/analytics → data/processed
                       └─ ml inference → models + data/processed

scripts/bootstrap
    ├─ backend/data_pipeline → data/raw → data/processed
    └─ ml training/validation → models

backend/legacy (Streamlit)
    └─ те же analytics и ml; не зависимость основного API
```

## Ответственность

| Область | Что делает | Чего не делает |
|---|---|---|
| frontend | Представление, выбор фильтров, запросы и отображение ошибок | Не читает CSV и не обучает модель |
| backend/api | HTTP-контракт и валидация, раздача сборки | Не зависит от Streamlit и не запускает обучение |
| backend/auth | Аккаунты PostgreSQL, сессии и права | Не зависит от HTTP, React и ML |
| backend/analytics | Ограниченные SQL-агрегаты и история событий | Не возвращает пациентские записи в браузер |
| backend/data_pipeline | Проверка и подготовка исходных данных | Не импортирует UI |
| backend/core | Единые абсолютные пути и работа с артефактами | Не зависит от API/ML/UI |
| ml | Признаки, обучение, прогноз, объяснения, проверка | Не зависит от FastAPI/Streamlit/React |
| data | Исходные и подготовленные файлы | Не содержит рабочий Python-код |
| models | Версионированные локальные артефакты | Не содержит код модели |
| scripts | Явные команды оператора | Не выполняется при обычном импорте API |

ML использует общие настройки и обнаружение версии данных из backend; обучение вызывает отдельный data pipeline. Это один Python-проект, а не несколько сетевых микросервисов.

## Сохранённое поведение

Адрес сайта сохраняется. Бизнес-маршруты `/api/*` требуют сессии и разрешений; объектные запросы используют `hospital_id`. [Авторизация и PostgreSQL](AUTH_SETUP.md). Для запуска: `python -m scripts.serve`. Исходные CSV, Parquet, CBM и metadata остаются на прежних местах; fingerprint источников не меняется из-за перемещения кода. Переобучение не требуется.

Корневые `app.py` и `run.ps1` сохранены как совместимые точки входа старого Streamlit. Внутренние команды `src.*` заменены на `ml.*`, `backend.data_pipeline.*` и `scripts.*`; инструкции и тесты обновлены.

Границы пакетов и пути проверяются в `tests/test_architecture.py`. GitHub Actions проверяет Python-тесты и сборку фронтенда. Все данные и генерируемые файлы игнорируются Git.
