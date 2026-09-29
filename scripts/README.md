# Команды обслуживания

Выполняются из корня проекта, не через прямой запуск файла:

- `python -m scripts.serve`: только HTTP-сервер, без подготовки/обучения.
- `python -m scripts.bootstrap`: подготовить изменённые данные, обучить только устаревшие модели.
- `python -m scripts.bootstrap --retrain`: явно переобучить обе модели.
- `python -m scripts.bootstrap --validate`: обновить временную проверку.
- `python -m scripts.demo_check`: read-only проверка готовности.
- `python -m scripts.inspect_data`: SQL-проверка исходной выгрузки.
- `python -m scripts.build_hospital_map /path/to/kazakhstan.osm.pbf`: сопоставить организации с объектами OpenStreetMap по названию и региону.

Команды подготовки тяжёлые; обычный запуск сайта их не вызывает.

## Координаты стационаров

Исходник для карты — [выгрузка Kazakhstan от Geofabrik](https://download.geofabrik.de/asia/kazakhstan.html), данные OpenStreetMap. Для обновления установите в рабочее окружение `osmium`, `rapidfuzz`, `shapely` и зависимости проекта, скачайте `.osm.pbf` и запустите команду выше. Скрипт использует `data/processed/hospital_day.parquet`, записывает принятые совпадения в `frontend/src/pages/welcome/model/hospitalCoordinates.json` и оставляет спорные совпадения для проверки в `data/processed/hospital_map_review.json`.

На снимке OSM от 28 сентября 2026 года автоматически принято 66 из 1 382 организаций. Координаты взяты из объектов OSM, а не вычислены по центрам городов. Отсутствующие организации не отображаются. Совпадение по названию и региону не заменяет ручную проверку адреса перед применением карты для реальной навигации.
