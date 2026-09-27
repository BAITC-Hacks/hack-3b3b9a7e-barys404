"""Stable page identifiers and shared hospital context for the Russian UI."""
import streamlit as st

PAGE_NAMES = {
    "Overview": "Обзор", "Hospital explorer": "Карточка стационара",
    "Compare & review": "Сравнение и отчёт", "Waiting time prediction": "Время ожидания",
    "7-day load forecast": "Поток на 7 дней", "Pressure & anomalies": "Сигналы и отклонения",
    "Model performance": "Качество модели", "Validation evidence": "Проверка по периодам",
    "Data quality": "Качество данных",
}

DEFAULT_ROLE = "hospital_lead"
ROLE_NAMES = {
    "hospital_lead": "Руководитель больницы",
    "department_lead": "Заведующий отделением",
    "admissions_specialist": "Специалист по госпитализации",
}

DEFAULT_HOSPITAL_TYPE = "multidisciplinary"
HOSPITAL_TYPE_NAMES = {
    "multidisciplinary": "Многопрофильная",
    "regional": "Областная",
    "city": "Городская",
    "district": "Районная",
    "specialized": "Специализированная",
}

# Every role can still reach every page. The role changes information priority,
# not authorization; production access control belongs outside this prototype.
SECTIONS = {
    "Обзор": ["Overview"],
    "Стационары": ["Hospital explorer", "Compare & review"],
    "Прогнозы": ["Waiting time prediction", "7-day load forecast"],
    "Сигналы": ["Pressure & anomalies"],
    "Данные и модели": ["Model performance", "Validation evidence", "Data quality"],
}

ROLE_SECTIONS = {
    "hospital_lead": SECTIONS,
    "department_lead": {
        "Моё отделение": ["Hospital explorer", "Waiting time prediction"],
        "Планирование": ["7-day load forecast", "Pressure & anomalies"],
        "Сводка": ["Overview", "Compare & review"],
        "Данные и модели": ["Model performance", "Validation evidence", "Data quality"],
    },
    "admissions_specialist": {
        "Госпитализация": ["Hospital explorer", "Waiting time prediction", "Pressure & anomalies"],
        "Планирование": ["7-day load forecast"],
        "Сводка": ["Overview", "Compare & review"],
        "Данные и модели": ["Model performance", "Validation evidence", "Data quality"],
    },
}

ROLE_ACTIONS = {
    "hospital_lead": [
        ("Открыть стационар", "Hospital explorer"),
        ("Прогноз потока", "7-day load forecast"),
        ("Проверить сигналы", "Pressure & anomalies"),
    ],
    "department_lead": [
        ("Открыть отделение", "Hospital explorer"),
        ("Проверить ожидание", "Waiting time prediction"),
        ("Посмотреть прогноз", "7-day load forecast"),
    ],
    "admissions_specialist": [
        ("Открыть направления", "Hospital explorer"),
        ("Рассчитать ожидание", "Waiting time prediction"),
        ("Проверить сигналы", "Pressure & anomalies"),
    ],
}


def current_role():
    role = st.session_state.get("user_role", DEFAULT_ROLE)
    return role if role in ROLE_NAMES else DEFAULT_ROLE


def current_hospital_type():
    value = st.session_state.get("hospital_type", DEFAULT_HOSPITAL_TYPE)
    return value if value in HOSPITAL_TYPE_NAMES else DEFAULT_HOSPITAL_TYPE


def sections_for_role(role=None):
    return ROLE_SECTIONS.get(role or current_role(), SECTIONS)


def role_actions(role=None):
    return ROLE_ACTIONS.get(role or current_role(), ROLE_ACTIONS[DEFAULT_ROLE])


def go_to(page, hospital=None):
    """Use as a widget callback, before the next page's widgets are constructed."""
    sections = sections_for_role()
    st.session_state["nav_section"] = next(section for section, pages in sections.items() if page in pages)
    st.session_state["nav_page"] = page
    if hospital is not None:
        st.session_state["active_hospital"] = hospital
        for key in ("hospital_picker", "forecast_hospital", "predict_hospital_mo", "pressure_hospital"):
            st.session_state[key] = hospital
        st.session_state.pop("comparison_groups_hospital_mo", None)


def hospital_picker(label, options, key):
    if not options:
        return None
    active = st.session_state.get("active_hospital")
    if key not in st.session_state or st.session_state[key] not in options:
        st.session_state[key] = active if active in options else options[0]
    value = st.selectbox(label, options, key=key)
    st.session_state["active_hospital"] = value
    return value
