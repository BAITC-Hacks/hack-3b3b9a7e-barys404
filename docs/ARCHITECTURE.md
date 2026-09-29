# Границы проекта

```text
frontend (React)
    └─ HTTP /api → backend/main.py → backend/modules
                                      ├─ auth + accounts → PostgreSQL
                                      ├─ analytics → data/processed
                                      ├─ predictions → ml → models + data/processed
                                      └─ briefings → агрегаты → PDF

scripts/bootstrap
    ├─ backend/data_pipeline → data/raw → data/processed
    └─ ml training/validation → models
```

Фронтенд организован по FSD: `app → pages → widgets → features → entities → shared`.
Страницы собирают экран, features владеют пользовательскими действиями, entities —
предметными справочниками; HTTP/CSRF и UI-примитивы остаются общими. Границы слоёв
и публичные API срезов проверяются при сборке. [Подробнее](../frontend/README.md).

## Ответственность

Код сгруппирован по функциональным разделам. `backend/main.py` только собирает приложение.

```text
backend/modules
    ├─ auth          вход, сессии, CSRF и разрешения
    ├─ accounts      управление аккаунтами
    ├─ analytics     обзор, справочники и сравнение
    ├─ hospitals     каталог и карточка стационара
    ├─ predictions   поток направлений и ожидание
    ├─ briefings     просмотр и выгрузка PDF
    └─ system        состояние сервиса и моделей
```

В разделах используются `router.py`, `schemas.py` и `service.py`; дополнительные
слои создаются только при необходимости. Роутеры отвечают за HTTP и разрешение на
действие, сервисы — за последовательность проверок и сборку результата. Общие
фильтры находятся в `modules/analytics`, проверка готовности данных — в `http/data.py`.
SQL хранится рядом со своим разделом. Подготовка данных находится в `data_pipeline`,
ML-расчёты — в `ml/`, генерация PDF — в `modules/briefings/pdf.py`. Зависимости между
разделами импортируются явно; сервисы не импортируют роутеры или `main.py`.

Структура опирается на [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices).

| Область | Что делает | Чего не делает |
|---|---|---|
| frontend | Представление, выбор фильтров, запросы и отображение ошибок | Не читает CSV и не обучает модель |
| backend/main.py | Сборка приложения и подключение разделов | Не содержит обработчиков запросов или расчётов |
| backend/modules | HTTP-контракты и прикладные сценарии по разделам | Не зависит от UI и не запускает обучение |
| backend/http | Общие HTTP-проверки, middleware и раздача сборки | Не обучает модели |
| backend/modules/auth | Вход, аккаунты PostgreSQL, сессии и права | `store.py` и `scope.py` не зависят от HTTP, React и ML |
| backend/modules/accounts | Каталог аккаунтов, блокировка и удаление | Не меняет права по данным из браузера |
| backend/modules/analytics | Ограниченные SQL-агрегаты и история событий | Не возвращает пациентские записи в браузер |
| backend/data_pipeline | Проверка, очистка, дневные агрегаты и исторические индикаторы | Не импортирует HTTP или UI |
| backend/core | Единые абсолютные пути и работа с артефактами | Не зависит от API/ML/UI |
| ml | Признаки, обучение, прогноз, объяснения, проверка | Не зависит от FastAPI/React |
| data | Исходные и подготовленные файлы | Не содержит рабочий Python-код |
| models | Версионированные локальные артефакты | Не содержит код модели |
| scripts | Явные команды оператора | Не выполняется при обычном импорте API |

ML использует общие настройки и обнаружение версии данных из backend; обучение вызывает отдельный data pipeline. Это один Python-проект, а не несколько сетевых микросервисов.

## Сохранённое поведение

Адрес сайта сохраняется. Бизнес-маршруты `/api/*` требуют сессии и разрешений; объектные запросы используют `hospital_id`. [Авторизация и PostgreSQL](AUTH_SETUP.md). Для запуска: `python -m scripts.serve`. Исходные CSV, Parquet, CBM и metadata остаются на прежних местах; fingerprint источников не меняется из-за перемещения кода. Переобучение не требуется.

Веб-сервер запускается через `scripts.serve` или `uvicorn backend.main:app`, подготовка и обучение — через `scripts.bootstrap`. Агрегация отдельно: `python -m backend.data_pipeline.aggregation`. Миграция аккаунтов остаётся командой `python -m scripts.auth migrate`; её SQL лежит в `backend/modules/auth/migrations/`.

Границы пакетов и пути проверяются в `tests/test_architecture.py`. GitHub Actions проверяет Python-тесты и сборку фронтенда. Все данные и генерируемые файлы игнорируются Git.
