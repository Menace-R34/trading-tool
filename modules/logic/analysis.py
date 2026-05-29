import pandas as pd
import concurrent.futures
from modules.markt_daten import lade_kursdaten
from modules.markt_statistik import berechne_marktstatistik
from modules.saisonalitaet import berechne_saisonalitaet
from modules.news_modul import berechne_news_score
from modules.intraday_timing import lade_intraday_timing_fuer_ticker
from modules.logic.trading import bewerte_signale
from modules.markt_lage import berechne_marktlage

def _normalisiere_ticker(ticker):
    return str(ticker).strip().upper()

def _baue_land_mapping():
    from modules.universum import lade_trade_republic_universum
    mapping = {}
    df = lade_trade_republic_universum()
    if df.empty or "Ticker" not in df.columns or "Land" not in df.columns:
        return mapping
    for _, row in df.iterrows():
        ticker = str(row["Ticker"]).strip().upper()
        land = str(row["Land"]).strip()
        mapping[ticker] = land
    return mapping

def berechne_vollstaendige_analyse(ticker_liste, zeitraum):
    """
    Reine Logik-Funktion zur Berechnung aller Kennzahlen für eine Liste von Tickern.
    Unabhängig von Streamlit-Caching.
    """
    if not ticker_liste:
        return pd.DataFrame()

    daten = lade_kursdaten(
        ticker_liste=ticker_liste,
        zeitraum=zeitraum,
        intervall="1d"
    )

    if not daten:
        return pd.DataFrame()

    markt = berechne_marktlage()
    land_mapping = _baue_land_mapping()

    ergebnisse = []

    def process_ticker(ticker, df):
        statistik = berechne_marktstatistik(df, ticker)
        if statistik is None:
            return None

        ticker_clean = _normalisiere_ticker(ticker)
        land = land_mapping.get(ticker_clean, "")
        statistik["Land"] = land
        intraday = lade_intraday_timing_fuer_ticker([ticker_clean]).get(ticker_clean, {})
        statistik.update(intraday)

        saison = berechne_saisonalitaet(df)
        news = berechne_news_score(ticker_clean)
        signale = bewerte_signale(statistik, saison, news, markt=markt)

        return {**statistik, **saison, **news, **signale}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_ticker, ticker, df) for ticker, df in daten.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                ergebnisse.append(res)

    if not ergebnisse:
        return pd.DataFrame()

    df_res = pd.DataFrame(ergebnisse)
    
    # Numerische Konvertierung
    numerische_spalten = [
        "Letzter Kurs €", "Ø Tagesrange %", "Ø Tagesrange €", "Median Tagesrange %", 
        "Median Tagesrange €", "Volatilität %", "Hit-Rate > 2 %", "Hit-Rate > 3 %",
        "Tagesveränderung %", "Tagesveränderung €", "Abstand zum Hoch %", "Abstand zum Tief %",
        "ATR relativ %", "ATR 14 €", "Perf 20 Tage %", "RSI 14", "Saison-Score", "News-Score",
        "Day Score", "Swing Score", "Day Stop Loss €", "Day Take Profit €", "Day CRV",
        "Day Erwartung €", "Day Netto €", "Day Potenzial €", "Swing Stop Loss €",
        "Swing Take Profit €", "Swing CRV", "Swing Erwartung €", "Swing Netto €", "Swing Potenzial €",
        "Day Optimiert Trefferquote %", "Day Optimiert Ø Rendite %", "Day Optimiert Basis",
        "Swing Optimiert Trefferquote %", "Swing Optimiert Ø Rendite %", "Swing Optimiert Basis"
    ]
    for spalte in numerische_spalten:
        if spalte in df_res.columns:
            df_res[spalte] = pd.to_numeric(df_res[spalte], errors="coerce")

    return df_res
