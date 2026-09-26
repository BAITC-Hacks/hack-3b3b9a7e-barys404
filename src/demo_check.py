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
        from src.navigation import SECTIONS
        app = AppTest.from_file(config.ROOT / "app.py", default_timeout=90).run()
        from src.experience import DEMO_STEPS
        def button(label):
            return next(item for item in app.button if item.label == label)

        def review():
            return next(item for item in app.checkbox if item.label.startswith("Я проверил"))

        def pdf_enabled():
            return any(item.proto.label == "Скачать PDF-сводку" and not item.proto.disabled for item in app.get("download_button"))

        def navigate(page):
            section = next(name for name, pages in SECTIONS.items() if page in pages)
            app.sidebar.radio(key="nav_section").set_value(section).run()
            if len(SECTIONS[section]) > 1:
                app.sidebar.radio(key="nav_page").set_value(page).run()

        for page in [page for pages in SECTIONS.values() for page in pages]:
            navigate(page)
            checks[f"page:{page}"] = not app.exception and not app.error
            if app.exception or app.error:
                continue
            if page == "Waiting time prediction":
                button("Рассчитать ожидание").click().run()
                checks["waiting_prediction_and_explanation"] = (
                    not app.exception and not app.error
                    and any(item.label == "Прогноз типичного ожидания" for item in app.metric)
                    and (len(app.get("plotly_chart")) > 0 or any("Основа оценки" in item.value for item in app.info)))
            if page == "7-day load forecast":
                checks["weekly_forecast_and_explanation"] = (
                    any(item.label == "Прогноз направлений за 7 дней" for item in app.metric)
                    and len(app.get("plotly_chart")) >= 2)
            if page == "Compare & review":
                checks["review_starts_pending"] = not review().value and not pdf_enabled()
                review().check().run()
                checks["review_unlocks_pdf"] = pdf_enabled() and not app.exception
                app.select_slider(key="comparison_minimum").set_value(300).run()
                checks["changed_sample_threshold_requires_new_review"] = not review().value and not pdf_enabled() and not app.exception
                review().check().run()
                app.radio(key="comparison_mode").set_value("Регионы происхождения").run()
                checks["changed_comparison_requires_new_review"] = not review().value and not pdf_enabled() and not app.exception
            checks["demo_preparation_disabled"] = button("Подготовить / обновить данные").disabled
        # Follow callbacks exactly as in a presentation; do not fake model predictions.
        button("Показать пример").click().run()
        hospital = app.session_state["tour_hospital"]
        checks["demo_profile_observed"] = bool(app.session_state["example_profile"])
        for index, (page, _, _) in enumerate(DEMO_STEPS):
            checks[f"guided_step:{index + 1}"] = (
                not app.exception and not app.error and app.session_state["nav_page"] == page
                and app.session_state["active_hospital"] == hospital)
            if page == "Compare & review":
                checks[f"guided_comparison:{index + 1}"] = hospital in app.multiselect(key="comparison_groups_hospital_mo").value
            if page == "Waiting time prediction":
                button("Рассчитать ожидание").click().run()
                checks["guided_prediction"] = not app.exception and any(item.label == "Прогноз типичного ожидания" for item in app.metric)
            if index < len(DEMO_STEPS) - 1:
                button("Следующий шаг").click().run()
        review().check().run()
        checks["guided_pdf_ready"] = pdf_enabled() and not app.exception
        button("Завершить пример").click().run()
        checks["guided_demo_ends"] = "tour_step" not in app.session_state
        # Shared filters survive a trip through a model page, whose input scope is different.
        from datetime import timedelta
        from src.dashboard_data import dimensions as data_dimensions
        # Pick an interval from the actual data bounds, so this preflight also works on later sources.
        dimensions = data_dimensions()
        import pandas as pd
        low, high = (pd.Timestamp(dimensions["dates"][k]).date() for k in ("first", "last"))
        chosen_period = (low, min(high, low + timedelta(days=20)))
        app.sidebar.date_input(key="cohort_period").set_value(chosen_period).run()
        navigate("7-day load forecast")
        navigate("Compare & review")
        checks["shared_period_survives_navigation"] = tuple(app.sidebar.date_input(key="cohort_period").value) == chosen_period
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
