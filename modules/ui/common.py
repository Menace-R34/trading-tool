import streamlit as st
from modules.prognose_auswertung import berechne_ticker_genauigkeit
from modules.intraday_timing import lade_intraday_timing_fuer_ticker

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


def _ergaenze_intraday_timing(df_target):
    if df_target is None or df_target.empty or "Ticker" not in df_target.columns:
        return df_target

    intraday_timing = lade_intraday_timing_fuer_ticker(df_target["Ticker"].unique())

    df_target = df_target.copy()
    df_target["Intraday Beste Kaufzeit"] = df_target["Ticker"].map(lambda t: intraday_timing.get(str(t).strip().upper(), {}).get("Intraday Beste Kaufzeit", ""))
    df_target["Intraday Beste Verkaufszeit"] = df_target["Ticker"].map(lambda t: intraday_timing.get(str(t).strip().upper(), {}).get("Intraday Beste Verkaufszeit", ""))
    df_target["Intraday Ø Haltedauer Min"] = df_target["Ticker"].map(lambda t: intraday_timing.get(str(t).strip().upper(), {}).get("Intraday Ø Haltedauer Min", 0))
    df_target["Intraday Ø Potenzial %"] = df_target["Ticker"].map(lambda t: intraday_timing.get(str(t).strip().upper(), {}).get("Intraday Ø Potenzial %", None))
    return df_target
