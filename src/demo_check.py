"""Read-only local preflight. Run python -m src.demo_check --ui before presenting."""
import argparse
import json

from src import config
from src.predict import model_status
from src.load_forecast import forecast_status
from src.validation import validation_status
from src.utils import read_json


def check_demo(include_ui=False):
    report = read_json(config.QUALITY_PATH)
    checks = {
        "preparation_complete": bool(report.get("pipeline_complete")),
        "referral_parts_complete": bool(report.get("coverage", {}).get("referrals", {}).get("complete")),
        "refusal_parts_complete": bool(report.get("coverage", {}).get("refusals", {}).get("complete")),
        "waiting_model_current": model_status()["available"],
        "forecast_model_current": forecast_status(report)["available"],
        "temporal_validation_current": validation_status()["available"],
    }
    if include_ui and all(checks.values()):
        from streamlit.testing.v1 import AppTest
        from src.ui import PAGES
        app = AppTest.from_file(config.ROOT / "app.py", default_timeout=90).run()
        for page in PAGES:
            app.sidebar.radio[0].set_value(page).run()
            checks[f"page:{page}"] = not app.exception and not app.error
            if app.exception or app.error:
                continue
            if page == "Waiting time prediction":
                next(item for item in app.button if item.label == "Estimate waiting time").click().run()
                checks["waiting_prediction_and_explanation"] = (
                    not app.exception and not app.error
                    and any(item.label == "Predicted typical waiting time" for item in app.metric)
                    and len(app.get("plotly_chart")) > 0)
            if page == "7-day load forecast":
                checks["weekly_forecast_and_explanation"] = (
                    any(item.label == "Predicted referrals · next 7 days" for item in app.metric)
                    and len(app.get("plotly_chart")) >= 2)
            if page == "Compare & review":
                check = next(item for item in app.checkbox if item.label.startswith("I checked"))
                checks["review_starts_pending"] = not check.value
                check.check().run()
                next(item for item in app.select_slider if item.label == "Minimum referrals per group").set_value(300).run()
                check = next(item for item in app.checkbox if item.label.startswith("I checked"))
                checks["changed_sample_threshold_requires_new_review"] = not check.value and not app.exception
                check.check().run()
                next(item for item in app.radio if item.label == "Compare").set_value("Origin regions").run()
                check = next(item for item in app.checkbox if item.label.startswith("I checked"))
                checks["changed_comparison_requires_new_review"] = not check.value and not app.exception
            checks["demo_preparation_disabled"] = next(item for item in app.button if item.label == "Prepare / refresh data").disabled
    return {"ready": all(checks.values()), "checks": checks,
            "historical_period": {"start": str(report.get("summary", {}).get("registration_min")),
                                  "end": str(report.get("summary", {}).get("registration_max"))},
            "scope": "Functional Streamlit checks; not a browser screenshot review or external clinical validation."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui", action="store_true")
    args = parser.parse_args()
    result = check_demo(include_ui=args.ui)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)
