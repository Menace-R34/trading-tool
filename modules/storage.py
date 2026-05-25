import json
import os
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
    ws = _worksheet(logical_name)
    rows = _records(ws)
    return pd.DataFrame(rows)


def schreibe_tabelle(logical_name, df):
    if not nutzt_google_sheets():
        return False
    ws = _worksheet(logical_name)
    ws.clear()
    if df is None or df.empty:
        return True

    export = df.copy().fillna("")
    values = [export.columns.tolist()] + export.astype(str).values.tolist()
    ws.update(values)
    return True


def lese_json(logical_name, default=None):
    if not nutzt_google_sheets():
        return default
    ws = _worksheet(logical_name)
    rows = _records(ws)
    if not rows:
        return default

    if len(rows) == 1 and "json" in rows[0]:
        try:
            return json.loads(rows[0].get("json") or "{}")
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
    return daten or default


def schreibe_json(logical_name, daten):
    if not nutzt_google_sheets():
        return False
    ws = _worksheet(logical_name)
    ws.clear()
    ws.update([["json"], [json.dumps(daten or {}, ensure_ascii=False)]])
    return True


def _worksheet(logical_name):
    client = _gspread_client()
    spreadsheet_id = _secret("GOOGLE_SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID fehlt.")

    spreadsheet = client.open_by_key(spreadsheet_id)
    title = SHEET_NAMES.get(logical_name, logical_name)

    try:
        return spreadsheet.worksheet(title)
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=50)


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
