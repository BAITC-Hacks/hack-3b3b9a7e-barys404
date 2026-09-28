"""Read-only data/model preflight. Run python -m scripts.demo_check before presenting."""
import argparse
import json

from backend.core import config
from backend.core.utils import read_json
from ml.predict import model_status
from ml.load_forecast import forecast_status
from ml.validation import validation_status


def check_demo():
    report = read_json(config.QUALITY_PATH)
    checks = {
        "preparation_complete": bool(report.get("pipeline_complete")),
        "referral_parts_complete": bool(report.get("coverage", {}).get("referrals", {}).get("complete")),
        "refusal_parts_complete": bool(report.get("coverage", {}).get("refusals", {}).get("complete")),
        "waiting_model_current": model_status()["available"],
        "forecast_model_current": forecast_status(report)["available"],
        "temporal_validation_current": validation_status()["available"],
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "historical_period": {
            "start": str(report.get("summary", {}).get("registration_min")),
            "end": str(report.get("summary", {}).get("registration_max")),
        },
        "scope": "Data/model artifact readiness only; no browser UI or external clinical validation.",
    }


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = check_demo()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)
