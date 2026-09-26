"""Prepare changed local data and train only when no matching model exists."""
import logging
import argparse
from backend.data_pipeline.preprocessing import run_pipeline
from ml.predict import model_status
from ml.train_waiting_model import train_model
from ml.load_forecast import forecast_status, train_load_forecast

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrain", action="store_true", help="Retrain both models on the prepared data")
    parser.add_argument("--validate", action="store_true", help="Compute missing or stale expanding-window evidence")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = run_pipeline()
    if args.retrain or not model_status()["available"]:
        train_model()
    else:
        logging.info("Prepared data and trained model are up to date.")
    if args.retrain or not forecast_status(report)["available"]:
        train_load_forecast()
    else:
        logging.info("Seven-day referral-load forecast is up to date.")
    if args.validate:
        from ml.validation import run_validation
        run_validation()

if __name__ == "__main__":
    main()
