from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


DATA_ORDNER = Path("data")
DATEI_INTRADAY_TIMING = DATA_ORDNER / "intraday_timing.csv"
CACHE_TTL_STUNDEN = 20


def lade_intraday_timing_fuer_ticker(ticker_liste, interval="15m", period="60d"):
    """
    Ermittelt aus Intraday-Kerzen eine historische Bestzeit je Ticker.

    Die Fixierungszeiten bleiben davon unberuehrt. Die Kennzahl beantwortet nur:
    Wenn man an vergangenen Tagen perfekt innerhalb des Tages gehandelt haette,
    zu welcher Uhrzeit lagen Kauf und Verkauf im Median?
    """
    ticker_liste = [str(t).strip().upper() for t in ticker_liste if str(t).strip()]
    if not ticker_liste:
        return {}

    cache = _lade_cache()
    ergebnis = {}
    geaendert = False

    for ticker in ticker_liste:
        eintrag = cache.get(ticker)
        if eintrag and not _cache_abgelaufen(eintrag.get("Berechnet am")):
            ergebnis[ticker] = eintrag
            continue

        analyse = _berechne_intraday_timing(ticker, interval=interval, period=period)
        if analyse:
            cache[ticker] = analyse
            ergebnis[ticker] = analyse
            geaendert = True

    if geaendert:
        _schreibe_cache(cache)

    return ergebnis


def _berechne_intraday_timing(ticker, interval="15m", period="60d"):
    try:
        df = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            prepost=False,
        )
    except Exception:
        return None

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Low" not in df.columns or "High" not in df.columns:
        return None

    df = df.dropna(subset=["Low", "High"]).copy()
    if df.empty:
        return None

    df["Datum"] = df.index.date
    tages_trades = []

    for _, tag in df.groupby("Datum", sort=True):
        trade = _bester_intraday_trade(tag)
        if trade:
            tages_trades.append(trade)

    if not tages_trades:
        return None

    trades = pd.DataFrame(tages_trades)
    kauf_minute = int(round(trades["Kauf Minute"].median()))
    verkauf_minute = int(round(trades["Verkauf Minute"].median()))

    return {
        "Ticker": ticker,
        "Intraday Beste Kaufzeit": _minute_zu_uhrzeit(kauf_minute),
        "Intraday Beste Verkaufszeit": _minute_zu_uhrzeit(verkauf_minute),
        "Intraday Ø Haltedauer Min": int(round(trades["Haltedauer Min"].mean())),
        "Intraday Ø Potenzial %": round(float(trades["Potenzial %"].mean()), 2),
        "Intraday Tage": int(len(trades)),
        "Berechnet am": datetime.now().isoformat(timespec="seconds"),
    }


def _bester_intraday_trade(tag):
    tag = tag.sort_index()
    if len(tag) < 2:
        return None

    bester = None
    min_preis = None
    min_zeit = None

    for zeitpunkt, zeile in tag.iterrows():
        low = _zu_float(zeile.get("Low"))
        high = _zu_float(zeile.get("High"))
        if low is None or high is None:
            continue

        if min_preis is not None and min_preis > 0:
            potenzial = ((high / min_preis) - 1) * 100
            if bester is None or potenzial > bester["Potenzial %"]:
                kauf_minute = _minute_des_tages(min_zeit)
                verkauf_minute = _minute_des_tages(zeitpunkt)
                bester = {
                    "Kauf Minute": kauf_minute,
                    "Verkauf Minute": verkauf_minute,
                    "Haltedauer Min": max(0, verkauf_minute - kauf_minute),
                    "Potenzial %": potenzial,
                }

        if min_preis is None or low < min_preis:
            min_preis = low
            min_zeit = zeitpunkt

    if bester is None or bester["Potenzial %"] <= 0:
        return None
    return bester


def _lade_cache():
    if not DATEI_INTRADAY_TIMING.exists():
        return {}
    try:
        df = pd.read_csv(DATEI_INTRADAY_TIMING)
    except Exception:
        return {}
    if df.empty or "Ticker" not in df.columns:
        return {}
    return {
        str(row["Ticker"]).strip().upper(): row.dropna().to_dict()
        for _, row in df.iterrows()
    }


def _schreibe_cache(cache):
    DATA_ORDNER.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(cache.values())
    if not df.empty:
        df = df.sort_values("Ticker")
    df.to_csv(DATEI_INTRADAY_TIMING, index=False)


def _cache_abgelaufen(zeitstempel):
    if not zeitstempel:
        return True
    try:
        berechnet = datetime.fromisoformat(str(zeitstempel))
    except Exception:
        return True
    return datetime.now() - berechnet > timedelta(hours=CACHE_TTL_STUNDEN)


def _minute_des_tages(zeitpunkt):
    return int(zeitpunkt.hour) * 60 + int(zeitpunkt.minute)


def _minute_zu_uhrzeit(minute):
    minute = int(max(0, min(23 * 60 + 59, minute)))
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _zu_float(wert):
    try:
        return float(wert)
    except Exception:
        return None
