"""Presentation layer for the historical MedFlow AI decision-support prototype."""
from datetime import date
from html import escape
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import (ANALYTICAL_PATH, DATA_DIR, METADATA_PATH, MODEL_PATH,
                        PROCESSED_DIR, QUALITY_PATH, ensure_directories)
from src import dashboard_data as db
from src.navigation import (DEFAULT_HOSPITAL_TYPE, DEFAULT_ROLE,
                            HOSPITAL_TYPE_NAMES, PAGE_NAMES, ROLE_NAMES,
                            current_hospital_type, current_role, hospital_picker,
                            sections_for_role)
from src.localization import LABELS, display_frame


COLORS = ["#087F8C", "#3969B3", "#E5A24A", "#9073BA"]
def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_uploaded_csvs(uploaded_files, raw_dir=None):
    """Atomically store new local CSVs without silently replacing a source."""
    raw_dir = Path(raw_dir or DATA_DIR / "raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    prepared, existing, conflicts = [], [], []
    for uploaded in uploaded_files:
        name = Path(uploaded.name).name
        if name != uploaded.name or Path(name).suffix.lower() != ".csv":
            raise ValueError(f"Недопустимое имя файла: {uploaded.name}")
        data = uploaded.getvalue()
        target = raw_dir / name
        if target.exists():
            if target.read_bytes() == data:
                existing.append(name)
            else:
                conflicts.append(name)
        else:
            prepared.append((target, data))
    if conflicts:
        return [], existing, conflicts
    saved = []
    for target, data in prepared:
        temporary = target.with_suffix(target.suffix + ".upload")
        temporary.write_bytes(data)
        os.replace(temporary, target)
        saved.append(target.name)
    return saved, existing, []


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
    return f"{int(value):,}".replace(",", " ") if pd.notna(value) else "—"


def number(value, suffix=""):
    return f"{float(value):,.2f}".replace(",", " ").replace(".", ",") + suffix if value is not None and pd.notna(value) else "—"


def chart(fig, height=320):
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=20, b=12), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#e5eaf0" if any(trace.type == "heatmap" for trace in fig.data) else "rgba(0,0,0,0)", font=dict(family="Arial", color="#40566B", size=14),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        colorway=COLORS, hovermode="x unified", separators=", ",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E6EDF4", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def theme():
    st.markdown("""<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1460px;}
    .context-strip {display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 24px;}
    .context-strip span {padding:7px 12px; border:1px solid #dce8ec; background:#eff6f7; border-radius:8px; font-size:13px; color:#31566a;}
    .role-chip {display:inline-flex; align-items:center; gap:7px; margin:-8px 0 22px; padding:6px 11px; border-radius:999px; background:#e9f5f4; color:#096c74; font-size:12px; font-weight:700;}
    .role-chip:before {content:""; width:7px; height:7px; border-radius:50%; background:#0c8991;}
    .data-status {display:flex; align-items:center; gap:8px; margin:4px 0 18px; padding:9px 11px; border-radius:9px; background:#f3f7f9; color:#466274; font-size:12px; font-weight:650;}
    .data-status.ready:before, .data-status.empty:before {content:""; width:8px; height:8px; border-radius:50%;}
    .data-status.ready:before {background:#168b70;}
    .data-status.empty:before {background:#d99a2b;}
    .empty-steps {display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:22px 0;}
    .empty-step {background:#fff; border:1px solid #dfe8ed; border-radius:14px; padding:18px; min-height:112px; box-shadow:0 5px 18px #173e550d;}
    .empty-step b {display:block; color:#0b7780; font-size:12px; letter-spacing:.08em; margin-bottom:8px;}
    .empty-step span {color:#17384b; font-size:16px; font-weight:700;}
    [data-testid="stMetric"] {box-shadow:0 3px 12px #173e5510; border-top:3px solid #168b94 !important;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
    [data-testid="stSidebar"] .stButton button {border-radius:9px;}
    [data-testid="stDataFrame"] {background:#fff;}
    .stButton button {min-height:42px;}
    @media (max-width:800px) { .block-container {padding:1rem;} h1 {font-size:1.8rem !important;} .empty-steps {grid-template-columns:1fr;} }
    [data-testid="stSidebar"] {border-right: 1px solid #e3eaf1;}
    [data-testid="stMetric"] {background:white; border:1px solid #e3eaf1; border-radius:12px; padding:18px 16px; min-height:122px;}
    [data-testid="stMetricLabel"] {font-size:14px; color:#60758a;}
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
    st.markdown(f'<div class="eyebrow">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(heading)
    st.markdown(f'<div class="intro">{escape(subtitle)}</div>', unsafe_allow_html=True)
    context = f"{ROLE_NAMES[current_role()]} · {HOSPITAL_TYPE_NAMES[current_hospital_type()]} больница"
    st.markdown(f'<div class="role-chip">{escape(context)}</div>', unsafe_allow_html=True)


def coverage_note(report):
    pieces = []
    for key, label in [("referrals", "Направления"), ("refusals", "Отдельные отказы")]:
        info = report.get("coverage", {}).get(key, {})
        available = len(info.get("available_parts", []))
        expected = info.get("expected_parts")
        if expected:
            pieces.append(f"{label}: {available}/{expected} частей")
    return " · ".join(pieces)


def sidebar(report, ready):
    with st.sidebar:
        st.markdown('<div class="brand">MEDFLOW <span>AI</span></div><div class="brand-sub">АНАЛИТИКА ГОСПИТАЛЬНЫХ ПОТОКОВ</div>', unsafe_allow_html=True)
        if st.session_state.get("user_role") not in ROLE_NAMES:
            st.session_state["user_role"] = DEFAULT_ROLE
        if st.session_state.get("hospital_type") not in HOSPITAL_TYPE_NAMES:
            st.session_state["hospital_type"] = DEFAULT_HOSPITAL_TYPE
        role = st.selectbox("Ваша роль", list(ROLE_NAMES), format_func=ROLE_NAMES.get, key="user_role")
        st.selectbox("Тип больницы", list(HOSPITAL_TYPE_NAMES), format_func=HOSPITAL_TYPE_NAMES.get, key="hospital_type")
        sections = sections_for_role(role)
        previous_role = st.session_state.get("_rendered_role")
        if previous_role != role or st.session_state.get("nav_section") not in sections:
            st.session_state["nav_section"] = next(iter(sections))
            st.session_state["nav_page"] = sections[st.session_state["nav_section"]][0]
        st.session_state["_rendered_role"] = role
        status_class, status_text = ("ready", "Данные готовы") if ready else ("empty", "Данные не подключены")
        st.markdown(f'<div class="data-status {status_class}">{status_text}</div>', unsafe_allow_html=True)
        section = st.radio("Раздел", list(sections), key="nav_section", label_visibility="collapsed")
        pages = sections[section]
        if st.session_state.get("nav_page") not in pages:
            st.session_state["nav_page"] = pages[0]
        if len(pages) > 1:
            page = st.radio("Страница", pages, format_func=PAGE_NAMES.get, key="nav_page", label_visibility="collapsed")
        else:
            page = pages[0]
        if ready:
            from src.experience import start_demo
            st.button("Показать пример", on_click=start_demo, width="stretch", type="primary")
        note = coverage_note(report)
        if note:
            st.caption(note)
        filters = dict(st.session_state.get("analysis_filters", {}))
        if ready and page in {"Overview", "Hospital explorer", "Compare & review"}:
            st.divider()
            st.markdown("**Фильтры**")
            dimensions = cached_dimensions(db.file_version(ANALYTICAL_PATH))
            for field, label in [("region_origin_code", "Регион происхождения"), ("bed_profile", "Профиль койки")]:
                if f"filter_{field}" not in st.session_state:
                    value = filters.get(field)
                    st.session_state[f"filter_{field}"] = value if value in dimensions[field] else None
                filters[field] = st.selectbox(label, [None, *dimensions[field]], format_func=lambda value: "Все" if value is None else value, key=f"filter_{field}")
            start, end = dimensions["dates"]["first"], dimensions["dates"]["last"]
            if pd.notna(start) and pd.notna(end):
                low, high = pd.Timestamp(start).date(), pd.Timestamp(end).date()
                initial = (max(low, min(high, pd.Timestamp(filters.get("start", low)).date())), max(low, min(high, pd.Timestamp(filters.get("end", high)).date())))
                selected = st.date_input("Период регистрации", initial, min_value=low, max_value=high, key="cohort_period", format="DD.MM.YYYY")
                st.session_state["invalid_period"] = not selected
                if isinstance(selected, (tuple, list)) and len(selected) == 2:
                    filters["start"], filters["end"] = selected
                elif isinstance(selected, (tuple, list)) and len(selected) == 1:
                    filters["start"] = filters["end"] = selected[0]
            st.session_state["analysis_filters"] = filters
            st.caption("Фильтры выбирают когорту по регистрации. Исходы могут наступить позже. Прогноз потока использует полную историю организации.")
        with st.expander("Данные и настройки"):
            st.session_state.setdefault("demo_mode", ready)
            st.toggle("Деморежим", key="demo_mode", help="Блокирует подготовку данных и обучение во время показа.")
            if ready:
                upload_sources("sidebar")
            refresh = st.button("Подготовить / обновить данные", width="stretch", disabled=st.session_state.get("demo_mode", False))
            st.caption("Исторические данные · прототип")
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
        with st.spinner("Читаем части выгрузки, проверяем качество и готовим аналитику…"):
            run_pipeline(force=False)
        st.cache_data.clear()
        st.rerun()
    except Exception as exc:
        st.error(f"Подготовка не завершилась: {type(exc).__name__}. Подробности доступны в локальном журнале.")
        import logging
        logging.getLogger(__name__).exception("Dashboard data preparation failed")


def upload_sources(key_prefix="main"):
    uploaded = st.file_uploader(
        "Загрузить CSV",
        type=["csv"],
        accept_multiple_files=True,
        key=f"{key_prefix}_source_upload",
        help="Можно выбрать все части выгрузок одновременно.",
    )
    if not uploaded:
        st.caption("Выберите выгрузки ожидающих и направлений. Остальные источники можно добавить вместе с ними.")
        return
    total_mb = sum(item.size for item in uploaded) / 1_000_000
    st.caption(f"Выбрано файлов: {len(uploaded)} · {total_mb:.1f} МБ")
    if not st.button("Загрузить и подготовить", key=f"{key_prefix}_upload_button", type="primary", width="stretch",
                     disabled=key_prefix == "sidebar" and st.session_state.get("demo_mode", False)):
        return
    try:
        ensure_directories()
        saved, existing, conflicts = save_uploaded_csvs(uploaded)
        if conflicts:
            st.error("Файлы с такими именами уже есть и отличаются: " + ", ".join(conflicts) + ". Переименуйте новые файлы.")
            return
        from src.data_loader import discover_files
        discovered = discover_files()
        missing = [label for category, label in (("waiting", "ожидающие"), ("referrals", "направления")) if not discovered[category]]
        if missing:
            st.success(f"Сохранено новых файлов: {len(saved)}. Уже были загружены: {len(existing)}.")
            st.warning("Для подготовки добавьте: " + " и ".join(missing) + ".")
            return
        prepare_data()
    except (OSError, ValueError) as exc:
        st.error(str(exc))


def empty_state():
    title("GOVTECH / КЕЙС 1", "Загрузите данные", "Выберите CSV-файлы — MedFlow проверит их и откроет рабочую сводку.")
    st.markdown("""<div class="empty-steps">
      <div class="empty-step"><b>01</b><span>Выберите CSV</span></div>
      <div class="empty-step"><b>02</b><span>Нажмите «Загрузить»</span></div>
      <div class="empty-step"><b>03</b><span>Откройте сводку</span></div>
    </div>""", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])
    with left:
        with st.container(border=True):
            upload_sources("empty")
    with right, st.expander("Запуск из терминала"):
        st.code("python -m src.preprocessing\npython -m src.train_waiting_model\nstreamlit run app.py", language="bash")


def model_training_control(changed):
    if changed:
        st.warning("CSV изменились. Обновите данные перед обучением или использованием модели.")
    if st.button("Обучить и проверить модель ожидания", disabled=changed or st.session_state.get("demo_mode", False), type="primary"):
        try:
            from src.train_waiting_model import train_model
            with st.spinner("Обучаем CatBoost и проверяем на более поздних регистрациях…"):
                train_model()
            st.cache_data.clear()
            st.rerun()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Dashboard model training failed")
            st.error("Обучение не завершилось. Подробности: `python -m src.train_waiting_model`.")


def prediction_page(report, changed):
    title("ПРОГНОЗ / ОЖИДАНИЕ", "Оценка времени ожидания", "Выберите профиль направления и получите оценку срока от регистрации до госпитализации.")
    metadata = read_json(METADATA_PATH)
    stale = changed or (bool(metadata) and metadata.get("source_fingerprint") != report.get("source_fingerprint"))
    st.info("Модель обучена на наблюдённых госпитализациях с ожиданием 0–90 дней. Оценка не определяет оставшееся время в очереди и не является медицинским назначением.")
    if not metadata or not MODEL_PATH.exists() or stale:
        if stale:
            st.warning("Сохранённая модель устарела. Обновите данные и переобучите её для получения прогноза.")
        else:
            st.info("Обученной модели пока нет. Запустите обучение на подготовленных данных.")
        model_training_control(changed)
        return
    options = metadata.get("feature_options", {})
    labels = {"hospital_mo": "Стационар", "icd10_ref_diag_code": "Код диагноза направления (МКБ-10)", "bed_profile": "Профиль койки", "territorial_type": "Территориальный тип", "referral_purpose": "Цель направления", "finance_source": "Источник финансирования"}
    with st.form("waiting_prediction"):
        left, right = st.columns(2)
        record = {}
        for index, (key, label) in enumerate(labels.items()):
            with (left if index % 2 == 0 else right):
                values = options.get(key, [])
                example = st.session_state.get("example_profile", {})
                if f"predict_{key}" not in st.session_state and example.get("hospital_mo") == st.session_state.get("active_hospital") and example.get(key) in values:
                    st.session_state[f"predict_{key}"] = example[key]
                if key == "hospital_mo":
                    record[key] = hospital_picker(label, values or ["Unknown"], key=f"predict_{key}")
                else:
                    record[key] = st.selectbox(label, values or ["Unknown"], key=f"predict_{key}")
        end = metadata.get("test_period", {}).get("end")
        selected_date = pd.Timestamp(end).date() if end else date.today()
        record["registration_dt"] = st.date_input("Дата регистрации", value=selected_date, format="DD.MM.YYYY")
        submit = st.form_submit_button("Рассчитать ожидание", type="primary")
    if submit:
        try:
            from src.explanations import explain_waiting
            explanation = explain_waiting(record)
            st.metric("Прогноз типичного ожидания", number(explanation["prediction"], " дн."))
            st.caption("Это оценка модели, а не гарантированная дата госпитализации.")
            st.caption(f"MAE на временном тесте: {number(metadata.get('metrics', {}).get('mae'))} дня. Средняя ошибка не является персональным интервалом прогноза.")
            st.subheader("Что повлияло на оценку?")
            if explanation["contributions"]:
                contributions = pd.DataFrame(explanation["contributions"])
                chart(px.bar(contributions.sort_values("contribution"), x="contribution", y="label", orientation="h",
                             color="contribution", color_continuous_scale="Tealrose",
                             labels={"contribution": "Вклад в оценку, дни", "label": ""}))
                st.caption(f"SHAP: базовое значение {number(explanation['base_value'])} дня + вклады признаков = {number(explanation['raw_prediction'])} дня. Это связи внутри модели, не доказанные причины.")
            else:
                st.info(f"Основа оценки: медиана завершённых случаев из обучающей истории ({explanation['method']}, {explanation['support']} случаев, до {explanation['training_cutoff']}). Диагноз и дата не меняют эту групповую оценку.")
            if explanation["unseen_categories"]:
                st.warning("Некоторые категории не встречались при обучении; надёжность такой оценки не установлена.")
            st.info("Перед обсуждением со специалистом проверьте профиль, период данных и ошибку модели. Прогноз не назначает дату госпитализации и не маршрутизирует пациента.")
            if end and pd.Timestamp(record["registration_dt"]) > pd.Timestamp(end):
                st.warning("Дата выходит за период проверки. Качество на будущих датах ещё не установлено.")
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Dashboard prediction failed")
            st.error("Не удалось рассчитать прогноз. Проверьте соответствие сохранённой модели текущим данным.")
    with st.expander("Как понимать прогноз"):
        st.write("Обучение использует завершённые корректные госпитализации. У отказов, незавершённых и некорректных записей нет такого целевого срока; их ожидание может отличаться. Списки категорий взяты из обучения.")
        st.write("CatBoost с функцией ошибки MAE оценивает типичное ожидание — условную медиану. Сравнение с простым прогнозом по исторической медиане доступно на странице «Качество модели».")


def performance_page(report, changed):
    title("МОДЕЛИ / КАЧЕСТВО", "Проверка качества модели ожидания", "Результаты сохранённой модели на более поздних регистрациях. Повторные проверки доступны на соседней странице.")
    meta = read_json(METADATA_PATH)
    if not meta:
        st.info("Обучите модель ожидания, чтобы увидеть измеренные показатели.")
        model_training_control(changed)
        return
    if changed or meta.get("source_fingerprint") != report.get("source_fingerprint"):
        st.warning("Метрики относятся к предыдущей версии данных. Обновите данные и модель перед использованием результатов.")
    metrics = meta.get("metrics", {})
    for col, (label, key, suffix) in zip(st.columns(4), [("Средняя ошибка, MAE", "mae", " дн."), ("Ошибка с весом больших промахов, RMSE", "rmse", " дн."), ("MAE простого прогноза", "baseline_mae", " дн."), ("Снижение MAE", "improvement_pct", "%")]):
        col.metric(label, number(metrics.get(key), suffix))
    improvement = metrics.get("improvement_pct")
    if improvement is not None and improvement < 0:
        st.warning("На этом периоде MAE модели выше, чем у исторической медианы. Этот результат не показывает преимущество модели.")
    st.caption("MAE — средняя абсолютная ошибка в днях. RMSE сильнее учитывает большие ошибки. Снижение = (MAE простого прогноза − MAE модели) / MAE простого прогноза × 100%.")
    train, test = meta.get("train_period", {}), meta.get("test_period", {})
    rows = meta.get("rows", {})
    with st.container(border=True):
        st.subheader("Ранние даты — обучение. Поздние — проверка.")
        st.write(f"**Обучение:** {train.get('start', '—')} → {train.get('end', '—')} · **{count(rows.get('train'))}** записей")
        st.write(f"**Тест:** {test.get('start', '—')} → {test.get('end', '—')} · **{count(rows.get('test'))}** записей")
        st.caption("Разделение по дате регистрации. Даты исходов используются для целевого срока и проверки доступности исходов к моменту обучения.")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Наблюдение и прогноз")
        st.caption("Группы тестовых наблюдений по сроку ожидания. Группы меньше 10 записей скрыты.")
        points = pd.DataFrame(meta.get("actual_vs_predicted", []))
        if not points.empty and {"actual_mean", "predicted_mean", "count"}.issubset(points.columns):
            fig = px.scatter(points, x="actual_mean", y="predicted_mean", size="count", color_discrete_sequence=COLORS, labels={"actual_mean": "Среднее наблюдаемое ожидание, дни", "predicted_mean": "Средний прогноз, дни", "count": "Записи"})
            bound = max(points["actual_mean"].max(), points["predicted_mean"].max())
            fig.add_trace(go.Scatter(x=[0, bound], y=[0, bound], mode="lines", line=dict(color="#9AA9B9", dash="dash"), name="Точное совпадение", hoverinfo="skip"))
            chart(fig)
        else:
            st.info("Нет достаточно крупных групп для графика.")
    with right, st.container(border=True):
        st.subheader("Важность признаков CatBoost")
        st.caption("Относится только к ветке CatBoost для редкой истории, не к групповым медианам. Причинность не установлена.")
        importance = pd.DataFrame(meta.get("feature_importance", []))
        if not importance.empty and {"feature", "importance"}.issubset(importance.columns):
            from src.explanations import FEATURE_LABELS
            importance["feature"] = importance["feature"].map(lambda value: FEATURE_LABELS.get(value, value))
            chart(px.bar(importance.sort_values("importance").tail(12), x="importance", y="feature", orientation="h", color_discrete_sequence=COLORS, labels={"importance": "Важность", "feature": ""}))
    with st.expander("Подробности обучения и ограничения", expanded=False):
        st.write("Проверка относится к историческим завершённым госпитализациям. Незавершённые случаи создают смещение отбора; большие ошибки остаются существенными. Внешняя проверка и интервалы неопределённости ещё нужны. Ниже — исходный технический отчёт.")
        st.json(meta, expanded=False)
    model_training_control(changed)


def forecast_page(report, changed):
    title("ПРОГНОЗ / ВХОДЯЩИЙ ПОТОК", "Направления на семь дней", "Одна организация, семь прогнозных дней, измеренная ошибка на историческом периоде.")
    st.warning("Прогнозируется число входящих направлений. Данные не позволяют оценить занятость коек, доступность персонала или актуальную очередь.")
    path = PROCESSED_DIR / "hospital_day.parquet"
    if not path.exists():
        st.info("Подготовьте направления перед обучением прогноза.")
        return
    from src.load_forecast import METADATA_PATH as FORECAST_METADATA_PATH, forecast_status
    metadata = read_json(FORECAST_METADATA_PATH)
    status = forecast_status(report)
    if changed or not status["available"]:
        st.info("Источники изменились. Сначала обновите данные." if changed else "Актуальная модель прогноза недоступна. Проверьте данные и обучите модель.")
        if st.button("Обучить и проверить прогноз потока", disabled=changed or st.session_state.get("demo_mode", False), type="primary"):
            try:
                from src.load_forecast import train_load_forecast
                with st.spinner("Обучаем семидневный прогноз на истории организаций…"):
                    train_load_forecast()
                st.cache_data.clear()
                st.rerun()
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Load forecast training failed")
                st.error("Обучение не завершилось. Проверьте данные и журнал; для обучения и проверки нужны минимум 42 дня.")
        return
    metrics = metadata.get("metrics", {})
    for column, (label, key, suffix) in zip(st.columns(4), [("Средняя ошибка, MAE", "mae", " напр."), ("Ошибка RMSE", "rmse", " напр."), ("MAE среднего за 7 дней", "baseline_mae", " напр."), ("Снижение MAE", "improvement_pct", "%")]):
        column.metric(label, number(metrics.get(key), suffix))
    split = metadata.get("split", {})
    st.caption(f"Тест: {metadata['test_period']['start'][:10]} — {metadata['test_period']['end'][:10]}. Все семь дней прогнозируются из конца {split['forecast_origin'][:10]}, только по доступной к этой дате истории. MAE измеряется в направлениях на организацию в день.")
    st.caption(f"MAE прогноза по тому же дню прошлой недели: {number(metrics.get('seasonal_baseline_mae'))}. Проверено организаций: {count(split['test_hospitals'])}; исключено из-за недостаточной истории: {count(split['excluded_test_hospitals'])}.")
    if metrics.get("improvement_pct") is not None and metrics["improvement_pct"] < 0:
        st.warning("На этом тесте модель не превзошла среднее за предыдущие 7 дней.")
    if metrics.get("seasonal_baseline_mae") is not None and metrics["mae"] > metrics["seasonal_baseline_mae"]:
        st.warning("На этом тесте прогноз по тому же дню прошлой недели оказался лучше модели.")
    weaker_horizons = [str(row["horizon"]) for row in metadata.get("metrics_by_horizon", []) if row["mae"] > row["baseline_mae"]]
    if weaker_horizons:
        st.caption(f"Среднее за предыдущие 7 дней оказалось лучше модели на горизонтах: {', '.join(weaker_horizons)}. Подробности ниже.")
    with st.expander("Ошибка по дням горизонта"):
        st.dataframe(display_frame(pd.DataFrame(metadata.get("metrics_by_horizon", []))), hide_index=True, width="stretch")
    hospitals = db.aggregate_query(path, "SELECT hospital_mo FROM read_parquet(?) GROUP BY hospital_mo ORDER BY sum(referrals) DESC, hospital_mo")["hospital_mo"].dropna().astype(str).tolist()
    if not hospitals:
        st.info("Организации с историей направлений не найдены.")
        return
    selected = hospital_picker("Стационар", hospitals, key="forecast_hospital")
    try:
        from src.load_forecast import forecast_next_week
        forecast = forecast_next_week(selected)
        history = db.pressure_rows(path, hospital=selected).sort_values("date").tail(28)
    except (ValueError, FileNotFoundError):
        st.info("Для прогноза этой организации нужны минимум 28 наблюдённых дней.")
        return
    total = float(forecast["predicted_referrals"].sum())
    st.metric("Прогноз направлений за 7 дней", number(total))
    st.caption(f"Историческая проекция: {forecast['date'].min():%d.%m.%Y} — {forecast['date'].max():%d.%m.%Y}, после последнего наблюдения {metadata['history_end'][:10]}. Это не прогноз на текущую календарную неделю.")
    with st.container(border=True):
        observed = history.loc[:, ["date", "referrals"]].rename(columns={"referrals": "records"}).assign(series="Наблюдаемые направления")
        projected = forecast.rename(columns={"predicted_referrals": "records"}).assign(series="Прогноз")
        chart(px.line(pd.concat([observed, projected]), x="date", y="records", color="series", markers=True, color_discrete_sequence=[COLORS[0], COLORS[2]], labels={"date": "Дата", "records": "Направления", "series": ""}))
    values = forecast.assign(predicted_referrals=forecast["predicted_referrals"].round(1)).rename(columns={"date": "Дата прогноза", "predicted_referrals": "Прогноз направлений"})
    st.dataframe(values, hide_index=True, width="stretch")
    with st.expander("Объяснение прогноза выбранного дня"):
        horizon = st.select_slider("День горизонта", options=list(range(1, 8)), value=1)
        from src.load_forecast import explain_next_week
        explanation = explain_next_week(selected, horizon)
        contributions = pd.DataFrame(explanation["contributions"])
        chart(px.bar(contributions.sort_values("contribution"), x="contribution", y="label", orientation="h",
                     labels={"contribution": "Вклад в прогноз, направлений", "label": ""}))
        st.caption(f"Базовое значение {number(explanation['base_value'])} + вклады = {number(explanation['raw_prediction'])} до коррекции отрицательных значений. История заканчивается {metadata['history_end'][:10]}. Причинность не установлена.")
    with st.expander("Область применения и ограничения"):
        st.write("Прогноз описывает входящие направления. История короткая; нулевые дни означают отсутствие записей в файлах. Актуальная очередь и занятость коек неизвестны. Полный технический отчёт приведён ниже.")
        st.json(metadata, expanded=False)


def pressure_cohort():
    path = PROCESSED_DIR / "hospital_day.parquet"
    if not path.exists():
        st.info("Дневные показатели организаций пока не подготовлены. Выполните `python -m src.aggregation` после подготовки данных.")
        return
    st.caption("Здесь выбираются организация и даты событий. Фильтры региона и профиля из обзора не применяются.")
    values = db.aggregate_query(path, "SELECT hospital_mo FROM read_parquet(?) GROUP BY hospital_mo ORDER BY sum(referrals) DESC, hospital_mo")["hospital_mo"].dropna().tolist()
    selected = hospital_picker("Стационар для мониторинга", values, "pressure_hospital")
    if not selected:
        st.info("Нет дневных показателей для этой организации.")
        return
    try:
        rows = db.pressure_rows(path, hospital=selected).sort_values("date")
    except duckdb_error_types():
        st.info("Формат дневных показателей устарел. Пересоберите их командой `python -m src.aggregation`.")
        return
    if rows.empty:
        st.info("Для этой организации нет дневных записей.")
        return
    low, high = pd.Timestamp(rows["date"].min()).date(), pd.Timestamp(rows["date"].max()).date()
    selected_dates = st.date_input("Исторические даты событий", (low, high), min_value=low, max_value=high, key="pressure_dates", format="DD.MM.YYYY")
    if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
        rows = rows.loc[(pd.to_datetime(rows["date"]).dt.date >= selected_dates[0]) & (pd.to_datetime(rows["date"]).dt.date <= selected_dates[1])]
    if rows.empty:
        st.info("В этом интервале нет записей.")
        return
    last = rows.iloc[-1]
    st.caption(f"Индикатор на {pd.Timestamp(last['date']):%d.%m.%Y} · Только историческая когорта")
    cols = st.columns(3)
    cols[0].metric("Индикатор активности", {"HIGH": "Высокий", "MEDIUM": "Средний", "LOW": "Низкий", "INSUFFICIENT_HISTORY": "Мало истории"}.get(str(last["prototype_pressure"]), "Нет оценки"))
    cols[1].metric("Восстановленная открытая когорта", count(last["reconstructed_open_cohort"]))
    cols[2].metric("Направления за день", count(last["referrals"]))
    st.warning("Индикатор ещё не проверен во внешнем пилоте. Открытая когорта восстановлена из доступных регистраций и известных выходов; она не равна занятости коек или очереди на сегодня.")
    st.caption("Сравнение с предыдущими 28 днями при наличии хотя бы 14 дней истории: выше 95-го перцентиля — высокий уровень, выше 75-го — средний.")
    with st.container(border=True):
        melted = rows.melt(id_vars=["date"], value_vars=["referrals", "hospitalized", "refusals"], var_name="event", value_name="records")
        melted["event"] = melted["event"].map({"referrals": "Направления", "hospitalized": "Госпитализации", "refusals": "Отказы"})
        chart(px.line(melted, x="date", y="records", color="event", color_discrete_sequence=COLORS, labels={"date": "Дата события", "records": "Записи", "event": ""}))
    with st.container(border=True):
        st.subheader("Восстановленная открытая когорта")
        chart(px.area(rows, x="date", y="reconstructed_open_cohort", color_discrete_sequence=COLORS, labels={"date": "Дата события", "reconstructed_open_cohort": "Наблюдаемые открытые направления"}), 250)
    anomaly_columns = [c for c in rows if c.startswith("anomaly_")]
    alerts = rows.loc[rows[anomaly_columns].any(axis=1), ["date", "referrals", "refusals", "reconstructed_open_cohort", *anomaly_columns]] if anomaly_columns else pd.DataFrame()
    st.subheader("Статистические отклонения")
    st.caption("Сигналы сравнивают активность с предыдущими наблюдениями. Они требуют проверки специалистом и сами по себе не доказывают перегрузку.")
    if alerts.empty:
        st.info("Для организации и периода нет отмеченных отклонений.")
    else:
        st.dataframe(display_frame(alerts.sort_values("date", ascending=False).head(100)), hide_index=True, width="stretch")
    with st.expander("Правила расчёта индикатора"):
        indicator = read_json(PROCESSED_DIR / "aggregation_summary.json").get("indicator", {})
        if indicator:
            st.json(indicator)
        else:
            st.caption("Перцентили и отклонения рассчитаны только по предыдущим наблюдениям. Недостаточная история помечается отдельно.")


def independent_refusals():
    st.subheader("Отдельная выгрузка отказов")
    st.caption("Отказы приёмного покоя из самостоятельного источника. Связь с направлениями не установлена; названия регионов и организаций относятся к этой выгрузке.")
    path = PROCESSED_DIR / "refusals.parquet"
    if not path.exists():
        st.info("Отдельная выгрузка отказов недоступна.")
        return
    options = db.aggregate_query(path, "SELECT DISTINCT region_in FROM read_parquet(?) WHERE region_in IS NOT NULL ORDER BY region_in")["region_in"].tolist()
    organizations = db.aggregate_query(path, "SELECT DISTINCT org_in FROM read_parquet(?) WHERE org_in IS NOT NULL ORDER BY org_in")["org_in"].tolist()
    left, right = st.columns(2)
    region = left.selectbox("Регион в выгрузке отказов", [None, *options], format_func=lambda value: "Все" if value is None else value)
    organization = right.selectbox("Организация в выгрузке отказов", [None, *organizations], format_func=lambda value: "Все" if value is None else value)
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
        st.info("По этим фильтрам нет отказов с известной датой.")
        return
    start, end = pd.Timestamp(daily["date"].min()).date(), pd.Timestamp(daily["date"].max()).date()
    selected = st.date_input("Даты отказов", (start, end), min_value=start, max_value=end, key="refusal_feed_dates")
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        daily = daily.loc[(pd.to_datetime(daily["date"]).dt.date >= selected[0]) & (pd.to_datetime(daily["date"]).dt.date <= selected[1])]
    st.metric("Отказы с известной датой", count(daily["refusals"].sum()))
    chart(px.bar(daily, x="date", y="refusals", color_discrete_sequence=[COLORS[2]], labels={"date": "Дата отказа", "refusals": "Записи"}))
    st.caption("Показаны события с известной датой. Их нельзя складывать с отказами в направлениях: пересечение источников неизвестно.")


def treated_context():
    st.subheader("Пролеченные случаи по организациям")
    st.caption("Самостоятельная агрегированная выгрузка. Дата загрузки не определяет отчётный период; эти данные не измеряют мощность стационара и не входят во временные признаки 2025 года.")
    path = PROCESSED_DIR / "treated.parquet"
    if not path.exists():
        st.info("Выгрузка пролеченных случаев недоступна.")
        return
    totals = db.aggregate_query(path, """SELECT count(*) AS source_rows,
        count(DISTINCT medicine_organization) AS organizations,
        min(sdu_load_date) AS earliest_load, max(sdu_load_date) AS latest_load
        FROM read_parquet(?)""").iloc[0]
    left, right = st.columns(2)
    left.metric("Агрегированные записи", count(totals["source_rows"]))
    right.metric("Организации в источнике", count(totals["organizations"]))
    st.caption(f"Даты загрузки источника: {totals['earliest_load']} → {totals['latest_load']}")
    values = db.aggregate_query(path, """SELECT medicine_organization AS organization,
        count(*) AS source_records, sum(discharged_total) AS reported_discharges,
        sum(bed_days) AS reported_bed_days
        FROM read_parquet(?) GROUP BY medicine_organization
        ORDER BY reported_discharges DESC NULLS LAST LIMIT 20""")
    st.dataframe(display_frame(values), hide_index=True, width="stretch")
    st.caption("До 20 организаций по сумме указанных выписок. Периоды записей могут пересекаться. Названия организаций между источниками не сопоставлялись.")


def pressure_page():
    title("МОНИТОРИНГ / СИГНАЛЫ", "Сигналы и отклонения", "Изменения активности и проверяемые статистические правила.")
    st.info("Прогноз входящих направлений доступен в разделе «Прогнозы». Для занятости коек, мощности и горизонтов 30/90 дней нужны дополнительные данные и проверка.")
    cohort, refusal, treated = st.tabs(["Когорта направлений", "Отдельные отказы", "Пролеченные случаи"])
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
    title("ДАННЫЕ / КАЧЕСТВО", "Качество и происхождение данных", "Покрытие источников, очистка, проверка дат и результатов соединения.")
    note = coverage_note(report)
    if note:
        st.info(note)
    datasets = report.get("datasets", {})
    inventory = []
    for category, details in datasets.items():
        inventory.append({"Источник": LABELS.get(category, category), "Строки": details.get("rows"), "Столбцы": len(details.get("columns", [])), "Стационары": details.get("unique_hospitals"), "Регионы": details.get("unique_regions"), "Коды диагнозов": details.get("unique_diagnoses")})
    if inventory:
        st.dataframe(pd.DataFrame(inventory), hide_index=True, width="stretch")
    join = report.get("join", {})
    if join:
        st.subheader("Связь ожидающих с направлениями")
        cols = st.columns(3)
        cols[0].metric("Связанные направления", count(join.get("matched_rows")))
        rate = join.get("match_rate")
        cols[1].metric("Доля совпадений", number(float(rate) * 100, "%") if rate is not None else "—")
        cols[2].metric("Неоднозначные ключи ожидающих", count(join.get("waiting_ambiguous_keys")))
        st.caption("Соединение выполнено по описанному составному ключу. Неоднозначности и конфликты учтены в аудите. Идентификаторы в интерфейс не выводятся.")
    for category, details in datasets.items():
        with st.expander(f"{LABELS.get(category, category)} · технические проверки качества"):
            st.write("**Столбцы:** " + ", ".join(details.get("columns", [])))
            dates = details.get("dates", {})
            if dates:
                st.dataframe(pd.DataFrame.from_dict(dates, orient="index").rename_axis("Поле даты").reset_index(), hide_index=True, width="stretch")
            missing = details.get("missing_values", {})
            if missing:
                st.dataframe(pd.DataFrame([{"Поле": key, "Пропуски": value} for key, value in missing.items()]), hide_index=True, width="stretch")
    with st.expander("Аудит очистки и исключений", expanded=True):
        st.json(report.get("cleaning", {}), expanded=False)
    st.caption("Для отдельных отказов нет проверенного ключа связи с направлениями. Пролеченные случаи имеют другую временную основу. Оба источника исключены из временных признаков моделей.")
    with st.expander("Полный агрегированный отчёт качества"):
        st.json(report, expanded=False)
    st.download_button("Скачать отчёт качества", json.dumps(report, ensure_ascii=False, indent=2), "medflow_data_quality.json", "application/json")
    with st.expander("Все локальные файлы и лабораторные данные"):
        from src.workbench import source_inventory
        source_inventory()


def main():
    st.set_page_config(page_title="MedFlow AI · Госпитальные потоки", page_icon="✚", layout="wide", initial_sidebar_state="expanded")
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
            st.caption("CSV найдены. Подготовьте данные через боковую панель.")
        return
    if changed:
        st.warning("Исходные файлы изменились. Аналитика относится к предыдущей версии; обновите данные перед использованием прогнозов и отчётов.")
    from src.experience import executive_page, hospital_page, guided_banner
    guided_banner(page)
    if page in {"Overview", "Hospital explorer", "Compare & review"} and st.session_state.get("invalid_period"):
        st.info("Выберите период регистрации в боковой панели.")
        return
    if st.session_state.pop("demo_unavailable", False):
        st.info("Для примера нужна организация с достаточной историей и обученная модель ожидания.")
    if page == "Overview":
        executive_page(report, filters)
    elif page == "Hospital explorer":
        hospital_page(report, filters, changed)
    elif page == "Compare & review":
        from src.workbench import comparison_page
        comparison_page(report, changed, filters)
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
    st.caption("MEDFLOW AI · Кейс 1 · Историческая управленческая аналитика · Агрегированные данные")
