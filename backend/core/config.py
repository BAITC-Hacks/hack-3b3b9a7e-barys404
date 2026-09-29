"""Shared paths and explicit, reviewable data/model policy."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MEDFLOW_DATA_DIR", ROOT / "data"))
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"
MIN_DATE = "2000-01-01"
MAX_DATE = "2026-09-11"
MIN_WAIT_DAYS = 0.0
MAX_WAIT_DAYS = 90.0
TRAIN_FRACTION = 0.8
RANDOM_SEED = 42
# Three referral source parts require more than 1 GB while a cleaned DuckDB
# table is materialized. Deployments with a smaller budget can still override
# this explicitly with MEDFLOW_MEMORY_LIMIT.
DUCKDB_MEMORY_LIMIT = os.environ.get("MEDFLOW_MEMORY_LIMIT", "4GB")
THREAD_COUNT = min(4, os.cpu_count() or 1)
MODEL_PATH = MODELS_DIR / "waiting_time_catboost.cbm"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
WAITING_MODEL_VERSION = "waiting-hybrid-temporal-v3"
ANALYTICAL_PATH = PROCESSED_DIR / "analytical.parquet"
QUALITY_PATH = PROCESSED_DIR / "data_quality_report.json"


def ensure_directories():
    for path in (DATA_DIR / "raw", PROCESSED_DIR, MODELS_DIR, ROOT / ".runtime"):
        path.mkdir(parents=True, exist_ok=True)
