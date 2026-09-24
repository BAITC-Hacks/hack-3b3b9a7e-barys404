"""Presentation layer for the historical MedFlow AI decision-support prototype."""
from datetime import date
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import ANALYTICAL_PATH, METADATA_PATH, MODEL_PATH, PROCESSED_DIR, QUALITY_PATH
from src import dashboard_data as db


COLORS = ["#087F8C", "#3969B3", "#E5A24A", "#9073BA"]
PAGES = ["Overview", "Compare & review", "Hospital explorer", "Waiting time prediction", "Model performance", "7-day load forecast", "Validation evidence", "Pressure & anomalies", "Data quality"]


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@st.cache_data(show_spinner=False)
def cached_dimensions(version):
    return db.dimensions()


@st.cache_data(show_spinner=False)
def cached_overview(version, filters):
    return db.overview(filters)


@st.cache_data(show_spinner=False)
def cached_charts(version, filters):
    return db.historical_charts(filters)


def count(value):
    return f"{int(value):,}" if pd.notna(value) else "—"


def number(value, suffix=""):
    return f"{float(value):,.2f}{suffix}" if value is not None and pd.notna(value) else "—"


def chart(fig, height=320):
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=20, b=12), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", color="#40566B", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        colorway=COLORS, hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E6EDF4", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def theme():
    st.markdown("""<style>
    .block-container {padding-top: 2.0rem; padding-bottom: 2rem; max-width: 1540px;}
    [data-testid="stSidebar"] {border-right: 1px solid #e3eaf1;}
    [data-testid="stMetric"] {background:white; border:1px solid #e3eaf1; border-radius:12px; padding:18px 16px; min-height:122px;}
    [data-testid="stMetricLabel"] {font-size:12px; color:#60758a;}
    [data-testid="stMetricValue"] {font-size:27px; font-weight:650; color:#153247;}
    h1 {font-size:2.25rem !important; letter-spacing:-0.06rem; font-weight:750 !important;}
    h2 {font-size:1.4rem !important; letter-spacing:-0.02rem;}
    h3 {font-size:1.12rem !important;}
    .eyebrow {font-size:11px; letter-spacing:2px; color:#087f8c; font-weight:750; margin-bottom:8px;}
    .brand {font-size:24px; font-weight:800; letter-spacing:-0.6px; color:#153247; margin-bottom:3px;}
    .brand span {color:#087f8c;}
    .brand-sub {font-size:11px; color:#74859a; letter-spacing:1px; margin-bottom:24px;}
    .intro {font-size:15px; color:#60758a; margin-top:-10px; margin-bottom:22px;}
    .tag {display:inline-block; background:#e7f4f3; color:#086872; padding:5px 10px; border-radius:16px; font-size:11px; font-weight:650;}
    [data-testid="stDataFrame"] {border-radius:10px;}
    </style>""", unsafe_allow_html=True)


def title(kicker, heading, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(heading)
    st.markdown(f'<div class="intro">{subtitle}</div>', unsafe_allow_html=True)


def coverage_note(report):
    pieces = []
    for key, label in [("referrals", "Referrals"), ("refusals", "Refusal feed")]:
        info = report.get("coverage", {}).get(key, {})
        available = len(info.get("available_parts", []))
        expected = info.get("expected_parts")
        if expected:
            pieces.append(f"{label}: {available}/{expected} parts")
    return " · ".join(pieces)


def sidebar(report, ready):
    with st.sidebar:
        st.markdown('<div class="brand">MEDFLOW <span>AI</span></div><div class="brand-sub">HOSPITAL LOAD INTELLIGENCE</div>', unsafe_allow_html=True)
        page = st.radio("Workspace", PAGES, label_visibility="collapsed")
        st.divider()
        st.caption("GOVTECH CAMP · KAZAKHSTAN")
        st.markdown("**Historical data · MVP**")
        st.toggle("Demo mode", value=ready, key="demo_mode", help="Disables preparation and model-training buttons during the live demo.")
        note = coverage_note(report)
        if note:
            st.caption(note)
        filters = {}
        if ready and page in {"Overview", "Hospital explorer"}:
            st.divider()
            st.markdown("**Explore the referral cohort**")
            dimensions = cached_dimensions(db.file_version(ANALYTICAL_PATH))
            for field, label in [("region_origin_code", "Origin region"), ("hospital_mo", "Hospital"), ("bed_profile", "Bed profile")]:
                choice = st.selectbox(label, [None, *dimensions[field]], format_func=lambda value: "All" if value is None else value, key=f"filter_{field}")
                filters[field] = choice
            start, end = dimensions["dates"]["first"], dimensions["dates"]["last"]
            if pd.notna(start) and pd.notna(end):
                selected = st.date_input("Registration dates", (pd.Timestamp(start).date(), pd.Timestamp(end).date()), min_value=pd.Timestamp(start).date(), max_value=pd.Timestamp(end).date())
                if isinstance(selected, (tuple, list)) and len(selected) == 2:
                    filters["start"], filters["end"] = selected
                elif isinstance(selected, (tuple, list)) and len(selected) == 1:
                    filters["start"] = filters["end"] = selected[0]
            st.caption("Filters select referrals registered in this interval. Outcomes may occur later.")
        st.divider()
        refresh = st.button("Prepare / refresh data", width="stretch", disabled=st.session_state.get("demo_mode", False))
        st.caption("Scans available CSV parts and rebuilds changed data. Model training is a separate step.")
    return page, filters, refresh


def source_status(report):
    try:
        from src.data_loader import discover_files, source_fingerprint
        discovered = discover_files()
        has_sources = any(discovered.values())
        changed = bool(report.get("source_fingerprint")) and report["source_fingerprint"] != source_fingerprint(discovered)
        return has_sources, changed
    except (ImportError, OSError, ValueError):
        return False, False


def prepare_data():
    try:
        from src.preprocessing import run_pipeline
        with st.spinner("Reading source parts, checking quality and preparing analytical data…"):
            run_pipeline(force=False)
        st.cache_data.clear()
        st.rerun()
    except Exception as exc:
        st.error(f"Data preparation could not finish: {type(exc).__name__}. See the local terminal for details.")
        import logging
        logging.getLogger(__name__).exception("Dashboard data preparation failed")


def empty_state():
    title("GOVTECH CASE 1", "Your data, ready for decisions.", "MedFlow AI · Hospital load and waiting-time intelligence for Kazakhstan.")
    st.info("Prepare the available CSV files to calculate real statistics and unlock the dashboard.")
    st.markdown("Place the source CSV files in `data/` or `data/raw/`, then select **Prepare / refresh data**. All available referral and refusal parts are discovered automatically.")
    st.code("python -m src.preprocessing\npython -m src.train_waiting_model\nstreamlit run app.py", language="bash")
    st.caption("No sample metrics or synthetic predictions are displayed. This local application supports operational analysis; it does not provide medical advice.")


def overview_page(report, filters, explorer=False):
    title("HISTORICAL REFERRAL COHORT", "Hospital explorer" if explorer else "Care access, in perspective.", "Explore observed referrals, hospitalization outcomes and waiting times across available records.")
    version = db.file_version(ANALYTICAL_PATH)
    stats = cached_overview(version, filters)
    metrics = [("Total referrals", count(stats["referrals"])), ("No recorded outcome", count(stats["unresolved"])), ("Hospitalized", count(stats["hospitalized"])), ("Refused", count(stats["refused"])), ("Mean observed wait", number(stats["mean_wait"], " d")), ("Hospitals analyzed", count(stats["hospitals"]))]
    for column, (label, value) in zip(st.columns(6), metrics):
        column.metric(label, value)
    st.caption("Selected registration cohort. ‘No recorded outcome’ is an unresolved record in the extract, not a live waiting-list count. Mean wait uses valid observed hospitalizations within 0–90 days.")
    excluded = int(stats["conflicting"] + stats["invalid_outcome"])
    if excluded:
        st.caption(f"{excluded:,} cohort records have conflicting or invalid outcomes; they remain in the total and are excluded from outcome KPIs and waiting-time targets.")
    if not stats["referrals"]:
        st.info("No referrals match these filters. Broaden the hospital, region, profile or registration interval.")
        return
    events, waits, hospitals = cached_charts(version, filters)
    with st.container(border=True):
        st.subheader("Observed activity")
        st.caption("Daily events for the selected registration cohort. Later outcomes appear on their actual event dates.")
        if not events.empty:
            chart(px.line(events, x="date", y="records", color="event", color_discrete_sequence=COLORS, labels={"date": "Event date", "records": "Records", "event": ""}))
    left, right = st.columns([1.05, 1])
    with left, st.container(border=True):
        st.subheader("Waiting-time distribution")
        st.caption(f"{count(stats['eligible'])} eligible hospitalizations · Median {number(stats['median_wait'])} days")
        if not waits.empty:
            chart(px.bar(waits, x="waiting_day", y="records", color_discrete_sequence=COLORS, labels={"waiting_day": "Waiting time (whole-day bins)", "records": "Hospitalizations"}), 300)
        else:
            st.info("No eligible waiting-time outcomes in this cohort.")
    with right, st.container(border=True):
        st.subheader("Hospitals by referral volume")
        st.caption("Largest 10 organizations in the selected cohort")
        top = hospitals.head(10).sort_values("referrals")
        # Names remain available in hover; short labels keep long organization names readable.
        top = top.assign(label=top["hospital"].fillna("Unknown").str.slice(0, 42))
        fig = px.bar(top, x="referrals", y="label", orientation="h", hover_data=["hospital"], color_discrete_sequence=COLORS, labels={"referrals": "Referrals", "label": ""})
        chart(fig, 300)
    if explorer:
        st.subheader("Organization summary")
        st.caption("Up to 20 hospitals by referral count. Aggregates only; no patient identifiers.")
        st.dataframe(hospitals, hide_index=True, width="stretch", column_config={"mean_wait_days": st.column_config.NumberColumn("Mean wait, days", format="%.2f")})
    else:
        summary = report.get("summary", {})
        waiting_count = summary.get("waiting_records")
        st.markdown("**Data coverage**")
        if waiting_count is not None:
            st.caption(f"Waiting source: {count(waiting_count)} recorded rows across the full extract. This source is a historical snapshot; cohort filters above do not apply to this count.")
        st.caption((coverage_note(report) + ". " if coverage_note(report) else "") + "Partial files limit population coverage. Current bed occupancy and a live national queue cannot be inferred from these extracts.")


def model_training_control(changed):
    if changed:
        st.warning("New or changed CSV files were detected. Refresh data before training or using the model.")
    if st.button("Train / evaluate CatBoost", disabled=changed or st.session_state.get("demo_mode", False), type="primary"):
        try:
            from src.train_waiting_model import train_model
            with st.spinner("Training CatBoost and evaluating on later registration dates…"):
                train_model()
            st.cache_data.clear()
            st.rerun()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Dashboard model training failed")
            st.error("Training could not finish. Run `python -m src.train_waiting_model` to inspect the error.")


def prediction_page(report, changed):
    title("WAITING TIME · CATBOOST", "A historical estimate, in seconds.", "Estimate typical registration-to-hospitalization waiting time for a referral profile.")
    metadata = read_json(METADATA_PATH)
    stale = changed or (bool(metadata) and metadata.get("source_fingerprint") != report.get("source_fingerprint"))
    st.info("Model estimate based on historical hospitalization patterns. Applies to observed hospitalizations within 0–90 days; it is not a remaining-queue-time estimate or a medical recommendation.")
    if not metadata or not MODEL_PATH.exists() or stale:
        if stale:
            st.warning("The saved model is stale relative to the available data. Refresh data and retrain to enable predictions.")
        else:
            st.info("No trained model is available yet. Train the baseline on the prepared data.")
        model_training_control(changed)
        return
    options = metadata.get("feature_options", {})
    labels = {"hospital_mo": "Hospital", "icd10_ref_diag_code": "Referral diagnosis code (ICD-10)", "bed_profile": "Bed profile", "territorial_type": "Territorial type", "referral_purpose": "Referral purpose", "finance_source": "Finance source"}
    with st.form("waiting_prediction"):
        left, right = st.columns(2)
        record = {}
        for index, (key, label) in enumerate(labels.items()):
            with (left if index % 2 == 0 else right):
                values = options.get(key, [])
                record[key] = st.selectbox(label, values or ["Unknown"], key=f"predict_{key}")
        end = metadata.get("test_period", {}).get("end")
        selected_date = pd.Timestamp(end).date() if end else date.today()
        record["registration_dt"] = st.date_input("Registration date", value=selected_date)
        submit = st.form_submit_button("Estimate waiting time", type="primary")
    if submit:
        try:
            from src.explanations import explain_waiting
            explanation = explain_waiting(record)
            st.metric("Predicted typical waiting time", number(explanation["prediction"], " days"))
            st.caption("Initial ML baseline — Work in Progress. The estimate is a model output, not a guaranteed date of admission.")
            st.caption(f"Measured holdout MAE: {number(metadata.get('metrics', {}).get('mae'))} days. This average error is not a personal prediction interval.")
            st.subheader("Why this estimate?")
            contributions = pd.DataFrame(explanation["contributions"])
            chart(px.bar(contributions.sort_values("contribution"), x="contribution", y="label", orientation="h",
                         color="contribution", color_continuous_scale="Tealrose",
                         labels={"contribution": "Contribution to raw model estimate (days)", "label": ""}))
            st.caption(f"SHAP reference {number(explanation['base_value'])} days + signed contributions = raw estimate {number(explanation['raw_prediction'])} days. Nonnegative adjustment: {number(explanation['clipping_adjustment'])} days. Associations learned by the model do not establish causes.")
            if explanation["unseen_categories"]:
                st.warning("Some selected categories were not present in training; reliability is uncertain.")
            st.info("Analyst review: check the profile, historical period and validation error before discussing planning decisions. This estimate does not assign a hospitalization date or route a patient.")
            if end and pd.Timestamp(record["registration_dt"]) > pd.Timestamp(end):
                st.warning("This date is beyond the evaluation period. Future performance has not been established.")
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Dashboard prediction failed")
            st.error("Prediction could not be calculated. Check that the saved model matches the current metadata.")
    with st.expander("How to interpret this estimate"):
        st.write("The model learns from completed, valid hospitalizations. Refused, unresolved and invalid cases do not provide this target. Results can therefore differ from the waiting experience of all people referred to hospital. Category lists come from the training data.")
        st.write("A CatBoost model trained with absolute-error loss estimates typical (conditional median) waiting time. Compare its held-out error with the historical-median baseline on the Model performance page.")


def performance_page(report, changed):
    title("TEMPORAL VALIDATION", "Measure before you trust.", "Initial ML baseline — Work in Progress. Metrics come from saved results of a real training run.")
    meta = read_json(METADATA_PATH)
    if not meta:
        st.info("Train the waiting-time model to see measured performance.")
        model_training_control(changed)
        return
    if changed or meta.get("source_fingerprint") != report.get("source_fingerprint"):
        st.warning("These metrics belong to an earlier dataset version. Refresh the data and retrain before presenting them as current.")
    metrics = meta.get("metrics", {})
    for col, (label, key, suffix) in zip(st.columns(4), [("CatBoost MAE", "mae", " d"), ("CatBoost RMSE", "rmse", " d"), ("Median baseline MAE", "baseline_mae", " d"), ("MAE improvement", "improvement_pct", "%")]):
        col.metric(label, number(metrics.get(key), suffix))
    improvement = metrics.get("improvement_pct")
    if improvement is not None and improvement < 0:
        st.warning("CatBoost has higher MAE than the historical-median baseline on this test period. The negative improvement is retained; this run does not establish an advantage for the model.")
    st.caption("MAE: average absolute error in days. RMSE emphasizes larger errors. Improvement = (baseline MAE − model MAE) / baseline MAE × 100%.")
    train, test = meta.get("train_period", {}), meta.get("test_period", {})
    rows = meta.get("rows", {})
    with st.container(border=True):
        st.subheader("Earlier dates train. Later dates test.")
        st.write(f"**Train:** {train.get('start', '—')} → {train.get('end', '—')} · **{count(rows.get('train'))}** rows")
        st.write(f"**Test:** {test.get('start', '—')} → {test.get('end', '—')} · **{count(rows.get('test'))}** rows")
        st.caption("Chronological split by registration date. Outcome dates are used only to construct or validate the target and label availability.")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Actual vs predicted")
        st.caption("Aggregated test-set waiting-time bins; groups with fewer than 10 records are omitted.")
        points = pd.DataFrame(meta.get("actual_vs_predicted", []))
        if not points.empty and {"actual_mean", "predicted_mean", "count"}.issubset(points.columns):
            fig = px.scatter(points, x="actual_mean", y="predicted_mean", size="count", color_discrete_sequence=COLORS, labels={"actual_mean": "Observed mean wait (days)", "predicted_mean": "Predicted mean wait (days)", "count": "Records"})
            bound = max(points["actual_mean"].max(), points["predicted_mean"].max())
            fig.add_trace(go.Scatter(x=[0, bound], y=[0, bound], mode="lines", line=dict(color="#9AA9B9", dash="dash"), name="Perfect agreement", hoverinfo="skip"))
            chart(fig)
        else:
            st.info("No sufficiently large validation groups are available to plot.")
    with right, st.container(border=True):
        st.subheader("Feature importance")
        st.caption("Model contribution, not a causal explanation")
        importance = pd.DataFrame(meta.get("feature_importance", []))
        if not importance.empty and {"feature", "importance"}.issubset(importance.columns):
            chart(px.bar(importance.sort_values("importance").tail(12), x="importance", y="feature", orientation="h", color_discrete_sequence=COLORS, labels={"importance": "Importance", "feature": ""}))
    with st.expander("Training details and limitations", expanded=False):
        for limitation in meta.get("limitations", []):
            st.write(f"• {limitation}")
        st.json(meta, expanded=False)
    model_training_control(changed)


def forecast_page(report, changed):
    title("7-DAY REFERRAL FORECAST", "A short-term demand prototype.", "Forecasted incoming referrals by hospital, based on historical daily referral counts.")
    st.warning("Prototype only: this forecasts referrals received, not bed occupancy, staffed capacity, admissions, or a live waiting list.")
    path = PROCESSED_DIR / "hospital_day.parquet"
    if not path.exists():
        st.info("Prepare the referral data before training a forecast.")
        return
    from src.load_forecast import METADATA_PATH as FORECAST_METADATA_PATH, forecast_status
    metadata = read_json(FORECAST_METADATA_PATH)
    status = forecast_status(report)
    if changed or not status["available"]:
        st.info("Source data changed. Refresh data first." if changed else status["reason"])
        if st.button("Train / evaluate 7-day forecast", disabled=changed or st.session_state.get("demo_mode", False), type="primary"):
            try:
                from src.load_forecast import train_load_forecast
                with st.spinner("Training the seven-day referral-load prototype on historical hospital/day data…"):
                    train_load_forecast()
                st.cache_data.clear()
                st.rerun()
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Load forecast training failed")
                st.error("Forecast training could not finish. Refresh the prepared data and check the logs; at least 42 days are required for training and validation.")
        return
    metrics = metadata.get("metrics", {})
    for column, (label, key, suffix) in zip(st.columns(4), [("Forecast MAE", "mae", " referrals"), ("Forecast RMSE", "rmse", " referrals"), ("7-day mean baseline MAE", "baseline_mae", " referrals"), ("MAE improvement", "improvement_pct", "%")]):
        column.metric(label, number(metrics.get(key), suffix))
    split = metadata.get("split", {})
    st.caption(f"Historical test: {metadata['test_period']['start'][:10]} to {metadata['test_period']['end'][:10]}. All seven days are predicted from the end of {split['forecast_origin'][:10]}, using only observations available by that date. Lower MAE is better.")
    st.caption(f"Same-weekday baseline MAE: {number(metrics.get('seasonal_baseline_mae'))} referrals. Test covers {split['test_hospitals']:,} hospitals; {split['excluded_test_hospitals']:,} excluded for insufficient history or incomplete follow-up.")
    if metrics.get("improvement_pct") is not None and metrics["improvement_pct"] < 0:
        st.warning("The model did not beat the 7-day mean baseline on this holdout.")
    if metrics.get("seasonal_baseline_mae") is not None and metrics["mae"] > metrics["seasonal_baseline_mae"]:
        st.warning("The same-weekday baseline performed better than the model on this holdout.")
    weaker_horizons = [str(row["horizon"]) for row in metadata.get("metrics_by_horizon", []) if row["mae"] > row["baseline_mae"]]
    if weaker_horizons:
        st.caption(f"The 7-day mean baseline performed better at these forecast horizons (days): {', '.join(weaker_horizons)}. See the breakdown below.")
    with st.expander("Validation by forecast horizon"):
        st.dataframe(pd.DataFrame(metadata.get("metrics_by_horizon", [])), hide_index=True, width="stretch")
    hospitals = db.aggregate_query(path, "SELECT hospital_mo FROM read_parquet(?) GROUP BY hospital_mo ORDER BY sum(referrals) DESC, hospital_mo")["hospital_mo"].dropna().astype(str).tolist()
    if not hospitals:
        st.info("No hospitals with referral history are available.")
        return
    selected = st.selectbox("Hospital", hospitals, key="forecast_hospital")
    try:
        from src.load_forecast import forecast_next_week
        forecast = forecast_next_week(selected)
        history = db.pressure_rows(path, hospital=selected).sort_values("date").tail(28)
    except (ValueError, FileNotFoundError):
        st.info("This hospital does not yet have the 28 observed days required for a forecast.")
        return
    total = float(forecast["predicted_referrals"].sum())
    st.metric("Predicted referrals · next 7 days", number(total))
    st.caption(f"Historical projection for {forecast['date'].min():%Y-%m-%d} to {forecast['date'].max():%Y-%m-%d}, after the last supplied observation ({metadata['history_end'][:10]}). This is not a forecast for the current calendar week.")
    with st.container(border=True):
        observed = history.loc[:, ["date", "referrals"]].rename(columns={"referrals": "records"}).assign(series="Observed referrals")
        projected = forecast.rename(columns={"predicted_referrals": "records"}).assign(series="Forecast")
        chart(px.line(pd.concat([observed, projected]), x="date", y="records", color="series", markers=True, color_discrete_sequence=[COLORS[0], COLORS[2]], labels={"date": "Date", "records": "Referrals", "series": ""}))
    values = forecast.assign(predicted_referrals=forecast["predicted_referrals"].round(1)).rename(columns={"date": "Forecast date", "predicted_referrals": "Predicted referrals"})
    st.dataframe(values, hide_index=True, width="stretch")
    with st.expander("Why this daily forecast?"):
        horizon = st.select_slider("Day ahead to explain", options=list(range(1, 8)), value=1)
        from src.load_forecast import explain_next_week
        explanation = explain_next_week(selected, horizon)
        contributions = pd.DataFrame(explanation["contributions"])
        chart(px.bar(contributions.sort_values("contribution"), x="contribution", y="label", orientation="h",
                     labels={"contribution": "Contribution to raw forecast (referrals)", "label": ""}))
        st.caption(f"Reference {number(explanation['base_value'])} + signed contributions = {number(explanation['raw_prediction'])} before nonnegative adjustment. All observed features stop at {metadata['history_end'][:10]}. Model associations are not causal explanations.")
    with st.expander("Forecast scope and limits"):
        for limitation in metadata.get("limitations", []):
            st.write(f"• {limitation}")
        st.json(metadata, expanded=False)


def pressure_cohort():
    path = PROCESSED_DIR / "hospital_day.parquet"
    if not path.exists():
        st.info("Hospital/day monitoring is not prepared yet. Run `python -m src.aggregation` after the data pipeline.")
        return
    st.caption("This page has its own hospital/event-date scope. Region and bed-profile filters from the referral explorer do not apply.")
    values = db.aggregate_query(path, "SELECT hospital_mo FROM read_parquet(?) GROUP BY hospital_mo ORDER BY sum(referrals) DESC, hospital_mo")["hospital_mo"].dropna().tolist()
    selected = st.selectbox("Hospital for monitoring", values)
    if not selected:
        st.info("No hospital monitoring rows are available.")
        return
    try:
        rows = db.pressure_rows(path, hospital=selected).sort_values("date")
    except duckdb_error_types():
        st.info("The hospital/day artifact uses a different schema. Rebuild it with `python -m src.aggregation`.")
        return
    if rows.empty:
        st.info("No hospital/day records for this organization.")
        return
    low, high = pd.Timestamp(rows["date"].min()).date(), pd.Timestamp(rows["date"].max()).date()
    selected_dates = st.date_input("Historical event dates", (low, high), min_value=low, max_value=high, key="pressure_dates")
    if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
        rows = rows.loc[(pd.to_datetime(rows["date"]).dt.date >= selected_dates[0]) & (pd.to_datetime(rows["date"]).dt.date <= selected_dates[1])]
    if rows.empty:
        st.info("No records in this interval.")
        return
    last = rows.iloc[-1]
    st.caption(f"Indicator as of {pd.Timestamp(last['date']).date()} · Historical cohort only")
    cols = st.columns(3)
    cols[0].metric("Prototype pressure", str(last["prototype_pressure"]).replace("_", " "))
    cols[1].metric("Reconstructed open cohort", count(last["reconstructed_open_cohort"]))
    cols[2].metric("Referrals on this date", count(last["referrals"]))
    st.warning("Prototype risk indicator — not yet clinically/operationally validated. Open cohort is reconstructed from available referrals and observed exits; it is not bed occupancy or a current waiting list.")
    st.caption(str(last["pressure_reason"]))
    with st.container(border=True):
        melted = rows.melt(id_vars=["date"], value_vars=["referrals", "hospitalized", "refusals"], var_name="event", value_name="records")
        chart(px.line(melted, x="date", y="records", color="event", color_discrete_sequence=COLORS, labels={"date": "Event date", "records": "Records", "event": ""}))
    with st.container(border=True):
        st.subheader("Reconstructed open cohort")
        chart(px.area(rows, x="date", y="reconstructed_open_cohort", color_discrete_sequence=COLORS, labels={"date": "Event date", "reconstructed_open_cohort": "Observed open referrals"}), 250)
    anomaly_columns = [c for c in rows if c.startswith("anomaly_")]
    alerts = rows.loc[rows[anomaly_columns].any(axis=1), ["date", "referrals", "refusals", "reconstructed_open_cohort", *anomaly_columns]] if anomaly_columns else pd.DataFrame()
    st.subheader("Statistical anomaly signals")
    st.caption("Signals compare activity with previous observations. They are analytical flags, not evidence of operational overload.")
    if alerts.empty:
        st.info("No anomaly flags for this hospital and interval.")
    else:
        st.dataframe(alerts.sort_values("date", ascending=False).head(100), hide_index=True, width="stretch")
    with st.expander("Transparent indicator rules"):
        indicator = read_json(PROCESSED_DIR / "aggregation_summary.json").get("indicator", {})
        if indicator:
            st.json(indicator)
        else:
            st.caption("Historical percentiles and statistical deviations are computed from preceding observations only. Insufficient history is shown explicitly.")


def independent_refusals():
    st.subheader("Independent refusal feed")
    st.caption("Reception-room refusal records. This feed is not joined to referrals; organization and region labels are specific to this source.")
    path = PROCESSED_DIR / "refusals.parquet"
    if not path.exists():
        st.info("No separate refusal feed is available.")
        return
    options = db.aggregate_query(path, "SELECT DISTINCT region_in FROM read_parquet(?) WHERE region_in IS NOT NULL ORDER BY region_in")["region_in"].tolist()
    organizations = db.aggregate_query(path, "SELECT DISTINCT org_in FROM read_parquet(?) WHERE org_in IS NOT NULL ORDER BY org_in")["org_in"].tolist()
    left, right = st.columns(2)
    region = left.selectbox("Region in refusal feed", [None, *options], format_func=lambda value: "All" if value is None else value)
    organization = right.selectbox("Organization in refusal feed", [None, *organizations], format_func=lambda value: "All" if value is None else value)
    clauses, params = ["refuse_dt IS NOT NULL"], []
    if region is not None:
        clauses.append("region_in = ?")
        params.append(region)
    if organization is not None:
        clauses.append("org_in = ?")
        params.append(organization)
    where = " AND ".join(clauses)
    daily = db.aggregate_query(path, f"SELECT CAST(refuse_dt AS DATE) AS date, count(*) AS refusals FROM read_parquet(?) WHERE {where} GROUP BY date ORDER BY date", params)
    if daily.empty:
        st.info("No dated refusal records match these source filters.")
        return
    start, end = pd.Timestamp(daily["date"].min()).date(), pd.Timestamp(daily["date"].max()).date()
    selected = st.date_input("Refusal event dates", (start, end), min_value=start, max_value=end, key="refusal_feed_dates")
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        daily = daily.loc[(pd.to_datetime(daily["date"]).dt.date >= selected[0]) & (pd.to_datetime(daily["date"]).dt.date <= selected[1])]
    st.metric("Dated refusal-feed records", count(daily["refusals"].sum()))
    chart(px.bar(daily, x="date", y="refusals", color_discrete_sequence=[COLORS[2]], labels={"date": "Refusal event date", "refusals": "Records"}))
    st.caption("Observed dated events only. Counts must not be added to referral refusals: overlap is unknown and available source parts may cover different populations.")


def treated_context():
    st.subheader("Treated-case organizational context")
    st.caption("Separate aggregate extract. Its reporting period is not established by its load timestamp; it is not a hospital-capacity denominator or a 2025 time-series feature.")
    path = PROCESSED_DIR / "treated.parquet"
    if not path.exists():
        st.info("No treated-case aggregate extract is available.")
        return
    totals = db.aggregate_query(path, """SELECT count(*) AS source_rows,
        count(DISTINCT medicine_organization) AS organizations,
        min(sdu_load_date) AS earliest_load, max(sdu_load_date) AS latest_load
        FROM read_parquet(?)""").iloc[0]
    left, right = st.columns(2)
    left.metric("Aggregate source records", count(totals["source_rows"]))
    right.metric("Organizations in this source", count(totals["organizations"]))
    st.caption(f"Source load timestamps: {totals['earliest_load']} → {totals['latest_load']}")
    values = db.aggregate_query(path, """SELECT medicine_organization AS organization,
        count(*) AS source_records, sum(discharged_total) AS reported_discharges,
        sum(bed_days) AS reported_bed_days
        FROM read_parquet(?) GROUP BY medicine_organization
        ORDER BY reported_discharges DESC NULLS LAST LIMIT 20""")
    st.dataframe(values, hide_index=True, width="stretch")
    st.caption("Top 20 organizations by sum of reported discharges across source records. Different record periods may overlap. No hospital-name matching or normalization across datasets is assumed.")


def pressure_page():
    title("HOSPITAL ACTIVITY", "Pressure signals, made transparent.", "Historical monitoring of the observed referral cohort.")
    st.info("The separate 7-day load forecast page evaluates incoming referrals. Bed occupancy, operational capacity, and 30/90-day forecasts require additional data and validation.")
    cohort, refusal, treated = st.tabs(["Referral cohort", "Separate refusal feed", "Treated-case context"])
    with cohort:
        pressure_cohort()
    with refusal:
        independent_refusals()
    with treated:
        treated_context()


def duckdb_error_types():
    import duckdb
    return (duckdb.Error,)


def quality_page(report):
    title("DATA PROVENANCE", "Know what the data can tell you.", "Source coverage, cleaning decisions, date validity and linkage checks from the latest preparation run.")
    note = coverage_note(report)
    if note:
        st.info(note)
    datasets = report.get("datasets", {})
    inventory = []
    for category, details in datasets.items():
        inventory.append({"Dataset": category, "Rows": details.get("rows"), "Columns": len(details.get("columns", [])), "Hospitals": details.get("unique_hospitals"), "Regions": details.get("unique_regions"), "Diagnoses": details.get("unique_diagnoses")})
    if inventory:
        st.dataframe(pd.DataFrame(inventory), hide_index=True, width="stretch")
    join = report.get("join", {})
    if join:
        st.subheader("Waiting ↔ referrals linkage")
        cols = st.columns(3)
        cols[0].metric("Matched referrals", count(join.get("matched_rows")))
        rate = join.get("match_rate")
        cols[1].metric("Match rate", number(float(rate) * 100, "%") if rate is not None else "—")
        cols[2].metric("Ambiguous waiting keys", count(join.get("waiting_ambiguous_keys")))
        st.caption("Linkage uses the documented composite key. Ambiguous keys and conflicting referral records are audited; the interface never displays the identifiers.")
    for category, details in datasets.items():
        with st.expander(f"{category.title()} · quality details"):
            st.write("**Columns:** " + ", ".join(details.get("columns", [])))
            dates = details.get("dates", {})
            if dates:
                st.dataframe(pd.DataFrame.from_dict(dates, orient="index").rename_axis("Date column").reset_index(), hide_index=True, width="stretch")
            missing = details.get("missing_values", {})
            if missing:
                st.dataframe(pd.DataFrame([{"Column": key, "Missing": value} for key, value in missing.items()]), hide_index=True, width="stretch")
    with st.expander("Cleaning and exclusion audit", expanded=True):
        st.json(report.get("cleaning", {}), expanded=False)
    st.caption("Refusal-feed records have no verified referral join key. Treated cases are a separate organizational extract with a different time basis; they are excluded from time-dependent prediction features.")
    with st.expander("Complete aggregate quality report"):
        st.json(report, expanded=False)
    st.download_button("Download quality report", json.dumps(report, ensure_ascii=False, indent=2), "medflow_data_quality.json", "application/json")
    with st.expander("All local sources and laboratory coverage"):
        from src.workbench import source_inventory
        source_inventory()


def main():
    st.set_page_config(page_title="MedFlow AI · Hospital Load Intelligence", page_icon="✚", layout="wide", initial_sidebar_state="expanded")
    theme()
    report = read_json(QUALITY_PATH)
    ready = ANALYTICAL_PATH.exists() and bool(report.get("pipeline_complete"))
    has_sources, changed = source_status(report)
    page, filters, refresh = sidebar(report, ready)
    if refresh:
        prepare_data()
    if not ready:
        empty_state()
        if has_sources:
            st.caption("CSV files detected. Use the sidebar to prepare them once; navigation never rereads complete CSV files.")
        return
    if changed:
        st.warning("New or changed source files detected. Displayed analytics belong to the previous preparation run. Select Prepare / refresh data to include the new files.")
    if page in {"Overview", "Hospital explorer"}:
        overview_page(report, filters, explorer=page == "Hospital explorer")
    elif page == "Compare & review":
        from src.workbench import comparison_page
        comparison_page(report, changed)
    elif page == "Waiting time prediction":
        prediction_page(report, changed)
    elif page == "Model performance":
        performance_page(report, changed)
    elif page == "7-day load forecast":
        forecast_page(report, changed)
    elif page == "Validation evidence":
        from src.workbench import validation_page
        validation_page()
    elif page == "Pressure & anomalies":
        pressure_page()
    else:
        quality_page(report)
    st.divider()
    st.caption("MEDFLOW AI · GovTech Case 1 · Historical decision support · Aggregate data only")
