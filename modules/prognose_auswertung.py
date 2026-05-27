# =========================================================
# 01_IMPORTS
# =========================================================
import json
import pandas as pd
import yfinance as yf
from pathlib import Path

from modules.prognose_speicher import (
    _lese_csv_sicher, _schreibe_csv, _heute_str, _jetzt_berlin,
    DATEI_PROGNOSEN, DATEI_AUSWERTUNG, DATEI_METADATEN, _zu_float,
    _schreibe_json_datei, _zeitstempel_str
)
from modules.markt_daten import rechne_df_in_eur_um
from modules.intraday_timing import werte_intraday_prognose_aus

# =========================================================
# 02_METADATEN / TAGESPRUEFUNG
# =========================================================
def _lade_metadaten():
    if not Path(DATEI_METADATEN).exists():
        return {}
    try:
        with open(DATEI_METADATEN, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _speichere_metadaten(daten):
    _schreibe_json_datei(DATEI_METADATEN, daten)

def fuehre_tagespruefung_aus(settings=None):
    """
    Soll einmal pro Tag aufgerufen werden (z.B. beim Start).
    Prüft alle bisher nicht endgültig bewerteten Prognosen der *Vortage*.
    """
    heute = _heute_str()
    meta = _lade_metadaten()

    letzte_pruefung = meta.get("letzte_tagespruefung", "")
    if letzte_pruefung == heute:
        # Heute schon geprüft
        return False
    
    if settings is None:
        settings = {}
    
    # Haltedauern aus Settings beziehen
    horizon_day = int(settings.get("day_haltedauer", 3))
    horizon_swing = int(settings.get("swing_haltedauer", 10))

    pruefung_zeitstempel = _zeitstempel_str()
    werte_prognosen_aus(
        horizon_day=horizon_day,
        horizon_swing=horizon_swing,
        pruefung_zeitstempel=pruefung_zeitstempel,
    )
    
    meta["letzte_tagespruefung"] = heute
    if "tagespruefungen" not in meta:
        meta["tagespruefungen"] = {}
    meta["tagespruefungen"][heute] = pruefung_zeitstempel
    _speichere_metadaten(meta)
    return True

# =========================================================
# 03_EINZELPROGNOSE AUSWERTEN
# =========================================================
def _lade_kursdaten_fuer_auswertung(ticker, start_datum, end_datum=None):
    start_dt = pd.to_datetime(start_datum).strftime("%Y-%m-%d")
    end_dt = _heute_str() if end_datum is None else pd.to_datetime(end_datum).strftime("%Y-%m-%d")
    
    try:
        df = yf.download(tickers=ticker, start=start_dt, end=end_dt, interval="1d", auto_adjust=False, progress=False)
        if df is None or df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.dropna(how="all")
        
        # In EUR umrechnen
        df = rechne_df_in_eur_um(df, ticker)
        
        return df
    except Exception:
        return pd.DataFrame()

def _werte_einzelprognose_aus(zeile, strategie="day", horizon_tage=3):
    ticker = zeile.get("Ticker", "")
    prognose_datum = zeile.get("Prognose-Datum", "")

    if not ticker or not prognose_datum:
        return {"Status": "Nicht bewertbar", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    if strategie == "day":
        kauf = zeile.get("Day Kauf", "NEIN")
        stop_loss = _zu_float(zeile.get("Day Stop Loss €", 0))
        take_profit = _zu_float(zeile.get("Day Take Profit €", 0))
        buy_in_zeit = zeile.get("Day Buy-in Zeit", "")
    else:
        kauf = zeile.get("Swing Kauf", "NEIN")
        stop_loss = _zu_float(zeile.get("Swing Stop Loss €", 0))
        take_profit = _zu_float(zeile.get("Swing Take Profit €", 0))
        buy_in_zeit = zeile.get("Swing Buy-in Zeit", "")

    if kauf != "JA":
        return {"Status": "Nicht bewertet", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    intraday = werte_intraday_prognose_aus(
        ticker=ticker,
        prognose_datum=prognose_datum,
        kaufzeit=buy_in_zeit,
        stop_loss=stop_loss,
        take_profit=take_profit,
        horizon_tage=horizon_tage,
    )
    if intraday:
        return intraday

    # Wir prüfen ab dem Folgetag
    start = pd.to_datetime(prognose_datum) + pd.Timedelta(days=1)
    
    # Wenn heute <= prognose_datum, noch nicht prüfen (nur Folgetage)
    if start.strftime("%Y-%m-%d") > _heute_str():
        return {"Status": "Warten auf Folgetag", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    ende = start + pd.Timedelta(days=horizon_tage + 7)
    df_kurs = _lade_kursdaten_fuer_auswertung(ticker, start, ende)

    if df_kurs.empty:
        return {"Status": "Keine Daten", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    df_kurs = df_kurs.head(horizon_tage)
    if df_kurs.empty:
        return {"Status": "Noch offen", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    einstieg = _zu_float(zeile.get("Letzter Kurs €", 0))
    if einstieg <= 0:
        return {"Status": "Fehlender Einstieg", "Ergebnis": "", "Treffer": None, "Erreicht am": "", "Rendite %": 0.0, "Haltedauer": 0}

    haltedauer_tp = None
    haltedauer_sl = None
    datum_tp = ""
    datum_sl = ""

    current_hold = 0
    for datum, row in df_kurs.iterrows():
        current_hold += 1
        high = _zu_float(row.get("High", 0))
        low = _zu_float(row.get("Low", 0))

        if high >= take_profit and take_profit > 0 and haltedauer_tp is None:
            haltedauer_tp = current_hold
            datum_tp = datum.strftime("%Y-%m-%d")
        
        if low <= stop_loss and stop_loss > 0 and haltedauer_sl is None:
            haltedauer_sl = current_hold
            datum_sl = datum.strftime("%Y-%m-%d")

    # Auswertung nach Priorität: 1. TP (Treffer), 2. SL (Fehler), 3. Zeitablauf
    if haltedauer_tp is not None:
        # Selbst wenn SL getroffen wurde, werten wir es als Treffer (Wunsch: "egal ob dazwischen stark absinkt")
        rendite = ((take_profit / einstieg) - 1) * 100
        return {
            "Status": "Abgeschlossen", 
            "Ergebnis": "Treffer", 
            "Treffer": 1, 
            "Erreicht am": datum_tp, 
            "Rendite %": round(rendite, 2), 
            "Haltedauer": haltedauer_tp
        }

    if haltedauer_sl is not None:
        rendite = ((stop_loss / einstieg) - 1) * 100
        return {
            "Status": "Abgeschlossen", 
            "Ergebnis": "Fehler", 
            "Treffer": 0, 
            "Erreicht am": datum_sl, 
            "Rendite %": round(rendite, 2), 
            "Haltedauer": haltedauer_sl
        }

    # Zeitablauf
    letzter_close = _zu_float(df_kurs["Close"].iloc[-1], einstieg)
    rendite = ((letzter_close / einstieg) - 1) * 100

    return {
        "Status": "Zeitablauf",
        "Ergebnis": "Positiv" if rendite > 0 else "Negativ" if rendite < 0 else "Neutral",
        "Treffer": 1 if rendite > 0 else 0 if rendite < 0 else None,
        "Erreicht am": df_kurs.index[-1].strftime("%Y-%m-%d"),
        "Rendite %": round(rendite, 2),
        "Haltedauer": current_hold
    }

# =========================================================
# 04_ALLE_PROGNOSEN_AUSWERTEN
# =========================================================
def werte_prognosen_aus(
    datei_prognosen=DATEI_PROGNOSEN,
    datei_auswertung=DATEI_AUSWERTUNG,
    horizon_day=3,
    horizon_swing=10,
    pruefung_zeitstempel=None,
):
    df = _lese_csv_sicher(datei_prognosen)
    if df.empty:
        return pd.DataFrame()

    pruefung_zeitstempel = pruefung_zeitstempel or _zeitstempel_str()

    # Wir überschreiben die Auswertung immer komplett um offene Trades fortzuführen.
    # Da yfinance gecached wird, ist es performant genug für eine tägliche Ausführung.
    auswertungen = []
    
    for _, zeile in df.iterrows():
        basis = {
            "Ticker": zeile.get("Ticker", ""),
            "Prognose-Datum": zeile.get("Prognose-Datum", ""),
            "Prognose-Zeit": zeile.get("Prognose-Zeit", ""),
            "Prognose-Zeitstempel": zeile.get("Prognose-Zeitstempel", ""),
            "Prognosekontrolle durchgeführt": pruefung_zeitstempel,
        }
        
        day = _werte_einzelprognose_aus(zeile, strategie="day", horizon_tage=horizon_day)
        swing = _werte_einzelprognose_aus(zeile, strategie="swing", horizon_tage=horizon_swing)

        auswertungen.append({
            **basis,
            "Day Status": day["Status"], "Day Ergebnis": day["Ergebnis"], "Day Treffer": day["Treffer"],
            "Day Erreicht am": day["Erreicht am"], "Day Rendite %": day["Rendite %"], "Day Haltedauer": day["Haltedauer"],
            "Day Tatsächliche Buy-in Zeit": day.get("Buy-in Zeit", ""), "Day Tatsächliche Exit Zeit": day.get("Exit Zeit", ""),
            
            "Swing Status": swing["Status"], "Swing Ergebnis": swing["Ergebnis"], "Swing Treffer": swing["Treffer"],
            "Swing Erreicht am": swing["Erreicht am"], "Swing Rendite %": swing["Rendite %"], "Swing Haltedauer": swing["Haltedauer"],
            "Swing Tatsächliche Buy-in Zeit": swing.get("Buy-in Zeit", ""), "Swing Tatsächliche Exit Zeit": swing.get("Exit Zeit", ""),
        })

    df_aus = pd.DataFrame(auswertungen)

    merge_spalten = ["Ticker", "Prognose-Zeitstempel"] if "Prognose-Zeitstempel" in df.columns and "Prognose-Zeitstempel" in df_aus.columns else ["Ticker", "Prognose-Datum"]
    kombi = df.merge(df_aus, on=merge_spalten, how="left")
    
    if "Prognose-Zeitstempel_x" in kombi.columns:
        kombi["Prognose-Zeitstempel"] = kombi["Prognose-Zeitstempel_x"]
        kombi = kombi.drop(columns=[c for c in ["Prognose-Zeitstempel_x", "Prognose-Zeitstempel_y"] if c in kombi.columns])
    if "Prognose-Datum_x" in kombi.columns:
        kombi["Prognose-Datum"] = kombi["Prognose-Datum_x"]
        kombi = kombi.drop(columns=[c for c in ["Prognose-Datum_x", "Prognose-Datum_y"] if c in kombi.columns])
    if "Prognose-Zeitstempel" in kombi.columns:
        kombi = kombi.sort_values("Prognose-Zeitstempel", ascending=False)

    _schreibe_csv(kombi, datei_auswertung)
    return kombi

# =========================================================
# 05_STATISTIKEN & GENAUIGKEIT
# =========================================================
def berechne_trefferstatistik(datei_auswertung=DATEI_AUSWERTUNG):
    df = _lese_csv_sicher(datei_auswertung)
    if df.empty:
        return {"Day Trefferquote %": 0.0, "Day Anzahl": 0, "Swing Trefferquote %": 0.0, "Swing Anzahl": 0}

    day_treffer = _zu_bool_serie(df["Day Treffer"]) if "Day Treffer" in df.columns else pd.Series(dtype="float64")
    swing_treffer = _zu_bool_serie(df["Swing Treffer"]) if "Swing Treffer" in df.columns else pd.Series(dtype="float64")

    day_basis = day_treffer.dropna()
    swing_basis = swing_treffer.dropna()

    day_quote = day_basis.mean() * 100 if not day_basis.empty else 0.0
    swing_quote = swing_basis.mean() * 100 if not swing_basis.empty else 0.0

    return {
        "Day Trefferquote %": round(day_quote, 2), "Day Anzahl": int(len(day_basis)),
        "Swing Trefferquote %": round(swing_quote, 2), "Swing Anzahl": int(len(swing_basis)),
    }

def _zu_bool_serie(serie):
    if serie is None:
        return pd.Series(dtype="float64")

    def konvertiere(wert):
        if pd.isna(wert):
            return pd.NA
        if isinstance(wert, bool):
            return 1.0 if wert else 0.0
        if isinstance(wert, (int, float)):
            return 1.0 if float(wert) != 0.0 else 0.0

        text = str(wert).strip().lower()
        if text in {"", "nan", "none", "null", "<na>"}:
            return pd.NA
        if text in {"true", "wahr", "ja", "yes", "y", "1", "1.0", "x"}:
            return 1.0
        if text in {"false", "falsch", "nein", "no", "n", "0", "0.0"}:
            return 0.0

        zahl = pd.to_numeric(text.replace(",", "."), errors="coerce")
        if pd.isna(zahl):
            return pd.NA
        return 1.0 if float(zahl) != 0.0 else 0.0

    return serie.apply(konvertiere).astype("Float64")

def _zu_numeric_serie(serie):
    if serie is None:
        return pd.Series(dtype="float64")
    return pd.to_numeric(
        serie.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

def berechne_ticker_genauigkeit(datei_auswertung=DATEI_AUSWERTUNG):
    """
    Liefert für jeden Ticker die historische Genauigkeit und Durchschnitts-Performance,
    getrennt nach Day und Swing sowie kombiniert.
    Gibt ein Dict zurück: { Ticker: { 'Hist. Prognosegenauigkeit %': ..., 'Ø Endperformance': ... } }
    """
    df = _lese_csv_sicher(datei_auswertung)
    if df.empty:
        return {}

    genauigkeiten = {}
    tickers = df["Ticker"].unique()

    for ticker in tickers:
        df_t = df[df["Ticker"] == ticker]
        
        day_treffer_serie = _zu_bool_serie(df_t["Day Treffer"]).dropna()
        swing_treffer_serie = _zu_bool_serie(df_t["Swing Treffer"]).dropna()
        
        day_rendite = _zu_numeric_serie(df_t["Day Rendite %"]).dropna()
        swing_rendite = _zu_numeric_serie(df_t["Swing Rendite %"]).dropna()

        alle_treffer = list(day_treffer_serie) + list(swing_treffer_serie)
        alle_renditen = list(day_rendite) + list(swing_rendite)

        if not alle_treffer:
            continue
            
        genauigkeit = (sum(alle_treffer) / len(alle_treffer)) * 100
        avg_perf = sum(alle_renditen) / len(alle_renditen) if alle_renditen else 0.0
        
        # Timing (Haltedauer)
        best_day_hold = df_t[df_t["Day Treffer"] == 1]["Day Haltedauer"].median() if "Day Haltedauer" in df_t.columns and not df_t[df_t["Day Treffer"] == 1].empty else 0
        best_swing_hold = df_t[df_t["Swing Treffer"] == 1]["Swing Haltedauer"].median() if "Swing Haltedauer" in df_t.columns and not df_t[df_t["Swing Treffer"] == 1].empty else 0

        genauigkeiten[ticker] = {
            "Hist. Prognosegenauigkeit %": round(genauigkeit, 1),
            "Ø Endperformance %": round(avg_perf, 2),
            "Best Hold Day": int(best_day_hold) if not pd.isna(best_day_hold) else 0,
            "Best Hold Swing": int(best_swing_hold) if not pd.isna(best_swing_hold) else 0,
            "Anzahl Hist. Prognosen": len(alle_treffer)
        }

    return genauigkeiten
