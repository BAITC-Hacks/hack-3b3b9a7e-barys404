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


def comparison_page(report, changed, filters=None):
    from src.experience import context_strip
    title("СТАЦИОНАРЫ / СРАВНЕНИЕ", "Сравнить и подготовить сводку",
          "Общий период и профиль, понятные знаменатели, проверка аналитиком перед выгрузкой.")
    dimensions = db.dimensions()
    start, end = pd.Timestamp(dimensions["dates"]["first"]).date(), pd.Timestamp(dimensions["dates"]["last"]).date()
    filters = dict(filters or {"start": start, "end": end})
    context_strip(filters)
    st.caption("Регион означает происхождение направления. Сравнение не скорректировано на тяжесть случаев или доступную мощность организации.")
    left, right = st.columns(2)
    mode = left.radio("Сравнить", ["Стационары", "Регионы происхождения"], horizontal=True, key="comparison_mode")
    group = "hospital_mo" if mode == "Стационары" else "region_origin_code"
    st.session_state.setdefault("comparison_minimum", 100)
    minimum = right.select_slider("Минимум направлений на группу", options=[30, 50, 100, 300], key="comparison_minimum")
    table = comparison_data(db.file_version(ANALYTICAL_PATH), filters, group, minimum)
    if table.empty:
        st.info("Нет групп с достаточным числом записей. Измените фильтры или минимальный размер группы.")
        return
    names = table["organization_or_region"].tolist()
    active = st.session_state.get("active_hospital")
    defaults = names[:3]
    if group == "hospital_mo" and active in names:
        defaults = [active] + [name for name in names if name != active][:2]
    key = f"comparison_groups_{group}"
    if key not in st.session_state:
        st.session_state[key] = defaults
    else:
        st.session_state[key] = [name for name in st.session_state[key] if name in names]
    selected = st.multiselect("Группы для сравнения (до 6)", names, max_selections=6, key=key)
    if not selected:
        st.info("Выберите хотя бы одну группу.")
        return
    chosen = table.set_index("organization_or_region").loc[selected].reset_index()
    labels = {name: f"Группа {chr(65 + index)}" for index, name in enumerate(selected)}
    chosen.insert(0, "group", chosen["organization_or_region"].map(labels))
    first, second, third = st.columns(3)
    first.metric("Группы в сравнении", count(len(chosen)))
    second.metric("Направления", count(chosen["referrals"].sum()))
    third.metric("Допустимые госпитализации", count(chosen["eligible_waits"].sum()))
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Входящие направления")
        chart(px.bar(chosen, x="referrals", y="group", orientation="h", hover_data=["organization_or_region"],
                     labels={"referrals": "Направления", "group": "", "organization_or_region": "Группа"}))
    with right, st.container(border=True):
        st.subheader("Наблюдаемое ожидание")
        waits = chosen.melt(id_vars=["group", "organization_or_region"], value_vars=["median_wait_days", "p90_wait_days"], var_name="measure", value_name="days").dropna(subset=["days"])
        waits["measure"] = waits["measure"].map({"median_wait_days": "Медиана", "p90_wait_days": "P90"})
        if not waits.empty:
            chart(px.bar(waits, x="days", y="group", color="measure", barmode="group", orientation="h", hover_data=["organization_or_region"], labels={"days": "Дни", "group": "", "measure": "", "organization_or_region": "Группа"}))
        else:
            st.info("Недостаточно допустимых госпитализаций для сравнения сроков.")
    st.dataframe(chosen.rename(columns={"group": "Метка", "organization_or_region": "Организация / регион", "referrals": "Направления", "hospitalized": "Госпитализации", "refused": "Отказы", "unresolved": "Исход не записан", "excluded_outcomes": "Некорректные исходы", "eligible_waits": "Допустимые ожидания", "median_wait_days": "Медиана, дни", "p90_wait_days": "P90, дни", "refusal_share_pct": "Доля отказов, %"}), hide_index=True, width="stretch")
    st.caption(f"Для сроков нужны минимум {minimum} допустимых госпитализаций. Доля отказов = отказы / (госпитализации + отказы), минимум {minimum} известных исходов. Пустое значение означает недостаточно данных.")
    trend = db.comparison_trends(filters, group, selected)
    if not trend.empty:
        # Reindex before plotting so suppressed weeks cannot be bridged by a line.
        weeks = pd.date_range(pd.Timestamp(filters["start"]).to_period("W").start_time, pd.Timestamp(filters["end"]), freq="W-MON")
        index = pd.MultiIndex.from_product([selected, weeks], names=["organization_or_region", "week"])
        trend = trend.set_index(["organization_or_region", "week"]).reindex(index).reset_index()
        trend["group"] = trend["organization_or_region"].map(labels)
        chart(px.line(trend, x="week", y="referrals", color="group", markers=True, hover_data=["organization_or_region"], labels={"week": "Неделя регистрации", "referrals": "Направления", "group": "Группа", "organization_or_region": "Организация / регион"}))
        st.caption("Недели с менее чем 10 записями скрыты. Пробел не равен нулю. Крайние недели могут быть неполными.")
    st.subheader("Сводка для ответственного специалиста")
    st.write("Проверьте полноту источников, исходы и различия профилей. Доступную мощность организации нужно уточнить у специалиста.")
    question = st.selectbox("Вопрос для проверки", ["Почему различаются наблюдаемые сроки ожидания?", "Как изменились поток направлений и доступная мощность?", "Каковы причины отказов и полнота регистрации?"], key="review_question")
    review_context = json.dumps([filters, group, minimum, selected, question, report.get("source_fingerprint")], sort_keys=True, default=str)
    review_key = "review_" + hashlib.sha256(review_context.encode()).hexdigest()[:16]
    reviewed = st.checkbox("Я проверил период, область сравнения и ограничения перед подготовкой сводки.", key=review_key)
    payload = {"created_at": datetime.now(timezone.utc).isoformat(), "source_fingerprint": report.get("source_fingerprint"),
               "source_period": {"start": str(start), "end": str(end)}, "filters": {key: str(value) if value is not None else None for key, value in filters.items()},
               "group_dimension": group, "minimum_group_size": minimum,
               "review_status": "reviewed_for_discussion" if reviewed else "pending", "review_question": question,
               "aggregates": json.loads(chosen.to_json(orient="records")),
               "limitations": ["Исторические регионы происхождения, не местонахождение стационара.", "Не оценка мощности и качества лечения; не рекомендация по маршрутизации.", "Локальное подтверждение просмотра; формальное согласование и исполнение решений не реализованы."]}
    pdf = b""
    if reviewed and not changed:
        from src.briefing import build_briefing_pdf
        from src.predict import model_status
        from src.load_forecast import forecast_status, METADATA_PATH as FORECAST_METADATA_PATH
        from src.config import METADATA_PATH
        from src.utils import read_json
        metrics = {}
        for name, model_path, available in [("waiting", METADATA_PATH, model_status()["available"]), ("forecast", FORECAST_METADATA_PATH, forecast_status(report)["available"])]:
            if available:
                meta = read_json(model_path)
                metrics[name] = {**meta["metrics"], "period": f"{meta['test_period']['start'][:10]} - {meta['test_period']['end'][:10]}"}
        try:
            pdf = build_briefing_pdf(payload, metrics)
        except ValueError as exc:
            st.warning(str(exc))
    a, b = st.columns([2, 1])
    a.download_button("Скачать PDF-сводку", pdf, "medflow_briefing.pdf", "application/pdf", disabled=not bool(pdf), type="primary", width="stretch")
    b.download_button("Скачать JSON", json.dumps(payload, ensure_ascii=False, indent=2), "medflow_reviewed_briefing.json", "application/json", disabled=not reviewed or changed, width="stretch")
    st.caption("Только агрегаты организаций. При изменении контекста нужно повторное подтверждение. Автоматические управленческие действия не выполняются.")


def validation_page():
    from src.validation import validation_status
    from src.localization import LABELS, display_frame
    title("МОДЕЛИ / ПРОВЕРКА ПО ПЕРИОДАМ", "Сохраняется ли качество на других неделях?",
          "Три непересекающихся тестовых окна, растущая история обучения и фиксированные параметры.")
    state = validation_status()
    if not state["available"]:
        st.info("Актуальный отчёт по временным окнам недоступен. Подготовьте данные и выполните проверку.")
        st.code("python -m src.validation")
        return
    report = state["report"]
    st.caption("Это отдельные повторные обучения. Их результаты не заменяют метрики сохранённых моделей. В общей ошибке каждое тестовое наблюдение имеет одинаковый вес.")
    wait_tab, load_tab = st.tabs(["Ожидание госпитализации", "Входящие направления на 7 дней"])
    for tab, key, unit in [(wait_tab, "waiting", "дни"), (load_tab, "forecast", "направления / организацию / день")]:
        with tab:
            result = report[key]
            metrics = result["pooled"]
            for col, label, metric in zip(st.columns(4), ["Общая MAE", "MAE простого прогноза", "Снижение MAE", "P90 абсолютной ошибки"], ["mae", "baseline_mae", "improvement_pct", "p90_absolute_error"]):
                col.metric(label, number(metrics.get(metric), "%" if metric == "improvement_pct" else ""))
            st.caption(f"Единица ошибки: {unit}. P90 — квантиль ошибок на тесте, не персональный интервал прогноза.")
            if metrics["improvement_pct"] is not None and metrics["improvement_pct"] < 0:
                st.warning("На этих окнах модель не превзошла основной простой прогноз.")
            if key == "forecast":
                st.caption(f"MAE прогноза по тому же дню прошлой недели: {number(metrics.get('seasonal_baseline_mae'))} направления / организацию / день.")
                if metrics["mae"] > metrics["seasonal_baseline_mae"]:
                    st.warning("Прогноз по тому же дню прошлой недели оказался лучше модели.")
            folds = pd.DataFrame(result["folds"])
            folds["period"] = folds["test_start"].str[:10] + " → " + folds["test_end"].str[:10]
            graph_columns = ["mae", "baseline_mae"] + (["seasonal_baseline_mae"] if key == "forecast" else [])
            plotted = folds.melt(id_vars="period", value_vars=graph_columns, var_name="method", value_name="error")
            plotted["method"] = plotted["method"].map(LABELS)
            chart(px.bar(plotted, x="period", y="error", color="method", barmode="group", labels={"period": "Тестовый период", "error": f"MAE ({unit})", "method": ""}))
            st.dataframe(display_frame(folds.drop(columns="period")), hide_index=True, width="stretch")
            if key == "waiting":
                group = st.selectbox("Ошибки по группам", ["region_origin_code", "hospital_mo", "bed_profile"], format_func=LABELS.get)
                st.dataframe(display_frame(pd.DataFrame(result["groups"][group])), hide_index=True, width="stretch")
                st.caption(f"Минимум {result['minimum_group_size']} тестовых наблюдений на группу. Регионы относятся к происхождению направлений. Различия ошибок не являются рейтингом качества стационаров.")
            else:
                st.dataframe(display_frame(pd.DataFrame(result["by_horizon"])), hide_index=True, width="stretch")
    with st.expander("Протокол и ограничения"):
        st.write("Ожидание: только допустимые наблюдённые госпитализации, исходы обучения известны до теста. Поток: все семь дней прогнозируются из одной даты, без фактов тестовой недели в признаках. Три окна относятся к одной короткой истории. Время доставки и поздние исправления данных неизвестны. Нужны новые независимые периоды и внешняя проверка.")
        st.caption(f"Расчёт: {report['created_at']}. Подбора параметров по тесту нет. Действующие модели не изменялись.")
    st.download_button("Скачать агрегированный отчёт проверки", json.dumps(report, ensure_ascii=False, indent=2), "medflow_temporal_validation.json", "application/json")


def source_inventory():
    from src.data_loader import discover_files
    from src.localization import LABELS
    recognized = {path.resolve(): LABELS.get(category, category) for category, paths in discover_files().items() for path in paths}
    files = sorted(set(DATA_DIR.glob("*.csv")) | set((DATA_DIR / "raw").glob("*.csv")))
    rows = [{"Файл": path.name, "Размер, МБ": round(path.stat().st_size / 1_000_000, 1),
             "Использование": recognized.get(path.resolve(), "Не подключён к этому кейсу")}
            for path in files]
    st.subheader("Какие файлы используются?")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("Ожидающие и направления формируют госпитальную когорту. Отдельные отказы и пролеченные случаи показаны самостоятельными срезами. Остальные источники не являются признаками моделей.")
    st.info("Данные лабораторных исследований ЕИП пока не предоставлены. Для подключения нужны схема, словарь регионов, периоды и объёмы исследований.")
