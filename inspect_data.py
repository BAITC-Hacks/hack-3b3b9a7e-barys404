"""Run with: python inspect_data.py. Full-data, memory-bounded quality inspection."""
import logging
from src.data_quality import inspect_data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    inspect_data()
