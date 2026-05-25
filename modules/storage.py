import json
import os
import time
from pathlib import Path

import pandas as pd


SHEET_NAMES = {
    "trade_republic_universum": "universum",
    "standardwerte_vorschlag": "settings",
    "prognosen_historie": "prognosen_historie",
    "prognosen_auswertung": "prognosen_auswertung",
    "prognosen_metadaten": "metadaten",
    "optimierungsvorschlaege_historie": "optimierung",
}

_TABLE_CACHE = {}
_JSON_CACHE = {}
_CACHE_TTL_SECONDS = int(os.getenv("TRADING_TOOL_SHEETS_CACHE_TTL", "300"))


def backend_name():
    return os.getenv("TRADING_TOOL_STORAGE", "local").strip().lower()


def nutzt_google_sheets():
    return backend_name() in {"google_sheets", "gsheets", "sheets"}


def logical_name_from_path(dateipfad):
    stem = Path(dateipfad).stem
    return stem if stem in SHEET_NAMES else None


def lese_tabelle(logical_name):
    if not nutzt_google_sheets():
        return None
    cached = _cache_get(_TABLE_CACHE, logical_name)
    if cached is not None:
        return cached.copy()

    ws = _worksheet(logical_name)
    rows = _records(ws)
    df = pd.DataFrame(rows)
    _cache_set(_TABLE_CACHE, logical_name, df.copy())
    return df


def schreibe_tabelle(logical_name, df):
    if not nutzt_google_sheets():
        return False
    ws = _worksheet(logical_name)
    ws.clear()
    if df is None or df.empty:
        _cache_set(_TABLE_CACHE, logical_name, pd.DataFrame())
        return True

    export = df.copy().fillna("")
    values = [export.columns.tolist()] + export.astype(str).values.tolist()
    ws.update(values)
    _cache_set(_TABLE_CACHE, logical_name, export.copy())
    return True


def kopiere_tabelle(logical_name, ziel_name):
    if not nutzt_google_sheets():
        return False
    df = lese_tabelle(logical_name)
    schreibe_tabelle(ziel_name, df if df is not None else pd.DataFrame())
    return True


def liste_tabellen(prefix=None):
    if not nutzt_google_sheets():
        return []
    spreadsheet = _spreadsheet()
    titel = [worksheet.title for worksheet in spreadsheet.worksheets()]
    if prefix:
        titel = [name for name in titel if name.startswith(prefix)]
    return titel


def loesche_tabelle(tabellen_name):
    if not nutzt_google_sheets():
        return False
    spreadsheet = _spreadsheet()
    worksheet = spreadsheet.worksheet(tabellen_name)
    spreadsheet.del_worksheet(worksheet)
    _TABLE_CACHE.pop(tabellen_name, None)
    _JSON_CACHE.pop(tabellen_name, None)
    return True


def tabellen_name(logical_name):
    return SHEET_NAMES.get(logical_name, logical_name)


def lese_json(logical_name, default=None):
    if not nutzt_google_sheets():
        return default
    cached = _cache_get(_JSON_CACHE, logical_name)
    if cached is not None:
        return cached

    ws = _worksheet(logical_name)
    rows = _records(ws)
    if not rows:
        return default

    if len(rows) == 1 and "json" in rows[0]:
        try:
            daten = json.loads(rows[0].get("json") or "{}")
            _cache_set(_JSON_CACHE, logical_name, daten)
            return daten
        except Exception:
            return default

    daten = {}
    for row in rows:
        key = row.get("key")
        if not key:
            continue
        value = row.get("value")
        try:
            daten[key] = json.loads(value)
        except Exception:
            daten[key] = value
    ergebnis = daten or default
    _cache_set(_JSON_CACHE, logical_name, ergebnis)
    return ergebnis


def schreibe_json(logical_name, daten):
    if not nutzt_google_sheets():
        return False
    ws = _worksheet(logical_name)
    ws.clear()
    ws.update([["json"], [json.dumps(daten or {}, ensure_ascii=False)]])
    _cache_set(_JSON_CACHE, logical_name, daten or {})
    return True


def _cache_get(cache, key):
    eintrag = cache.get(key)
    if not eintrag:
        return None
    zeitpunkt, wert = eintrag
    if time.time() - zeitpunkt > _CACHE_TTL_SECONDS:
        cache.pop(key, None)
        return None
    return wert


def _cache_set(cache, key, value):
    cache[key] = (time.time(), value)


def _worksheet(logical_name):
    spreadsheet = _spreadsheet()
    title = tabellen_name(logical_name)

    try:
        return spreadsheet.worksheet(title)
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=50)


def _spreadsheet():
    client = _gspread_client()
    spreadsheet_id = _secret("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID fehlt.")
    return client.open_by_key(spreadsheet_id)


def _records(ws):
    values = ws.get_all_values()
    if not values:
        return []

    headers = [str(header).strip() for header in values[0]]
    if not any(headers):
        return []

    rows = []
    for value_row in values[1:]:
        row = {}
        for index, header in enumerate(headers):
            if not header:
                continue
            row[header] = value_row[index] if index < len(value_row) else ""
        if any(str(value).strip() for value in row.values()):
            rows.append(row)
    return rows


def _gspread_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Google-Sheets-Backend benötigt gspread und google-auth."
        ) from exc

    raw = _secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON fehlt.")

    info = json.loads(raw) if isinstance(raw, str) else dict(raw)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(credentials)


def _secret(name):
    if os.getenv(name):
        return os.getenv(name)

    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return None
