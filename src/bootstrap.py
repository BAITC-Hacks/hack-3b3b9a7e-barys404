"""Prepare changed local data and train only when no matching model exists."""
import logging
from .preprocessing import run_pipeline
from .predict import model_status
from .train_waiting_model import train_model

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline()
    if not model_status()["available"]:
        train_model()
    else:
        logging.info("Prepared data and trained model are up to date.")

if __name__ == "__main__":
    main()
