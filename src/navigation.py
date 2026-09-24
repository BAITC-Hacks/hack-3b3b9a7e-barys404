"""Stable page identifiers and shared hospital context for the Russian UI."""
import streamlit as st

PAGE_NAMES = {
    "Overview": "Обзор", "Hospital explorer": "Карточка стационара",
    "Compare & review": "Сравнение и отчёт", "Waiting time prediction": "Время ожидания",
    "7-day load forecast": "Поток на 7 дней", "Pressure & anomalies": "Сигналы и отклонения",
    "Model performance": "Качество модели", "Validation evidence": "Проверка по периодам",
    "Data quality": "Качество данных",
}
SECTIONS = {
    "Обзор": ["Overview"],
    "Стационары": ["Hospital explorer", "Compare & review"],
    "Прогнозы": ["Waiting time prediction", "7-day load forecast"],
    "Сигналы": ["Pressure & anomalies"],
    "Данные и модели": ["Model performance", "Validation evidence", "Data quality"],
}


def go_to(page, hospital=None):
    """Use as a widget callback, before the next page's widgets are constructed."""
    st.session_state["nav_section"] = next(section for section, pages in SECTIONS.items() if page in pages)
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
