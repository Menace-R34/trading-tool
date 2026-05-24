import streamlit as st
from modules.prognose_auswertung import berechne_ticker_genauigkeit

def _prepare_df(df_target):
    if df_target is None or df_target.empty:
        return df_target
        
    ticker_genauigkeiten = berechne_ticker_genauigkeit()
    
    df_target = df_target.copy()
    df_target["Hist. Prognosegenauigkeit %"] = df_target["Ticker"].map(lambda t: ticker_genauigkeiten.get(t, {}).get("Hist. Prognosegenauigkeit %", None))
    df_target["Anzahl Hist. Prognosen"] = df_target["Ticker"].map(lambda t: ticker_genauigkeiten.get(t, {}).get("Anzahl Hist. Prognosen", 0))
    df_target["Ø Endperformance %"] = df_target["Ticker"].map(lambda t: ticker_genauigkeiten.get(t, {}).get("Ø Endperformance %", None))
    df_target["Hist. Idealer Hold (Day)"] = df_target["Ticker"].map(lambda t: ticker_genauigkeiten.get(t, {}).get("Best Hold Day", 0))
    df_target["Hist. Idealer Hold (Swing)"] = df_target["Ticker"].map(lambda t: ticker_genauigkeiten.get(t, {}).get("Best Hold Swing", 0))
    return df_target
