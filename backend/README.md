# Бэкенд

- `api/main.py`: FastAPI и раздача `frontend/dist`.
- `auth/`: аккаунты, сессии и права доступа в PostgreSQL.
- `analytics/`: агрегированные запросы и исторические показатели.
- `data_pipeline/`: обнаружение CSV, очистка, связывание и Parquet.
- `core/`: общие настройки, безопасный SQL и атомарный JSON.

Из корня: `python -m scripts.serve` или `python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`.

API не обучает модели и не запускает подготовку в ответ на веб-запросы. Он использует готовые файлы из `data/processed/` и функции `ml/`. Пациентские строки и идентификаторы в браузер не отправляются.

Зависимости HTTP/SQL-слоя: `backend/requirements.txt`. Полный веб-runtime: `requirements-api.txt` в корне. Настройки памяти и путей: `backend/core/config.py`.
