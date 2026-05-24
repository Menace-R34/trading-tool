import streamlit as st
from modules.ui_einstellungen import initialisiere_einstellungen, hole_filter_settings_aus_session
from modules.ui_navigation import erstelle_navigation
from modules.ui.dashboard import seite_start
from modules.ui.analyse import (
    seite_marktueberblick,
    seite_signale,
    seite_europa_aktien,
    seite_usa_aktien
)
from modules.ui.verwaltung import (
    seite_prognosekontrolle,
    seite_einstellungen
)
from modules.ui_hilfe import seite_hilfe
from modules.universum import hole_tickerliste_aus_universum
from modules.auswertung_builder import baue_auswertung_fuer_ticker
from modules.logic.automation import start_background_worker

# =========================================================
# 00_SYSTEM_START
# =========================================================
@st.cache_resource
def system_start_init():
    """Wird einmalig beim Start des Streamlit-Servers ausgeführt."""
    start_background_worker()
    return True

system_start_init()

st.set_page_config(page_title="Trading Tool", layout="wide")


def main():
    st.title("Trading Tool")
    initialisiere_einstellungen()
    
    from modules.prognose_auswertung import fuehre_tagespruefung_aus
    from modules.logic.automation import fuehre_automatische_fixierung_aus
    fuehre_tagespruefung_aus(st.session_state)
    fuehre_automatische_fixierung_aus(st.session_state)

    # --- GLOBALER FIX-TRIGGER ---
    if st.session_state.get("fixiere_prognosen_trigger"):
        st.session_state["fixiere_prognosen_trigger"] = False
        with st.sidebar:
            with st.spinner("Fixiere alle Prognosen..."):
                t_liste = hole_tickerliste_aus_universum()
                df_fix = baue_auswertung_fuer_ticker(tuple(t_liste), st.session_state["analyse_zeitraum"])
                speichere_prognosen(df_fix, hole_filter_settings_aus_session())
                st.success("Prognosen fixiert!")
                st.rerun()

    auswahl = erstelle_navigation()

    if auswahl == "Start":
        seite_start()
    elif auswahl == "Marktüberblick":
        seite_marktueberblick()
    elif auswahl == "Signale":
        seite_signale()
    elif auswahl == "Europa Aktien":
        seite_europa_aktien()
    elif auswahl == "USA Aktien":
        seite_usa_aktien()
    elif auswahl == "Prognosekontrolle":
        seite_prognosekontrolle()
    elif auswahl == "Einstellungen":
        seite_einstellungen()
    elif auswahl == "Hilfe":
        seite_hilfe()


if __name__ == "__main__":
    main()