# MedFlow AI

GovTech MVP для анализа госпитальных направлений и исторических оценок ожидания. Основной интерфейс — React; данные и прогнозы отдаёт FastAPI. Это аналитический инструмент, не система назначения лечения или даты госпитализации.

В кабинете доступны обзор и сравнение стационаров, гибридная оценка ожидания, прогноз потока на 7 дней, PDF-сводки для обсуждения. Из карточки или сравнения можно подготовить PDF-сводку после просмотра и подтверждения аналитиком. Права сотрудника ограничены своей больницей. [Страницы и рабочий сценарий](docs/WEB_INTERFACE.md).

## Структура

```text
backend/                  Python-бэкенд
  api/                    FastAPI: HTTP-маршруты, валидация, раздача фронтенда
  analytics/              SQL-агрегаты, исторические индикаторы, PDF-сводки
  data_pipeline/          Чтение CSV, проверки качества, подготовка Parquet
  core/                   Общие пути, настройки и работа с артефактами
  legacy/                 Сохранённый Streamlit, отдельно от основного веб-API
frontend/                 React + TypeScript + Vite: интерфейс и стили
ml/                       Признаки, обучение, прогнозы, объяснения, валидация
  notebooks/              Исследовательский ноутбук с агрегатами
data/
  raw/                    Исходные CSV — только локально
  processed/              Подготовленные Parquet и отчёты — только локально
models/                   Обученные CBM и metadata — только локально
scripts/                  Подготовка, запуск, проверка готовности
tests/                    Тесты логики, API, ML и границ архитектуры
docs/                     Архитектура, результаты проверок и документация
  presentations/          Презентация и офлайн-слайды
  legacy/                 Сценарии и инструкции прежнего Streamlit-интерфейса
```

Папки `data/` и `models/` содержат файлы, не Python-код. Подробные границы модулей: [архитектура](docs/ARCHITECTURE.md).

## Запуск веб-версии

Из корня проекта, Python 3.12+ и Node.js 22+:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-api.txt
npm --prefix frontend ci
npm --prefix frontend run build
# Настройте PostgreSQL и MEDFLOW_DATABASE_URL в .env (docs/AUTH_SETUP.md).
.venv/bin/python -m scripts.auth migrate
.venv/bin/python -m scripts.auth seed-demo
.venv/bin/python -m scripts.serve
```

Откройте http://127.0.0.1:8000: посетители видят публичную страницу, сотрудники входят в кабинет. Госорган видит все больницы, сотрудник — только закреплённую. Тестовые реквизиты находятся в `.runtime/demo-accounts.md` вне Git. API-документация `/docs` доступна только локально.

Пользователи и сессии хранятся в PostgreSQL; аналитика — в Parquet/DuckDB. [Настройка базы и аккаунтов](docs/AUTH_SETUP.md).
На Windows используйте `.venv\Scripts\python.exe` вместо `.venv/bin/python`.

Если данных и моделей ещё нет, получите разрешённую выгрузку, положите CSV в `data/raw/` и один раз выполните:

```bash
.venv/bin/python -m scripts.bootstrap
```

Подготовка больших CSV и обучение могут занять время. Обычный запуск сайта их не повторяет. Данные и модели не скачиваются автоматически и не публикуются в Git.

Разработка фронтенда: запустите API, затем `npm --prefix frontend run dev`; Vite на http://127.0.0.1:5173 проксирует `/api` на порт 8000.

## Проверки и обслуживание

```bash
# Полное окружение: тесты, PDF и прежний Streamlit
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build

# Проверить готовность без переобучения
.venv/bin/python -m scripts.demo_check

# Явное обновление данных / моделей / временной валидации
.venv/bin/python -m scripts.bootstrap --validate
.venv/bin/python -m ml.train_waiting_model
.venv/bin/python -m ml.load_forecast
.venv/bin/python -m ml.validation
```

`requirements-lock.txt` — полный фиксированный Python-набор для CI/демо. `requirements-api.txt` собирает зависимости только бэкенда и ML; Streamlit для веб-версии не требуется.

Прежний интерфейс сохранён только для локального оператора, не использует RBAC и не должен публиковаться рядом с защищённой платформой: `streamlit run app.py` (порт 8501). Корневые `app.py` и `run.ps1` — небольшие совместимые точки входа, не второй набор бизнес-логики.

## Данные и прогнозы

История регистрации: январь–март 2025. Семидневный прогноз относится к 1–7 апреля 2025, не к текущей очереди. Ожидание — оценка полного срока среди наблюдённых завершённых госпитализаций; незавершённые направления создают смещение отбора.

Ожидание v3 использует обучающие медианы стационара/профиля при достаточном числе случаев, а CatBoost — для редкой истории. Метод и основание показаны явно. Финальный временной тест: MAE 5,2709 дня на 86 341 случае; ошибки отдельных групп могут быть значительно выше.

- [Как пользоваться веб-интерфейсом](docs/WEB_INTERFACE.md)
- [ML: обучение и артефакты](ml/README.md)
- [Источники и подготовленные данные](data/README.md)
- [Проверка по периодам и ограничения](docs/VALIDATION_RESULTS.md)
- [Подробное описание проекта и методологии](docs/PROJECT_DETAILS.md)
- [Презентация](docs/presentations/MedFlowAI_Final_2026-10-02.pptx)
- [Офлайн-слайды](docs/presentations/MedFlowAI_Offline_Slides.html)
