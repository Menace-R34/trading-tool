import streamlit as st
from modules.prognose_speicher import lade_gespeicherte_standardwerte


def hole_standard_einstellungen():
    basis = {
        "analyse_zeitraum": "1y",
        "analyse_top_n": 10,
        "marktueberblick_nur_kandidaten": False,
        "signale_nur_kandidaten": True,
        "zeige_top_3_trades": True,

        "day_min_atr_rel": 1.8,
        "day_min_range": 1.5,
        "day_min_hitrate2": 30.0,
        "day_min_crv": 1.3,
        "day_min_potenzial": 5.0,
        "day_haltedauer": 3,

        "swing_min_crv": 1.5,
        "swing_min_potenzial": 10.0,
        "swing_min_rsi": 30,
        "swing_max_rsi": 75,
        "swing_haltedauer": 10,
        "auto_fix_aktiv": True,
        "auto_fix_offset_eu": 20,
        "auto_fix_offset_us": 20,
    }

    gespeichert = lade_gespeicherte_standardwerte()

    for key, value in gespeichert.items():
        if key in basis:
            basis[key] = value

    return basis


def initialisiere_einstellungen():
    standardwerte = hole_standard_einstellungen()

    for schluessel, wert in standardwerte.items():
        if schluessel not in st.session_state:
            st.session_state[schluessel] = wert


def setze_standard_einstellungen():
    standardwerte = hole_standard_einstellungen()
    for schluessel, wert in standardwerte.items():
        st.session_state[schluessel] = wert


def hole_filter_settings_aus_session():
    return {
        "day_min_atr_rel": st.session_state["day_min_atr_rel"],
        "day_min_range": st.session_state["day_min_range"],
        "day_min_hitrate2": st.session_state["day_min_hitrate2"],
        "day_min_crv": st.session_state["day_min_crv"],
        "day_min_potenzial": st.session_state["day_min_potenzial"],
        "day_haltedauer": st.session_state.get("day_haltedauer", 3),
        "swing_min_crv": st.session_state["swing_min_crv"],
        "swing_min_potenzial": st.session_state["swing_min_potenzial"],
        "swing_min_rsi": st.session_state["swing_min_rsi"],
        "swing_max_rsi": st.session_state["swing_max_rsi"],
        "swing_haltedauer": st.session_state.get("swing_haltedauer", 10),
    }