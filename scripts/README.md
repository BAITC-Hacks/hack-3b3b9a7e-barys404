# Команды обслуживания

Выполняются из корня проекта, не через прямой запуск файла:

- `python -m scripts.serve`: только HTTP-сервер, без подготовки/обучения.
- `python -m scripts.bootstrap`: подготовить изменённые данные, обучить только устаревшие модели.
- `python -m scripts.bootstrap --retrain`: явно переобучить обе модели.
- `python -m scripts.bootstrap --validate`: обновить временную проверку.
- `python -m scripts.demo_check`: read-only проверка готовности.
- `python -m scripts.demo_check --ui`: дополнительно проверить прежний Streamlit.
- `python -m scripts.inspect_data`: SQL-проверка исходной выгрузки.
- `scripts/run.ps1`: прежний Windows-сценарий Streamlit; корневой `run.ps1` делегирует ему.

Команды подготовки тяжёлые; обычный запуск сайта их не вызывает.
