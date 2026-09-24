"""Institutional comparison, evidence, and explicit human review for the demo."""
from datetime import datetime, timezone
import json
import hashlib

import pandas as pd
import plotly.express as px
import streamlit as st

from src import dashboard_data as db
from src.config import ANALYTICAL_PATH, DATA_DIR
from src.ui import chart, count, number, title


@st.cache_data(show_spinner=False)
def comparison_data(version, filters, group, minimum):
    return db.compare_groups(filters, group, minimum)


def comparison_page(report, changed):
    title("COMPARE · EXPLAIN · REVIEW", "Where should an analyst look next?",
          "Compare the same registration period and bed profile, inspect differences, then prepare a reviewed briefing.")
    st.info("Historical decision support. Region means the origin of the referral, not the hospital's location. Comparisons are descriptive and are not adjusted for patient complexity or available capacity.")
    dimensions = db.dimensions()
    left, middle, right = st.columns(3)
    mode = left.radio("Compare", ["Hospitals", "Origin regions"], horizontal=True)
    group = "hospital_mo" if mode == "Hospitals" else "region_origin_code"
    profile = middle.selectbox("Shared bed profile", [None, *dimensions["bed_profile"]], format_func=lambda value: "All profiles" if value is None else value)
    region = right.selectbox("Origin region filter", [None, *dimensions["region_origin_code"]], format_func=lambda value: "All origin regions" if value is None else value)
    start, end = pd.Timestamp(dimensions["dates"]["first"]).date(), pd.Timestamp(dimensions["dates"]["last"]).date()
    interval = st.date_input("Shared registration period", (start, end), min_value=start, max_value=end)
    minimum = st.select_slider("Minimum referrals per group", options=[30, 50, 100, 300], value=100)
    if not isinstance(interval, (tuple, list)) or len(interval) != 2:
        st.info("Choose both dates to compare groups.")
        return
    filters = {"bed_profile": profile, "region_origin_code": region, "start": interval[0], "end": interval[1]}
    table = comparison_data(db.file_version(ANALYTICAL_PATH), filters, group, minimum)
    if table.empty:
        st.info("No groups meet these filters and minimum sample size.")
        return
    selected = st.multiselect("Groups to compare (up to 6)", table["organization_or_region"].tolist(),
                              default=table["organization_or_region"].head(3).tolist(), max_selections=6)
    if not selected:
        st.info("Select at least one group.")
        return
    chosen = table.loc[table["organization_or_region"].isin(selected)].copy()
    labels = {name: f"Group {chr(65 + index)}" for index, name in enumerate(chosen["organization_or_region"])}
    chosen.insert(0, "group", chosen["organization_or_region"].map(labels))
    first, second, third = st.columns(3)
    first.metric("Compared groups", count(len(chosen)))
    second.metric("Referrals in selected groups", count(chosen["referrals"].sum()))
    third.metric("Eligible observed waits", count(chosen["eligible_waits"].sum()))
    left, right = st.columns(2)
    with left:
        st.subheader("Incoming referrals")
        chart(px.bar(chosen, x="referrals", y="group", orientation="h", hover_data=["organization_or_region"],
                     labels={"referrals": "Registered referrals", "group": ""}))
    with right:
        st.subheader("Observed waiting time")
        waits = chosen.melt(id_vars=["group", "organization_or_region"], value_vars=["median_wait_days", "p90_wait_days"],
                            var_name="measure", value_name="days").dropna(subset=["days"])
        if not waits.empty:
            chart(px.bar(waits, x="days", y="group", color="measure", barmode="group", orientation="h", hover_data=["organization_or_region"],
                         labels={"days": "Days among eligible hospitalizations", "group": "", "measure": ""}))
        else:
            st.info("Too few eligible hospitalizations to compare waiting times.")
    st.dataframe(chosen, hide_index=True, width="stretch")
    st.caption(f"Wait statistics require at least {minimum} eligible hospitalizations. Refusal share uses hospitalized + refused outcomes and requires the same minimum; unresolved and invalid outcomes are excluded from its denominator. Blank values mean insufficient evidence.")
    trend = db.comparison_trends(filters, group, selected)
    if not trend.empty:
        trend["group"] = trend["organization_or_region"].map(labels)
        chart(px.line(trend, x="week", y="referrals", color="group", markers=True, hover_data=["organization_or_region"],
                      labels={"week": "Registration week", "referrals": "Registered referrals", "group": "Group"}))
        st.caption("Weeks with fewer than 10 records are suppressed; gaps are not zero activity. Boundary weeks may be partial.")
    st.subheader("Prepare a human-reviewed briefing")
    st.write("Check source completeness and outcome validity, compare referral profiles, and confirm the organization's capacity with a responsible specialist before discussing operational changes.")
    question = st.selectbox("Question for the responsible specialist", [
        "Review why observed waiting times differ",
        "Review referral growth and available capacity",
        "Review refusal reasons and data completeness",
    ])
    review_context = json.dumps([filters, group, minimum, selected, question, report.get("source_fingerprint")], sort_keys=True, default=str)
    review_key = "review_" + hashlib.sha256(review_context.encode()).hexdigest()[:16]
    reviewed = st.checkbox("I checked the data period, comparison scope and limitations before preparing this briefing.", key=review_key)
    payload = {"created_at": datetime.now(timezone.utc).isoformat(), "source_fingerprint": report.get("source_fingerprint"),
               "source_period": {"start": str(start), "end": str(end)}, "filters": {key: str(value) if value is not None else None for key, value in filters.items()},
               "group_dimension": group, "minimum_group_size": minimum,
               "review_status": "reviewed_for_discussion" if reviewed else "pending",
               "review_question": question, "aggregates": json.loads(chosen.to_json(orient="records")),
               "limitations": ["Historical referral origin regions, not hospital location.",
                               "Not a capacity, clinical-quality or patient-routing recommendation.",
                               "Review acknowledgement is local to this session; there is no authenticated approval or decision execution."]}
    st.download_button("Download reviewed aggregate briefing", json.dumps(payload, ensure_ascii=False, indent=2),
                       "medflow_reviewed_briefing.json", "application/json", disabled=not reviewed or changed)
    st.caption("The briefing contains institutional aggregates only. It records a local review acknowledgement; no operational action or patient routing is performed.")


def validation_page():
    from src.validation import validation_status
    title("EVIDENCE ACROSS TIME", "Does the result hold on other weeks?",
          "Expanding training windows, disjoint test periods, fixed model parameters and no test-based tuning.")
    state = validation_status()
    if not state["available"]:
        st.info(state["reason"])
        st.code("python -m src.validation")
        return
    report = state["report"]
    st.caption("These are repeated historical evaluations, separate from the saved deployment models' single holdouts. Pooled errors weight each evaluated observation equally.")
    wait_tab, load_tab = st.tabs(["Waiting time", "7-day incoming referrals"])
    for tab, key, unit in [(wait_tab, "waiting", "days"), (load_tab, "forecast", "referrals / hospital-day")]:
        with tab:
            result = report[key]
            metrics = result["pooled"]
            for col, label, metric in zip(st.columns(4), ["Pooled MAE", "Baseline MAE", "MAE improvement", "P90 absolute error"],
                                          ["mae", "baseline_mae", "improvement_pct", "p90_absolute_error"]):
                col.metric(label, number(metrics.get(metric), "%" if metric == "improvement_pct" else ""))
            st.caption(f"Error unit: {unit}. P90 is a descriptive percentile of held-out absolute errors, not a prediction interval.")
            if metrics["improvement_pct"] is not None and metrics["improvement_pct"] < 0:
                st.warning("The model did not beat the primary baseline across these windows.")
            if key == "forecast":
                st.caption(f"Same-weekday baseline MAE: {number(metrics.get('seasonal_baseline_mae'))} referrals / hospital-day.")
                if metrics["mae"] > metrics["seasonal_baseline_mae"]:
                    st.warning("The same-weekday baseline performed better across these windows.")
            folds = pd.DataFrame(result["folds"])
            folds["period"] = folds["test_start"].str[:10] + " → " + folds["test_end"].str[:10]
            graph_columns = ["mae", "baseline_mae"] + (["seasonal_baseline_mae"] if key == "forecast" else [])
            plotted = folds.melt(id_vars="period", value_vars=graph_columns, var_name="method", value_name="error")
            chart(px.bar(plotted, x="period", y="error", color="method", barmode="group",
                         labels={"period": "Test window", "error": f"MAE ({unit})", "method": ""}))
            st.dataframe(folds.drop(columns="period"), hide_index=True, width="stretch")
            st.caption(result["evaluation_scope"])
            if key == "waiting":
                group = st.selectbox("Error breakdown", ["region_origin_code", "hospital_mo", "bed_profile"])
                st.dataframe(pd.DataFrame(result["groups"][group]), hide_index=True, width="stretch")
                st.caption(f"At least {result['minimum_group_size']} test observations per displayed group. Region codes refer to referral origins. Differences are descriptive, not adjusted hospital-quality scores.")
            else:
                st.dataframe(pd.DataFrame(result["by_horizon"]), hide_index=True, width="stretch")
    with st.expander("Validation protocol and limits"):
        for limitation in report["limitations"]:
            st.write("• " + limitation)
        st.caption(f"Computed {report['created_at']}. Hyperparameters selected on test: no. Deployment model artifacts modified: no.")
    st.download_button("Download aggregate validation evidence", json.dumps(report, ensure_ascii=False, indent=2),
                       "medflow_temporal_validation.json", "application/json")


def source_inventory():
    from src.data_loader import discover_files
    recognized = {path.resolve(): category for category, paths in discover_files().items() for path in paths}
    files = sorted(set(DATA_DIR.glob("*.csv")) | set((DATA_DIR / "raw").glob("*.csv")))
    rows = [{"File": path.name, "Size MB": round(path.stat().st_size / 1_000_000, 1),
             "Pipeline": recognized.get(path.resolve(), "Not connected to this case pipeline")}
            for path in files]
    st.subheader("Which files are actually used?")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("Waiting and referrals feed the hospital cohort. Independent refusals and treated cases have separate descriptive views. Unrecognized sources are not used as model features.")
    st.info("Laboratory research data (EIP) has not been provided. No laboratory-load forecast is claimed. Integration requires an agreed schema, region dictionary, observation periods and study counts.")
