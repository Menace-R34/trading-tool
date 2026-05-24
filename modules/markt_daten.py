# =========================================================
# 01_IMPORTS
# =========================================================
import pandas as pd
import yfinance as yf
import streamlit as st


# =========================================================
# 02_HILFSFUNKTION_SPALTENBEREINIGUNG
# =========================================================
def _hole_preisserie(df, spaltenname):
    """
    Gibt eine Preisserie aus einem DataFrame zurück.
    Unterstützt normale und mehrstufige Spalten.
    """
    if spaltenname not in df.columns:
        passende_spalten = [col for col in df.columns if isinstance(col, tuple) and col[0] == spaltenname]
        if not passende_spalten:
            return pd.Series(dtype="float64")
        serie = df[passende_spalten[0]]
    else:
        serie = df[spaltenname]

    if isinstance(serie, pd.DataFrame):
        serie = serie.iloc[:, 0]

    return serie.dropna()


# =========================================================
# 03_KURSDATEN_LADEN
# =========================================================
import concurrent.futures

import os
import time
from pathlib import Path

CACHE_DIR = Path("data/cache_kurse")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def lade_kursdaten(ticker_liste, zeitraum="1y", intervall="1d"):
    """
    Lädt Kursdaten für eine Liste von Tickern parallel.
    Nutzt einen lokalen Parquet-Cache (8 Stunden gültig), um 
    Neustarts erheblich zu beschleunigen.

    Rückgabe:
        dict: {Ticker: DataFrame}
    """
    daten = {}

    def fetch(ticker):
        cache_file = CACHE_DIR / f"{ticker}_{zeitraum}_{intervall}.parquet"
        
        # Cache prüfen (gültig für 8 Stunden)
        if cache_file.exists():
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600 * 8:
                try:
                    df = pd.read_parquet(cache_file)
                    df = rechne_df_in_eur_um(df, ticker)
                    return ticker, df
                except Exception:
                    pass # Fallback auf Download

        # Download falls Cache ungültig oder nicht vorhanden
        try:
            df = yf.download(
                tickers=ticker,
                period=zeitraum,
                interval=intervall,
                auto_adjust=False,
                progress=False
            )
            if df is not None and not df.empty:
                df = df.dropna(how="all")
                # In Cache speichern
                try:
                    df.to_parquet(cache_file)
                except Exception:
                    pass
                
                # In EUR umrechnen
                df = rechne_df_in_eur_um(df, ticker)
                
                return ticker, df
        except Exception as fehler:
            print(f"Fehler beim Laden von {ticker}: {fehler}")
        return ticker, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch, t): t for t in ticker_liste}
        for future in concurrent.futures.as_completed(futures):
            ticker, df = future.result()
            if df is not None:
                daten[ticker] = df

    return daten


# =========================================================
# 04_CLOSE_SERIE_BEREINIGEN
# =========================================================
def hole_close_serie(df):
    """
    Gibt die Close-Serie aus einem DataFrame zurück.
    """
    return _hole_preisserie(df, "Close")


# =========================================================
# 05_HIGH_LOW_SERIEN
# =========================================================
def hole_high_serie(df):
    return _hole_preisserie(df, "High")


def hole_low_serie(df):
    return _hole_preisserie(df, "Low")


# =========================================================
# 06_WAEHRUNG_ERMITTELN
# =========================================================
@st.cache_data(ttl=3600*8, show_spinner=False)
def hole_waehrung_fuer_ticker(ticker):
    """
    Ermittelt die Handelswährung eines Tickers.
    """
    try:
        info = yf.Ticker(ticker).fast_info

        if hasattr(info, "get"):
            waehrung = info.get("currency", "EUR")
        else:
            waehrung = getattr(info, "currency", "EUR")

        if waehrung is None:
            waehrung = "EUR"

        return str(waehrung).upper()

    except Exception:
        return "EUR"


# =========================================================
# 07_WECHSELKURS_NACH_EUR
# =========================================================
@st.cache_data(ttl=3600*8, show_spinner=False)
def hole_wechselkurs_nach_eur(waehrung):
    """
    Liefert den Umrechnungskurs in EUR.
    """
    waehrung = str(waehrung).upper()

    if waehrung == "EUR":
        return 1.0

    try:
        ticker_fx = f"{waehrung}EUR=X"
        df_fx = yf.download(
            tickers=ticker_fx,
            period="5d",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df_fx is not None and not df_fx.empty:
            close_serie = hole_close_serie(df_fx)
            if not close_serie.empty:
                return float(close_serie.iloc[-1])

    except Exception:
        pass

    return None


# =========================================================
# 08_DF_IN_EUR_UMRECHNEN
# =========================================================
def rechne_df_in_eur_um(df, ticker):
    """
    Wandelt alle Preisspalten eines DataFrames in EUR um.
    """
    if df is None or df.empty:
        return df
    
    waehrung = hole_waehrung_fuer_ticker(ticker)
    if waehrung == "EUR":
        return df
    
    wechselkurs = hole_wechselkurs_nach_eur(waehrung)
    if wechselkurs is None or wechselkurs == 1.0:
        return df
    
    df_eur = df.copy()
    
    # Preis-Spalten identifizieren
    preis_spalten = ["Open", "High", "Low", "Close", "Adj Close"]
    
    # Unterstützung für MultiIndex (yf.download mit mehreren Tickern)
    if isinstance(df_eur.columns, pd.MultiIndex):
        for col in df_eur.columns:
            if col[0] in preis_spalten:
                df_eur[col] = df_eur[col] * wechselkurs
    else:
        for col in preis_spalten:
            if col in df_eur.columns:
                df_eur[col] = df_eur[col] * wechselkurs
                
    return df_eur