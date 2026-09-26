"""Executive overview, hospital profile and a guided, real-data demonstration."""
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import dashboard_data as db
from src.config import ANALYTICAL_PATH, METADATA_PATH
from src.navigation import go_to, hospital_picker, role_actions
from src.ui import chart, count, number, title, read_json


@st.cache_data(show_spinner=False)
def activity(version, filters):
    return db.recent_activity(filters)


@st.cache_data(show_spinner=False)
def grid_data(version, filters, selected, limit):
    return db.weekly_activity(filters, selected, limit)


def period_label(filters):
    def fmt(value):
        return pd.Timestamp(value).strftime("%d.%m.%Y") if value else "весь период"
    return f"{fmt(filters.get('start'))} — {fmt(filters.get('end'))}"


def context_strip(filters):
    items = ["Исторические данные", period_label(filters),
             f"Регион происхождения: {filters.get('region_origin_code') or 'все'}",
             f"Профиль: {filters.get('bed_profile') or 'все'}"]
    st.markdown('<div class="context-strip">' + ''.join(f'<span>{escape(str(x))}</span>' for x in items) + '</div>', unsafe_allow_html=True)


def attention(filters, hospital=None):
    period, table = activity(db.file_version(ANALYTICAL_PATH), filters)
    st.subheader("Что требует внимания")
    if not period:
        st.info("Для сравнения двух полных семидневных периодов выберите не менее 14 дней.")
        return
    st.caption(f"Направления: {period['start']} — {period['end']} против {period['previous_start']} — {period['previous_end']}. Это изменение активности, не оценка занятости коек.")
    rows = table.loc[(table.previous >= 10) & (table.current >= 10) & (table.change_pct > 0)].sort_values("change_pct", ascending=False).head(3)
    if hospital:
        rows = table.loc[table.hospital.eq(hospital) & (table.previous >= 10) & (table.current >= 10)]
    if rows.empty:
        st.info("Нет роста с достаточным числом наблюдений для этого сравнения. Это не подтверждение отсутствия проблем.")
        return
    for row in rows.itertuples():
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{escape(str(row.hospital))}**")
            left.caption(f"{count(row.current)} направлений за последние 7 дней; ранее {count(row.previous)}. Изменение {number(row.change_pct)}%. Вопрос специалисту: изменился поток или полнота регистрации?")
            right.button("Открыть", key=f"attention_{row.hospital}", on_click=go_to, args=("Hospital explorer", row.hospital), width="stretch")


def heatmap(filters, selected=None, limit=15):
    st.subheader("Активность по неделям")
    grid = grid_data(db.file_version(ANALYTICAL_PATH), filters, tuple(selected) if selected else None, limit)
    if grid.empty:
        st.info("Нет организаций для выбранных фильтров.")
        return
    names = grid.hospital.drop_duplicates().tolist()
    weeks = sorted(grid.week.unique())
    values = grid.pivot(index="hospital", columns="week", values="referrals").reindex(index=names, columns=weeks)
    # Numbered compact labels stay unique even when organization names share a prefix.
    labels = [f"{i + 1:02d} · {name[:38]}{'…' if len(name) > 38 else ''}" for i, name in enumerate(names)]
    week_labels = [pd.Timestamp(w).strftime("%d.%m") + ("*" if bool(grid.loc[grid.week.eq(w), "partial_week"].any()) else "") for w in weeks]
    custom = [[str(name) for _ in weeks] for name in names]
    fig = go.Figure(go.Heatmap(z=values.to_numpy(), x=week_labels, y=labels, customdata=custom,
        colorscale=[[0, "#edf7f7"], [.35, "#92d0cc"], [.7, "#238e93"], [1, "#0b455e"]],
        xgap=3, ygap=3, hoverongaps=False, colorbar=dict(title="Напр."),
        hovertemplate="%{customdata}<br>Неделя с %{x}<br>Направлений: %{z:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    chart(fig, max(260, 31 * len(names) + 100))
    st.caption("Цвет = число зарегистрированных направлений. Серые пробелы скрывают группы из 1–9 записей; 0 означает отсутствие записей в файлах. * Неполная неделя на границе выбранного периода. Это не рейтинг качества или перегруженности.")
    if len(names) > 1:
        with st.expander("Полные названия и значения"):
            shown = grid.rename(columns={"hospital": "Стационар", "week": "Начало недели", "referrals": "Направления", "suppressed": "Малая группа скрыта", "partial_week": "Неполная неделя"})
            st.dataframe(shown, hide_index=True, width="stretch")


def executive_page(report, filters):
    title("MEDFLOW AI / ОБЗОР", "Потоки пациентов — в одном окне", "От общего объёма к организации, прогнозу и проверяемому решению.")
    context_strip(filters)
    stats = db.overview(filters)
    columns = st.columns(4)
    for col, label, value, help_text in zip(columns,
        ["Направления", "Стационары", "Медиана ожидания", "Госпитализации"],
        [count(stats["referrals"]), count(stats["hospitals"]), number(stats["median_wait"], " дн."), count(stats["hospitalized"])],
        ["Все направления выбранной когорты.", "Организации в выбранной когорте.", "Только допустимые наблюдённые госпитализации с ожиданием 0–90 дней.", "Известные корректные исходы; госпитализация могла произойти позже периода регистрации."]):
        col.metric(label, value, help=help_text)
    st.caption(f"Без записанного исхода: {count(stats['unresolved'])} · Отказы: {count(stats['refused'])} · Некорректные или конфликтующие исходы: {count(stats['conflicting'] + stats['invalid_outcome'])}. Отсутствие исхода не означает, что пациент ожидает сейчас.")
    if not stats["referrals"]:
        st.info("По этим фильтрам нет направлений. Измените период, регион или профиль.")
        return
    grid = grid_data(db.file_version(ANALYTICAL_PATH), filters, None, 6)
    left, right = st.columns([1.5, 1])
    with left, st.container(border=True):
        st.subheader("Ритм поступления направлений")
        if not grid.empty:
            # This chart explicitly concerns the six largest groups, not the national total.
            weekly = grid.groupby("week", as_index=False).agg(referrals=("referrals", lambda x: x.sum(min_count=len(x))))
            chart(px.area(weekly, x="week", y="referrals", labels={"week": "Неделя регистрации", "referrals": "Направления"}), 250)
            st.caption("Шесть крупнейших организаций по объёму в выбранной когорте. Недели с подавленными малыми группами не суммируются; крайние недели могут быть неполными.")
    with right, st.container(border=True):
        st.subheader("Быстрые действия")
        for index, (label, page) in enumerate(role_actions()):
            st.button(label, key=f"overview_action_{index}", on_click=go_to,
                      args=(page,), width="stretch", type="primary" if index == 0 else "secondary")
    attention(filters)
    heatmap(filters)


def hospital_page(report, filters, changed):
    title("MEDFLOW AI / СТАЦИОНАРЫ", "Карточка стационара", "История потока, профиль направлений и доступные прогнозы одной организации.")
    context_strip(filters)
    candidates = db.compare_groups(filters, minimum=10)
    names = candidates.organization_or_region.tolist()
    selected = hospital_picker("Медицинская организация", names, "hospital_picker")
    if selected is None:
        st.info("Нет организаций с минимум 10 направлениями по этим фильтрам.")
        return
    scope = {**filters, "hospital_mo": selected}
    row = candidates.loc[candidates.organization_or_region.eq(selected)].iloc[0]
    st.markdown(f"### {escape(selected)}")
    for col, label, value in zip(st.columns(4), ["Направления", "Медиана ожидания", "P90 ожидания", "Доля отказов"],
        [count(row.referrals), number(row.median_wait_days, " дн."), number(row.p90_wait_days, " дн."), number(row.refusal_share_pct, "%")]):
        col.metric(label, value)
    st.caption("Ожидание: минимум 10 допустимых госпитализаций. Доля отказов: отказы / (госпитализации + отказы), минимум 10 известных исходов. P90 — наблюдённый срок для 90% допустимых госпитализаций, не интервал прогноза.")
    a, b, c = st.columns(3)
    a.button("Сравнить стационар", on_click=go_to, args=("Compare & review", selected), width="stretch")
    b.button("Прогноз ожидания", on_click=go_to, args=("Waiting time prediction", selected), width="stretch")
    c.button("Прогноз потока на 7 дней", on_click=go_to, args=("7-day load forecast", selected), width="stretch")
    profiles = db.hospital_profiles(scope)
    left, right = st.columns([1.3, 1])
    with left, st.container(border=True):
        st.subheader("Наблюдаемые исходы")
        outcomes = pd.DataFrame({"Исход": ["Госпитализация", "Отказ", "Исход не записан", "Некорректный / конфликт"],
                                 "Направления": [row.hospitalized, row.refused, row.unresolved, row.excluded_outcomes]})
        chart(px.bar(outcomes, x="Направления", y="Исход", orientation="h"), 260)
        st.caption("Исходы известны из выгрузки и могут наступить позже выбранного периода регистрации.")
    with right, st.container(border=True):
        st.subheader("Профили направлений")
        st.dataframe(profiles.rename(columns={"profile": "Профиль", "referrals": "Направления", "eligible": "Допустимые исходы", "median_wait": "Медиана, дни"}), hide_index=True, width="stretch")
        st.caption("До восьми самых частых профилей. Пустая медиана — недостаточно допустимых исходов.")
    attention(scope, selected)
    heatmap(scope, [selected], 1)
    with st.container(border=True):
        st.subheader("Прогноз входящих направлений")
        st.caption("Используется вся доступная история организации по всем профилям и регионам. Фильтры когорты выше не изменяют модель и дату начала прогноза.")
        from src.load_forecast import forecast_status, forecast_next_week, METADATA_PATH as FORECAST_METADATA_PATH
        status = forecast_status(report)
        if changed or not status["available"]:
            st.info("Для прогноза нужны актуальные данные и модель. Проверьте раздел «Данные и модели».")
        else:
            try:
                future = forecast_next_week(selected)
                chart(px.line(future, x="date", y="predicted_referrals", markers=True,
                              labels={"date": "Дата прогноза", "predicted_referrals": "Направления"}), 250)
                meta = read_json(FORECAST_METADATA_PATH)
                st.caption(f"Историческая проекция: {future.date.min():%d.%m.%Y} — {future.date.max():%d.%m.%Y}. MAE сохранённой модели на всём тесте: {number(meta['metrics']['mae'])} направления на организацию в день.")
            except (ValueError, FileNotFoundError):
                st.info("Для этой организации пока нет подходящей истории прогноза.")


DEMO_STEPS = [
    ("Hospital explorer", "Сигнал", "Посмотрите изменение потока и исходы выбранного стационара."),
    ("Compare & review", "Сравнение", "Сопоставьте организации за один период и с одним фильтром профиля."),
    ("7-day load forecast", "Прогноз", "Покажите семидневный прогноз, исторические даты и измеренную ошибку."),
    ("Waiting time prediction", "Объяснение", "Нажмите «Рассчитать ожидание» и покажите вклады признаков в оценку."),
    ("Compare & review", "Отчёт", "Выберите вопрос специалисту, подтвердите просмотр и скачайте PDF."),
]


def start_demo():
    table = db.compare_groups({}, minimum=100)
    metadata = read_json(METADATA_PATH)
    options = metadata.get("feature_options", {}).get("hospital_mo", [])
    table = table.loc[table.organization_or_region.isin(options)]
    if table.empty:
        st.session_state["demo_unavailable"] = True
        return
    hospital = table.iloc[0].organization_or_region
    dims = db.dimensions()
    st.session_state["filter_region_origin_code"] = None
    st.session_state["filter_bed_profile"] = None
    st.session_state.pop("cohort_period", None)
    st.session_state["analysis_filters"] = {"start": pd.Timestamp(dims["dates"]["first"]).date(), "end": pd.Timestamp(dims["dates"]["last"]).date(), "bed_profile": None, "region_origin_code": None}
    st.session_state["comparison_mode"] = "Стационары"
    st.session_state["comparison_minimum"] = 100
    example = db.representative_profile(hospital, metadata.get("feature_options", {}))
    st.session_state["example_profile"] = example
    for key, value in example.items():
        st.session_state[f"predict_{key}"] = value
    st.session_state["demo_mode"] = True
    st.session_state["tour_step"] = 0
    st.session_state["tour_hospital"] = hospital
    go_to(DEMO_STEPS[0][0], hospital)


def move_demo(step):
    st.session_state["tour_step"] = step
    go_to(DEMO_STEPS[step][0], st.session_state["tour_hospital"])


def stop_demo():
    st.session_state.pop("tour_step", None)
    st.session_state.pop("tour_hospital", None)


def guided_banner(page):
    if "tour_step" not in st.session_state:
        return
    index = st.session_state["tour_step"]
    target, label, help_text = DEMO_STEPS[index]
    with st.container(border=True):
        st.markdown(f"**Демонстрация · {index + 1} / 5 · {label}**")
        st.progress((index + 1) / 5)
        st.caption(" → ".join(step[1] for step in DEMO_STEPS))
        st.write(help_text)
        st.caption(f"Пример: {st.session_state['tour_hospital']}")
        back, forward, exit_col = st.columns([1, 2, 1])
        back.button("Назад", disabled=index == 0, on_click=move_demo, args=(max(0, index - 1),), width="stretch")
        if page != target:
            forward.button("Вернуться к шагу", on_click=move_demo, args=(index,), width="stretch")
        elif index < len(DEMO_STEPS) - 1:
            forward.button("Следующий шаг", on_click=move_demo, args=(index + 1,), type="primary", width="stretch")
        else:
            forward.button("Завершить пример", on_click=stop_demo, type="primary", width="stretch")
        exit_col.button("Закрыть", on_click=stop_demo, width="stretch")
