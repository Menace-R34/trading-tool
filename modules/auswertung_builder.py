import pandas as pd
import streamlit as st
from modules.logic.analysis import berechne_vollstaendige_analyse
from modules.markt_zeit import bestimme_handelsfenster

@st.cache_data(show_spinner=False)
def _cached_baue_auswertung_fuer_ticker(ticker_liste, zeitraum, v="1.3"):
    """
    Wrapper für die Logik-Funktion mit Streamlit-Caching.
    """
    return berechne_vollstaendige_analyse(ticker_liste, zeitraum)

def baue_auswertung_fuer_ticker(ticker_liste, zeitraum):
    """
    Öffentliche API für die UI. Ergänzt dynamische Werte wie das Handelsfenster.
    """
    df = _cached_baue_auswertung_fuer_ticker(ticker_liste, zeitraum)
    if not df.empty:
        df = df.copy()
        if "Land" in df.columns:
            df["Handelsfenster"] = df["Land"].apply(bestimme_handelsfenster)
    return df