# =========================================================
# 01_IMPORTS
# =========================================================
import numpy as np
import pandas as pd

from modules.markt_daten import hole_close_serie, hole_high_serie, hole_low_serie


# =========================================================
# 02_HILFSFUNKTION_RSI
# =========================================================
def berechne_rsi(close, periode=14):
    delta = close.diff()

    gewinn = delta.clip(lower=0)
    verlust = -delta.clip(upper=0)

    durchschnitt_gewinn = gewinn.rolling(window=periode, min_periods=periode).mean()
    durchschnitt_verlust = verlust.rolling(window=periode, min_periods=periode).mean()

    rs = durchschnitt_gewinn / durchschnitt_verlust.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi


# =========================================================
# 03_MARKTSTATISTIK_BERECHNEN
# =========================================================
def berechne_marktstatistik(df, ticker):
    """
    Berechnet die wichtigsten Kennzahlen für Day- und Swingtrading.

    Rückgabe:
        dict mit Statistikwerten in % und €
    """
    if df is None or df.empty:
        return None

    close = hole_close_serie(df)
    high = hole_high_serie(df)
    low = hole_low_serie(df)

    if close.empty or high.empty or low.empty:
        return None

    gemeinsame_indexe = close.index.intersection(high.index).intersection(low.index)
    close = close.loc[gemeinsame_indexe]
    high = high.loc[gemeinsame_indexe]
    low = low.loc[gemeinsame_indexe]

    if len(close) < 200:
        return None

    # -----------------------------------------------------
    # Renditen und Tagesrange
    # -----------------------------------------------------
    rendite = close.pct_change()
    tagesveraenderung_prozent = rendite * 100
    tagesveraenderung_euro = close.diff()

    tagesrange_euro = (high - low).replace([np.inf, -np.inf], np.nan).dropna()
    tagesrange_prozent = ((high - low) / close.replace(0, np.nan)) * 100
    tagesrange_prozent = tagesrange_prozent.replace([np.inf, -np.inf], np.nan).dropna()

    # -----------------------------------------------------
    # Volatilität annualisiert
    # -----------------------------------------------------
    volatilitaet = rendite.dropna().std() * np.sqrt(252) * 100

    # -----------------------------------------------------
    # Hit-Rates
    # -----------------------------------------------------
    hitrate_2 = (tagesrange_prozent > 2).mean() * 100 if not tagesrange_prozent.empty else 0.0
    hitrate_3 = (tagesrange_prozent > 3).mean() * 100 if not tagesrange_prozent.empty else 0.0

    # -----------------------------------------------------
    # Trendlogik
    # -----------------------------------------------------
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    letzter_close = close.iloc[-1]
    letztes_sma20 = sma20.iloc[-1]
    letztes_sma50 = sma50.iloc[-1]

    trend_up = bool(
        pd.notna(letztes_sma20)
        and pd.notna(letztes_sma50)
        and letzter_close > letztes_sma20 > letztes_sma50
    )

    trend_stabil = bool(
        pd.notna(letztes_sma20)
        and pd.notna(letztes_sma50)
        and letztes_sma20 > letztes_sma50
    )

    # -----------------------------------------------------
    # Abstand zu Hoch / Tief auf 12 Monate
    # -----------------------------------------------------
    roll_high_252 = high.rolling(252, min_periods=200).max().iloc[-1]
    roll_low_252 = low.rolling(252, min_periods=200).min().iloc[-1]

    if pd.notna(roll_high_252) and roll_high_252 != 0:
        abstand_zum_hoch = ((letzter_close / roll_high_252) - 1) * 100
    else:
        abstand_zum_hoch = 0.0

    if pd.notna(roll_low_252) and roll_low_252 != 0:
        abstand_zum_tief = ((letzter_close / roll_low_252) - 1) * 100
    else:
        abstand_zum_tief = 0.0

    # -----------------------------------------------------
    # True Range / ATR
    # -----------------------------------------------------
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1
    ).max(axis=1)

    atr_14_euro = tr.rolling(14).mean().iloc[-1]
    atr_relativ = (atr_14_euro / letzter_close) * 100 if pd.notna(atr_14_euro) and letzter_close != 0 else 0.0

    # -----------------------------------------------------
    # Performance 20 Tage
    # -----------------------------------------------------
    if len(close) >= 21 and close.iloc[-21] != 0:
        perf_20 = ((letzter_close / close.iloc[-21]) - 1) * 100
    else:
        perf_20 = 0.0

    # -----------------------------------------------------
    # RSI
    # -----------------------------------------------------
    rsi_14_serie = berechne_rsi(close, periode=14)
    rsi_14 = rsi_14_serie.iloc[-1] if not rsi_14_serie.dropna().empty else np.nan

    # -----------------------------------------------------
    # Letzte Veränderung
    # -----------------------------------------------------
    letzte_tagesveraenderung_prozent = (
        tagesveraenderung_prozent.dropna().iloc[-1]
        if not tagesveraenderung_prozent.dropna().empty else 0.0
    )

    letzte_tagesveraenderung_euro = (
        tagesveraenderung_euro.dropna().iloc[-1]
        if not tagesveraenderung_euro.dropna().empty else 0.0
    )

    return {
        "Ticker": ticker,
        "Letzter Kurs €": round(float(letzter_close), 2),

        "Ø Tagesrange %": round(float(tagesrange_prozent.mean()), 2) if not tagesrange_prozent.empty else 0.0,
        "Ø Tagesrange €": round(float(tagesrange_euro.mean()), 2) if not tagesrange_euro.empty else 0.0,

        "Median Tagesrange %": round(float(tagesrange_prozent.median()), 2) if not tagesrange_prozent.empty else 0.0,
        "Median Tagesrange €": round(float(tagesrange_euro.median()), 2) if not tagesrange_euro.empty else 0.0,

        "Volatilität %": round(float(volatilitaet), 2) if pd.notna(volatilitaet) else 0.0,

        "Hit-Rate > 2 %": round(float(hitrate_2), 2),
        "Hit-Rate > 3 %": round(float(hitrate_3), 2),

        "Tagesveränderung %": round(float(letzte_tagesveraenderung_prozent), 2),
        "Tagesveränderung €": round(float(letzte_tagesveraenderung_euro), 2),

        "Trend Up": trend_up,
        "Trend Stabil": trend_stabil,

        "Abstand zum Hoch %": round(float(abstand_zum_hoch), 2),
        "Abstand zum Tief %": round(float(abstand_zum_tief), 2),

        "ATR relativ %": round(float(atr_relativ), 2),
        "ATR 14 €": round(float(atr_14_euro), 2) if pd.notna(atr_14_euro) else 0.0,

        "Perf 20 Tage %": round(float(perf_20), 2),
        "RSI 14": round(float(rsi_14), 2) if pd.notna(rsi_14) else 0.0,
    }