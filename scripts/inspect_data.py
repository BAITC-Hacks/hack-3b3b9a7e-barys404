"""Run with: python -m scripts.inspect_data. Full-data, memory-bounded quality inspection."""
import logging
from backend.data_pipeline.data_quality import inspect_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    inspect_data()
