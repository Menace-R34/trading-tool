# =========================================================
# 01_IMPORTS
# =========================================================
import pandas as pd
import yfinance as yf


# =========================================================
# 02_KONSTANTEN
# =========================================================
DAX_TICKER = "^GDAXI"


# =========================================================
# 03_HILFSFUNKTIONEN
# =========================================================
def _lade_dax_daten(zeitraum="6mo", intervall="1d"):
    try:
        df = yf.download(
            tickers=DAX_TICKER,
            period=zeitraum,
            interval=intervall,
            auto_adjust=False,
            progress=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


def _sichere_serie(df, spalte):
    if df is None or df.empty or spalte not in df.columns:
        return pd.Series(dtype="float64")

    serie = df[spalte]
    if isinstance(serie, pd.DataFrame):
        serie = serie.iloc[:, 0]

    return pd.to_numeric(serie, errors="coerce").dropna()


def _beurteile_volatilitaet(atr_relativ):
    if atr_relativ >= 2.2:
        return "Hoch"
    if atr_relativ >= 1.0:
        return "Mittel"
    return "Niedrig"


# =========================================================
# 04_MARKTLAGE_BERECHNEN
# =========================================================
def berechne_marktlage():
    """
    Ermittelt die aktuelle Gesamtmarktlage auf Basis des DAX.

    Rückgabe:
        dict mit Marktstatus, Trend, Volatilität und Kennzahlen
    """
    fallback = {
        "Index": "DAX",
        "Marktlage": "Neutral",
        "Trend": "Unklar",
        "Volatilität": "Unklar",
        "Signalbias": "Neutral",
        "DAX Schlusskurs": 0.0,
        "DAX Perf 5 Tage %": 0.0,
        "DAX Perf 20 Tage %": 0.0,
        "DAX GD20": 0.0,
        "DAX GD50": 0.0,
        "DAX ATR relativ %": 0.0,
        "Kommentar": "Keine Marktdaten verfügbar",
    }

    df = _lade_dax_daten()
    if df.empty:
        return fallback

    close = _sichere_serie(df, "Close")
    high = _sichere_serie(df, "High")
    low = _sichere_serie(df, "Low")

    if close.empty or high.empty or low.empty or len(close) < 60:
        return fallback

    gemeinsame_indexe = close.index.intersection(high.index).intersection(low.index)
    close = close.loc[gemeinsame_indexe]
    high = high.loc[gemeinsame_indexe]
    low = low.loc[gemeinsame_indexe]

    if len(close) < 60:
        return fallback

    letzter_close = float(close.iloc[-1])

    perf_5 = ((letzter_close / close.iloc[-6]) - 1) * 100 if len(close) >= 6 and close.iloc[-6] != 0 else 0.0
    perf_20 = ((letzter_close / close.iloc[-21]) - 1) * 100 if len(close) >= 21 and close.iloc[-21] != 0 else 0.0

    gd20 = close.rolling(20).mean().iloc[-1]
    gd50 = close.rolling(50).mean().iloc[-1]

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1
    ).max(axis=1)

    atr_14 = tr.rolling(14).mean().iloc[-1]
    atr_relativ = (atr_14 / letzter_close) * 100 if pd.notna(atr_14) and letzter_close != 0 else 0.0

    trend = "Seitwärts"
    if pd.notna(gd20) and pd.notna(gd50):
        if letzter_close > gd20 > gd50:
            trend = "Aufwärts"
        elif letzter_close < gd20 < gd50:
            trend = "Abwärts"

    volatilitaet = _beurteile_volatilitaet(atr_relativ)

    # -----------------------------------------------------
    # Marktlage-Logik
    # -----------------------------------------------------
    if trend == "Aufwärts" and perf_5 > 0 and perf_20 > 0:
        marktlage = "Risk-On"
        signalbias = "Long-freundlich"
        kommentar = "Der Gesamtmarkt zeigt eine positive Grundstruktur."
    elif trend == "Abwärts" and perf_5 < 0 and perf_20 < 0:
        marktlage = "Risk-Off"
        signalbias = "Defensiv"
        kommentar = "Der Gesamtmarkt zeigt eine negative Grundstruktur."
    else:
        marktlage = "Neutral"
        signalbias = "Selektiv"
        kommentar = "Der Gesamtmarkt zeigt kein klares Extrem."

    # Volatilitätsanpassung
    if volatilitaet == "Hoch" and marktlage == "Risk-Off":
        kommentar += " Hohe Schwankung bei schwacher Marktverfassung."
    elif volatilitaet == "Hoch" and marktlage == "Risk-On":
        kommentar += " Gute Bewegung, aber erhöhte Schwankung."
    elif volatilitaet == "Niedrig":
        kommentar += " Insgesamt ruhiger Markt."

    return {
        "Index": "DAX",
        "Marktlage": marktlage,
        "Trend": trend,
        "Volatilität": volatilitaet,
        "Signalbias": signalbias,
        "DAX Schlusskurs": round(letzter_close, 2),
        "DAX Perf 5 Tage %": round(float(perf_5), 2),
        "DAX Perf 20 Tage %": round(float(perf_20), 2),
        "DAX GD20": round(float(gd20), 2) if pd.notna(gd20) else 0.0,
        "DAX GD50": round(float(gd50), 2) if pd.notna(gd50) else 0.0,
        "DAX ATR relativ %": round(float(atr_relativ), 2),
        "Kommentar": kommentar,
    }