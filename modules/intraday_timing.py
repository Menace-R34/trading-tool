from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from modules.prognose_speicher import ZEITZONE_BERLIN, _jetzt_berlin


DATA_ORDNER = Path("data")
DATEI_AUSWERTUNG = DATA_ORDNER / "prognosen_auswertung.csv"
DATEI_INTRADAY_TIMING = DATA_ORDNER / "intraday_timing.csv"
CACHE_TTL_STUNDEN = 20
CACHE_VERSION = 3
MIN_OPTIMIERUNGS_TRADES = 3


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
        if eintrag and _cache_version_gueltig(eintrag) and not _cache_abgelaufen(eintrag.get("Berechnet am")):
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

    df = _index_in_berlin_zeit(df)
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

    basis = {
        "Ticker": ticker,
        "Intraday Beste Kaufzeit": _minute_zu_uhrzeit(kauf_minute),
        "Intraday Beste Verkaufszeit": _minute_zu_uhrzeit(verkauf_minute),
        "Intraday Ø Haltedauer Min": int(round(trades["Haltedauer Min"].mean())),
        "Intraday Ø Potenzial %": round(float(trades["Potenzial %"].mean()), 2),
        "Intraday Tage": int(len(trades)),
        "Berechnet am": _jetzt_berlin().isoformat(timespec="seconds"),
        "Cache Version": CACHE_VERSION,
    }
    basis.update(_berechne_strategie_optimierung(ticker, df))
    return basis


def _berechne_strategie_optimierung(ticker, intraday_df):
    historie = _lade_auswertung_fuer_ticker(ticker)
    if historie.empty or intraday_df.empty:
        return {}

    ergebnis = {}
    for strategie in ["Day", "Swing"]:
        optimierung = _optimiere_strategie_zeiten(historie, intraday_df, strategie)
        if optimierung:
            prefix = f"{strategie} Optimiert"
            ergebnis[f"{prefix} Buy-in Zeit"] = optimierung["Buy-in Zeit"]
            ergebnis[f"{prefix} Take-Profit Zeit"] = optimierung["Take-Profit Zeit"]
            ergebnis[f"{prefix} Trefferquote %"] = optimierung["Trefferquote %"]
            ergebnis[f"{prefix} Ø Rendite %"] = optimierung["Ø Rendite %"]
            ergebnis[f"{prefix} Basis"] = optimierung["Basis"]
    return ergebnis


def _lade_auswertung_fuer_ticker(ticker):
    if not DATEI_AUSWERTUNG.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(DATEI_AUSWERTUNG)
    except Exception:
        return pd.DataFrame()
    if df.empty or "Ticker" not in df.columns:
        return pd.DataFrame()
    return df[df["Ticker"].astype(str).str.upper().str.strip() == str(ticker).upper().strip()].copy()


def _optimiere_strategie_zeiten(historie, intraday_df, strategie):
    kauf_col = f"{strategie} Kauf"
    sl_col = f"{strategie} Stop Loss €"
    tp_col = f"{strategie} Take Profit €"
    datum_col = "Prognose-Datum"
    if not {kauf_col, sl_col, tp_col, datum_col}.issubset(historie.columns):
        return None

    rows = historie[
        historie[kauf_col].astype(str).str.upper().eq("JA")
    ].copy()
    if rows.empty:
        return None

    candidate_minutes = _ermittle_kandidaten_minuten(intraday_df)
    if not candidate_minutes:
        return None

    horizont = 3 if strategie == "Day" else 10
    bewertungen = []
    for minute in candidate_minutes:
        ergebnisse = []
        for _, zeile in rows.iterrows():
            test = _simuliere_historische_prognose(
                intraday_df=intraday_df,
                prognose_datum=zeile.get(datum_col),
                kauf_minute=minute,
                stop_loss=_zu_float(zeile.get(sl_col)),
                take_profit=_zu_float(zeile.get(tp_col)),
                horizon_tage=horizont,
            )
            if test:
                ergebnisse.append(test)

        if len(ergebnisse) < MIN_OPTIMIERUNGS_TRADES:
            continue

        trefferquote = sum(e["Treffer"] for e in ergebnisse) / len(ergebnisse) * 100
        avg_rendite = sum(e["Rendite %"] for e in ergebnisse) / len(ergebnisse)
        avg_exit = int(round(sum(e["Exit Minute"] for e in ergebnisse) / len(ergebnisse)))
        bewertungen.append({
            "Kauf Minute": minute,
            "Exit Minute": avg_exit,
            "Trefferquote %": trefferquote,
            "Ø Rendite %": avg_rendite,
            "Basis": len(ergebnisse),
        })

    if not bewertungen:
        return None

    bester = sorted(
        bewertungen,
        key=lambda x: (x["Trefferquote %"], x["Ø Rendite %"], x["Basis"]),
        reverse=True,
    )[0]
    return {
        "Buy-in Zeit": _minute_zu_uhrzeit(bester["Kauf Minute"]),
        "Take-Profit Zeit": _minute_zu_uhrzeit(bester["Exit Minute"]),
        "Trefferquote %": round(float(bester["Trefferquote %"]), 1),
        "Ø Rendite %": round(float(bester["Ø Rendite %"]), 2),
        "Basis": int(bester["Basis"]),
    }


def _ermittle_kandidaten_minuten(intraday_df):
    minuten = sorted({
        _minute_des_tages(idx)
        for idx in intraday_df.index
        if 7 * 60 <= _minute_des_tages(idx) <= 22 * 60
    })
    return minuten[::2] if len(minuten) > 28 else minuten


def _simuliere_historische_prognose(intraday_df, prognose_datum, kauf_minute, stop_loss, take_profit, horizon_tage):
    if stop_loss is None or take_profit is None or stop_loss <= 0 or take_profit <= 0:
        return None
    try:
        start_date = pd.to_datetime(prognose_datum).date()
    except Exception:
        return None

    zeitraum = intraday_df[
        (intraday_df.index.date >= start_date) &
        (intraday_df.index.date < start_date + timedelta(days=int(horizon_tage)))
    ].copy()
    if zeitraum.empty:
        return None

    entry_zeit = None
    entry_preis = None
    for zeitpunkt, row in zeitraum.iterrows():
        if zeitpunkt.date() == start_date and _minute_des_tages(zeitpunkt) < kauf_minute:
            continue
        entry_zeit = zeitpunkt
        entry_preis = _zu_float(row.get("Close"))
        break
    if entry_zeit is None or entry_preis is None or entry_preis <= 0:
        return None

    letzter_zeitpunkt = entry_zeit
    letzter_close = entry_preis
    for zeitpunkt, row in zeitraum.loc[zeitraum.index >= entry_zeit].iterrows():
        high = _zu_float(row.get("High"))
        low = _zu_float(row.get("Low"))
        close = _zu_float(row.get("Close"))
        if close is not None:
            letzter_close = close
            letzter_zeitpunkt = zeitpunkt
        if high is not None and high >= take_profit:
            return {
                "Treffer": 1,
                "Rendite %": ((take_profit / entry_preis) - 1) * 100,
                "Exit Minute": _minute_des_tages(zeitpunkt),
            }
        if low is not None and low <= stop_loss:
            return {
                "Treffer": 0,
                "Rendite %": ((stop_loss / entry_preis) - 1) * 100,
                "Exit Minute": _minute_des_tages(zeitpunkt),
            }

    rendite = ((letzter_close / entry_preis) - 1) * 100
    return {
        "Treffer": 1 if rendite > 0 else 0,
        "Rendite %": rendite,
        "Exit Minute": _minute_des_tages(letzter_zeitpunkt),
    }


def werte_intraday_prognose_aus(
    ticker,
    prognose_datum,
    kaufzeit,
    stop_loss,
    take_profit,
    horizon_tage=3,
    interval="15m",
    erlaube_heute=False,
):
    if not ticker or not prognose_datum or not kaufzeit:
        return None

    start = pd.to_datetime(prognose_datum)
    if start.strftime("%Y-%m-%d") > _jetzt_berlin().strftime("%Y-%m-%d"):
        return None
    if start.strftime("%Y-%m-%d") == _jetzt_berlin().strftime("%Y-%m-%d") and not erlaube_heute:
        return None

    ende = start + pd.Timedelta(days=int(horizon_tage) + 2)
    if start.strftime("%Y-%m-%d") == _jetzt_berlin().strftime("%Y-%m-%d"):
        ende = start + pd.Timedelta(days=1)

    try:
        df = yf.download(
            tickers=ticker,
            start=start.strftime("%Y-%m-%d"),
            end=ende.strftime("%Y-%m-%d"),
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
    if not {"High", "Low", "Close"}.issubset(df.columns):
        return None

    kauf_minute = _uhrzeit_zu_minute(kaufzeit)
    if kauf_minute is None:
        return None

    df = df.dropna(subset=["High", "Low", "Close"]).sort_index()
    if df.empty:
        return None
    df = _index_in_berlin_zeit(df)

    entry_zeit = None
    entry_preis = None
    start_date = start.date()

    for zeitpunkt, row in df.iterrows():
        if (zeitpunkt.date() - start_date).days >= int(horizon_tage):
            break
        if zeitpunkt.date() == start_date and _minute_des_tages(zeitpunkt) < kauf_minute:
            continue
        entry_zeit = zeitpunkt
        entry_preis = _zu_float(row.get("Close"))
        break

    if entry_zeit is None or entry_preis is None or entry_preis <= 0:
        return None

    for zeitpunkt, row in df.loc[df.index >= entry_zeit].iterrows():
        haltedauer_tage = (zeitpunkt.date() - start_date).days + 1
        if haltedauer_tage > int(horizon_tage):
            break

        high = _zu_float(row.get("High"))
        low = _zu_float(row.get("Low"))
        if high is None or low is None:
            continue

        if take_profit > 0 and high >= take_profit:
            rendite = ((take_profit / entry_preis) - 1) * 100
            return {
                "Status": "Intraday abgeschlossen",
                "Ergebnis": "Treffer",
                "Treffer": 1,
                "Erreicht am": _formatiere_berlin_zeitpunkt(zeitpunkt),
                "Rendite %": round(rendite, 2),
                "Haltedauer": haltedauer_tage,
                "Buy-in Zeit": _formatiere_berlin_uhrzeit(entry_zeit),
                "Exit Zeit": _formatiere_berlin_uhrzeit(zeitpunkt),
            }

        if stop_loss > 0 and low <= stop_loss:
            rendite = ((stop_loss / entry_preis) - 1) * 100
            return {
                "Status": "Intraday abgeschlossen",
                "Ergebnis": "Fehler",
                "Treffer": 0,
                "Erreicht am": _formatiere_berlin_zeitpunkt(zeitpunkt),
                "Rendite %": round(rendite, 2),
                "Haltedauer": haltedauer_tage,
                "Buy-in Zeit": _formatiere_berlin_uhrzeit(entry_zeit),
                "Exit Zeit": _formatiere_berlin_uhrzeit(zeitpunkt),
            }

    letzte_zeile = df.loc[df.index >= entry_zeit].tail(1)
    if letzte_zeile.empty:
        return None
    letzter_zeitpunkt = letzte_zeile.index[-1]
    letzter_close = _zu_float(letzte_zeile.iloc[-1].get("Close")) or entry_preis
    rendite = ((letzter_close / entry_preis) - 1) * 100
    return {
        "Status": "Intraday Zeitablauf",
        "Ergebnis": "Positiv" if rendite > 0 else "Negativ" if rendite < 0 else "Neutral",
        "Treffer": 1 if rendite > 0 else 0 if rendite < 0 else None,
        "Erreicht am": _formatiere_berlin_zeitpunkt(letzter_zeitpunkt),
        "Rendite %": round(rendite, 2),
        "Haltedauer": min(int(horizon_tage), (letzter_zeitpunkt.date() - start_date).days + 1),
        "Buy-in Zeit": _formatiere_berlin_uhrzeit(entry_zeit),
        "Exit Zeit": _formatiere_berlin_uhrzeit(letzter_zeitpunkt),
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
    if berechnet.tzinfo is None:
        berechnet = berechnet.replace(tzinfo=ZEITZONE_BERLIN)
    return _jetzt_berlin() - berechnet.astimezone(ZEITZONE_BERLIN) > timedelta(hours=CACHE_TTL_STUNDEN)


def _cache_version_gueltig(eintrag):
    try:
        return int(float(eintrag.get("Cache Version", 0))) == CACHE_VERSION
    except Exception:
        return False


def _minute_des_tages(zeitpunkt):
    zeitpunkt = _zeitpunkt_in_berlin(zeitpunkt)
    return int(zeitpunkt.hour) * 60 + int(zeitpunkt.minute)


def _minute_zu_uhrzeit(minute):
    minute = int(max(0, min(23 * 60 + 59, minute)))
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _uhrzeit_zu_minute(uhrzeit):
    try:
        stunde, minute = str(uhrzeit).strip().split(":", 1)
        return int(stunde) * 60 + int(minute[:2])
    except Exception:
        return None


def _zu_float(wert):
    try:
        return float(wert)
    except Exception:
        return None


def _index_in_berlin_zeit(df):
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize(ZEITZONE_BERLIN)
    else:
        df.index = df.index.tz_convert(ZEITZONE_BERLIN)
    return df


def _zeitpunkt_in_berlin(zeitpunkt):
    ts = pd.Timestamp(zeitpunkt)
    if ts.tzinfo is None:
        ts = ts.tz_localize(ZEITZONE_BERLIN)
    return ts.tz_convert(ZEITZONE_BERLIN)


def _formatiere_berlin_zeitpunkt(zeitpunkt):
    return _zeitpunkt_in_berlin(zeitpunkt).strftime("%Y-%m-%d %H:%M")


def _formatiere_berlin_uhrzeit(zeitpunkt):
    return _zeitpunkt_in_berlin(zeitpunkt).strftime("%H:%M")
