# =========================================================
# 01_IMPORTS
# =========================================================
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import shutil
from modules import storage

# =========================================================
# 02_KONSTANTEN
# =========================================================
DATA_ORDNER = Path("data")
BACKUP_ORDNER = DATA_ORDNER / "backups"
DATEI_PROGNOSEN = DATA_ORDNER / "prognosen_historie.csv"
DATEI_AUSWERTUNG = DATA_ORDNER / "prognosen_auswertung.csv"
DATEI_METADATEN = DATA_ORDNER / "prognosen_metadaten.json"
DATEI_STANDARDWERTE = DATA_ORDNER / "standardwerte_vorschlag.json"

# =========================================================
# 03_STANDARDWERTE (Laden & Speichern)
# =========================================================
def lade_gespeicherte_standardwerte(dateipfad=DATEI_STANDARDWERTE):
    logical_name = storage.logical_name_from_path(dateipfad)
    if logical_name:
        daten = storage.lese_json(logical_name, default=None)
        if isinstance(daten, dict):
            return daten

    if not Path(dateipfad).exists():
        return {}
    try:
        with open(dateipfad, "r", encoding="utf-8") as f:
            import json
            daten = json.load(f)
        return daten if isinstance(daten, dict) else {}
    except Exception:
        return {}

def speichere_standardwerte(standardwerte, dateipfad=DATEI_STANDARDWERTE):
    if not isinstance(standardwerte, dict):
        return False
    logical_name = storage.logical_name_from_path(dateipfad)
    if logical_name and storage.schreibe_json(logical_name, standardwerte):
        return True

    DATA_ORDNER.mkdir(parents=True, exist_ok=True)
    try:
        with open(dateipfad, "w", encoding="utf-8") as f:
            import json
            json.dump(standardwerte, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# =========================================================
# 04_HILFSFUNKTIONEN
# =========================================================
def _stelle_data_ordner_sicher():
    DATA_ORDNER.mkdir(parents=True, exist_ok=True)
    BACKUP_ORDNER.mkdir(parents=True, exist_ok=True)

def _jetzt_berlin():
    return datetime.now(ZoneInfo("Europe/Berlin"))

def _jetzt_new_york():
    return datetime.now(ZoneInfo("America/New_York"))

def _heute_str():
    return _jetzt_berlin().strftime("%Y-%m-%d")

def _uhrzeit_str():
    return _jetzt_berlin().strftime("%H:%M:%S")

def _zeitstempel_str():
    return _jetzt_berlin().strftime("%Y-%m-%d %H:%M:%S")

def _lese_csv_sicher(dateipfad):
    logical_name = storage.logical_name_from_path(dateipfad)
    if logical_name:
        df_storage = storage.lese_tabelle(logical_name)
        if df_storage is not None:
            df = df_storage
        else:
            df = None
    else:
        df = None

    if df is None:
        if not Path(dateipfad).exists():
            return pd.DataFrame()
        try:
            df = pd.read_csv(dateipfad)
        except Exception:
            return pd.DataFrame()

    try:
        # --- MIGRATION: Alle möglichen Varianten auf technischen Standard normalisieren ---
        rename_map = {
            "Erwarteter Gewinn (Day) €": "Day Netto €",
            "Erwarteter Gewinn (Swing) €": "Swing Netto €",
            "Day €": "Day Netto €",
            "Swing €": "Swing Netto €",
            "Acc %": "Hist. Prognosegenauigkeit %",
            "#": "Anzahl Hist. Prognosen",
            "Status": "Handelsfenster",
            "Sig. (D)": "Day Signalstärke",
            "Sig. (S)": "Swing Signalstärke",
            "Score (D)": "Day Score",
            "Score (S)": "Swing Score",
            "CRV (D)": "Day CRV",
            "CRV (S)": "Swing CRV",
            "Kurs €": "Letzter Kurs €",
            "Hold (D)": "Hist. Idealer Hold (Day)",
            "Hold (S)": "Hist. Idealer Hold (Swing)",
            "Saison": "Saison-Score",
            "News": "News-Score"
        }
        # Nur umbenennen, wenn die alte Spalte existiert UND die neue noch fehlt
        for alt, neu in rename_map.items():
            if alt in df.columns and neu not in df.columns:
                df = df.rename(columns={alt: neu})
        
        # Sicherstellen, dass neue Spalten zumindest als Spalte existieren (Default 0.0)
        for col in ["Day Netto €", "Swing Netto €", "Anzahl Hist. Prognosen"]:
            if col not in df.columns:
                df[col] = 0.0 if "€" in col or "%" in col else 0
                
        return df
    except Exception:
        return pd.DataFrame()

def _schreibe_csv(df, dateipfad):
    logical_name = storage.logical_name_from_path(dateipfad)
    if logical_name and storage.schreibe_tabelle(logical_name, df):
        return

    _stelle_data_ordner_sicher()
    df.to_csv(dateipfad, index=False)

def _zu_float(wert, standard=0.0):
    try:
        return float(wert)
    except Exception:
        return standard

def lade_prognosehistorie(datei_auswertung=DATEI_AUSWERTUNG):
    df = _lese_csv_sicher(datei_auswertung)
    if df.empty:
        return pd.DataFrame()
    if "Prognose-Zeitstempel" in df.columns:
        df = df.sort_values("Prognose-Zeitstempel", ascending=False)
    elif "Prognose-Datum" in df.columns:
        df = df.sort_values("Prognose-Datum", ascending=False)
    return df.reset_index(drop=True)

# =========================================================
# 04_PROGNOSEN_SPEICHERN
# =========================================================
def speichere_prognosen(df_signale, settings=None, dateiname=DATEI_PROGNOSEN):
    _stelle_data_ordner_sicher()

    if df_signale is None or df_signale.empty:
        return pd.DataFrame()

    settings = settings or {}

    prognose_datum = _heute_str()
    prognose_zeit = _uhrzeit_str()
    prognose_zeitstempel = _zeitstempel_str()

    benoetigte_spalten = [
        "Ticker", "Land", "Handelsfenster", "Letzter Kurs €",
        "Day Kauf", "Day Score", "Day Signalstärke", "Day Kommentar", 
        "Day Stop Loss €", "Day Take Profit €", "Day CRV", "Day Erwartung €", 
        "Day Netto €", "Day Potenzial €",
        "Swing Kauf", "Swing Score", "Swing Signalstärke", "Swing Kommentar", 
        "Swing Stop Loss €", "Swing Take Profit €", "Swing CRV", "Swing Potenzial €",
        "ATR relativ %", "Ø Tagesrange %", "Hit-Rate > 2 %", "RSI 14", 
        "Volatilität %", "Perf 20 Tage %", "Trend Up", "Trend Stabil", 
        "News-Score", "Saison-Score",
    ]

    vorhandene_spalten = [sp for sp in benoetigte_spalten if sp in df_signale.columns]
    df_export = df_signale[vorhandene_spalten].copy()

    df_export["Prognose-Datum"] = prognose_datum
    df_export["Prognose-Zeit"] = prognose_zeit
    df_export["Prognose-Zeitstempel"] = prognose_zeitstempel
    df_export["Analysezeitraum"] = settings.get("analyse_zeitraum", "1y")

    # Snapshot der aktiven Filter / Standardwerte
    for k in ["day_min_atr_rel", "day_min_range", "day_min_hitrate2", "day_min_crv", "day_min_potenzial",
              "swing_min_crv", "swing_min_potenzial", "swing_min_rsi", "swing_max_rsi"]:
        df_export[k] = settings.get(k)

    alt = _lese_csv_sicher(dateiname)

    if alt.empty:
        neu = df_export.copy()
    else:
        neu = pd.concat([alt, df_export], ignore_index=True)
        if "Ticker" in neu.columns and "Prognose-Zeitstempel" in neu.columns:
            neu = neu.drop_duplicates(subset=["Ticker", "Prognose-Zeitstempel"], keep="last")

    if "Prognose-Zeitstempel" in neu.columns:
        neu = neu.sort_values("Prognose-Zeitstempel", ascending=False)

    _schreibe_csv(neu, dateiname)
    return neu

# =========================================================
# 05_BACKUP_UND_LOESCHEN
# =========================================================
def _erstelle_backup(dateipfad):
    """Erstellt ein Backup der CSV im Backup-Ordner."""
    if not Path(dateipfad).exists():
        return None
    _stelle_data_ordner_sicher()
    zeitstempel = _jetzt_berlin().strftime("%Y%m%d_%H%M%S")
    dateiname = Path(dateipfad).name
    backup_pfad = BACKUP_ORDNER / f"{zeitstempel}_{dateiname}"
    shutil.copy2(dateipfad, backup_pfad)
    return backup_pfad

def loesche_historische_daten(von_datum, bis_datum):
    """
    Löscht Einträge in den CSV-Dateien zwischen von_datum und bis_datum.
    Erstellt vorher Backups.
    """
    dateien = [DATEI_PROGNOSEN, DATEI_AUSWERTUNG]
    backups_erstellt = []
    eintraege_geloescht = 0

    von_dt = pd.to_datetime(von_datum).strftime("%Y-%m-%d")
    bis_dt = pd.to_datetime(bis_datum).strftime("%Y-%m-%d")

    for dateipfad in dateien:
        df = _lese_csv_sicher(dateipfad)
        if df.empty or "Prognose-Datum" not in df.columns:
            continue

        # Backup
        backup_pfad = _erstelle_backup(dateipfad)
        if backup_pfad:
            backups_erstellt.append(str(backup_pfad))

        # Löschen
        mask = (df["Prognose-Datum"] >= von_dt) & (df["Prognose-Datum"] <= bis_dt)
        anzahl_geloescht = mask.sum()

        if anzahl_geloescht > 0:
            df_neu = df[~mask]
            _schreibe_csv(df_neu, dateipfad)
            eintraege_geloescht += anzahl_geloescht

    return {
        "geloescht": int(eintraege_geloescht),
        "backups": backups_erstellt
    }

# =========================================================
# 06_HEUTIGEN_SNAPSHOT_LADEN
# =========================================================
def lade_heutigen_snapshot(region=None):
    """
    Lädt bereits für heute gespeicherte Prognosen aus der Historie.
    Ermöglicht die Anzeige stabiler Werte nach der Fixierung.
    """
    df = _lese_csv_sicher(DATEI_PROGNOSEN)
    if df.empty or "Prognose-Datum" not in df.columns:
        return pd.DataFrame()
    
    heute = _heute_str()
    # Nur die aktuellsten Einträge pro Ticker für heute nehmen
    df_heute = df[df["Prognose-Datum"] == heute].copy()
    
    if df_heute.empty:
        return pd.DataFrame()

    if "Prognose-Zeitstempel" in df_heute.columns:
        df_heute = df_heute.sort_values("Prognose-Zeitstempel", ascending=False)
        df_heute = df_heute.drop_duplicates(subset=["Ticker"], keep="first")

    if region:
        from modules.region_logik import filtere_nach_region
        df_heute = filtere_nach_region(df_heute, region)
        
    return df_heute

# =========================================================
# 07_FIXIERUNGS_METADATEN
# =========================================================
def protokolliere_fixierung(region):
    """Speichert den Zeitpunkt der Fixierung für eine Region in den Metadaten."""
    import json
    _stelle_data_ordner_sicher()
    
    meta = storage.lese_json("prognosen_metadaten", default=None)
    if not isinstance(meta, dict):
        meta = {}
    if not meta and DATEI_METADATEN.exists():
        try:
            with open(DATEI_METADATEN, "r") as f:
                meta = json.load(f)
        except:
            pass
            
    heute = _heute_str()
    uhrzeit = _uhrzeit_str()
    
    if "fixierungen" not in meta:
        meta["fixierungen"] = {}
    
    if heute not in meta["fixierungen"]:
        meta["fixierungen"][heute] = {}
        
    meta["fixierungen"][heute][region] = uhrzeit
    
    if not storage.schreibe_json("prognosen_metadaten", meta):
        with open(DATEI_METADATEN, "w") as f:
            json.dump(meta, f, indent=2)

def hole_fixierungs_status(region=None):
    """
    Gibt die Uhrzeit der heutigen Fixierung zurück.
    Falls region=None, wird das gesamte Dictionary für heute zurückgegeben.
    """
    import json
    meta = storage.lese_json("prognosen_metadaten", default=None)
    if not isinstance(meta, dict):
        if not DATEI_METADATEN.exists():
            return None
        try:
            with open(DATEI_METADATEN, "r") as f:
                meta = json.load(f)
        except:
            return None
        
    heute = _heute_str()
    fix_heute = meta.get("fixierungen", {}).get(heute, {})
    
    if region:
        return fix_heute.get(region)
    return fix_heute

# =========================================================
# 08_BACKUP_WIEDERHERSTELLUNG
# =========================================================
def liste_backups_auf():
    """Listet Backups auf, gruppiert nach Zeitstempel."""
    if not BACKUP_ORDNER.exists():
        return []
    
    files = list(BACKUP_ORDNER.glob("*.csv"))
    if not files:
        return []
        
    # Gruppieren nach Zeitstempel (Format: YYYYMMDD_HHMMSS)
    gruppen = {}
    for f in files:
        teile = f.name.split("_")
        if len(teile) >= 2:
            ts = f"{teile[0]}_{teile[1]}"
            if ts not in gruppen:
                gruppen[ts] = {"dateien": [], "datum_formatiert": ""}
            
            gruppen[ts]["dateien"].append(f.name)
            if not gruppen[ts]["datum_formatiert"]:
                stats = f.stat()
                gruppen[ts]["datum_formatiert"] = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
    
    ergebnis = []
    for ts, info in gruppen.items():
        ergebnis.append({
            "zeitstempel": ts,
            "anzeige_name": f"Snapshot vom {info['datum_formatiert']} ({len(info['dateien'])} Dateien)",
            "dateien": info["dateien"]
        })
        
    return sorted(ergebnis, key=lambda x: x["zeitstempel"], reverse=True)

def stelle_backup_wieder_her(zeitstempel):
    """Stellt alle Dateien eines Zeitstempels wieder her."""
    if not BACKUP_ORDNER.exists():
        return False, "Backup-Ordner nicht gefunden."
    
    dateien_im_backup = list(BACKUP_ORDNER.glob(f"{zeitstempel}_*.csv"))
    if not dateien_im_backup:
        return False, f"Keine Dateien für Zeitstempel {zeitstempel} gefunden."
    
    erfolge = []
    fehler = []
    
    for quelle in dateien_im_backup:
        # Ziel bestimmen
        if "prognosen_historie" in quelle.name:
            ziel = DATEI_PROGNOSEN
        elif "prognosen_auswertung" in quelle.name:
            ziel = DATEI_AUSWERTUNG
        else:
            continue # Überspringen falls unbekannt
            
        try:
            # Sicherheits-Backup vom aktuellen Stand
            if ziel.exists():
                _erstelle_backup(str(ziel))
            
            shutil.copy2(quelle, ziel)
            erfolge.append(ziel.name)
        except Exception as e:
            fehler.append(f"{quelle.name}: {str(e)}")
            
    if fehler:
        return False, "; ".join(fehler)
    return True, f"Erfolgreich wiederhergestellt: {', '.join(erfolge)}"
