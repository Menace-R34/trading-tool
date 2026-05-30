import threading
import time
import os
import pandas as pd
from pathlib import Path

from modules.prognose_speicher import (
    speichere_prognosen,
    protokolliere_fixierung,
    hole_fixierungs_status,
    hole_profil_fixierungs_status,
    lade_gespeicherte_standardwerte,
    _jetzt_berlin,
    _jetzt_new_york,
    _zeitstempel_str
)
from modules.universum import hole_tickerliste_aus_universum
from modules.logic.analysis import berechne_vollstaendige_analyse
from modules.region_logik import filtere_nach_region

# Globaler Status, um Mehrfachstarts zu verhindern
_worker_gestartet = False
_worker_lock = threading.Lock()
AUTOMATION_LOCK = Path("data/automation_check.lock")
AUTOMATION_LOCK_MAX_AGE_SECONDS = 3 * 60 * 60
FIXIERUNGS_FENSTER_MINUTEN = 10
FIXIERUNGS_PROFILE = [
    {"profil": "EU_PRE", "region": "Europa", "zeitzone": "berlin", "h": 8, "m": 15},
    {"profil": "EU_OPEN", "region": "Europa", "zeitzone": "berlin", "h": 10, "m": 0},
    {"profil": "EU_POST", "region": "Europa", "zeitzone": "berlin", "h": 18, "m": 0},
    {"profil": "US_PRE", "region": "USA", "zeitzone": "new_york", "h": 8, "m": 45},
    {"profil": "US_OPEN", "region": "USA", "zeitzone": "new_york", "h": 9, "m": 55},
    {"profil": "US_POST", "region": "USA", "zeitzone": "new_york", "h": 16, "m": 15},
]

def start_background_worker():
    """Startet den Hintergrund-Wächter in einem eigenen Thread, falls noch nicht geschehen."""
    global _worker_gestartet
    with _worker_lock:
        if not _worker_gestartet:
            thread = threading.Thread(target=_worker_loop, daemon=True)
            thread.start()
            _worker_gestartet = True
            print("🚀 Integrierter Hintergrund-Wächter wurde gestartet.")

def _worker_loop():
    """Endlosschleife für den Hintergrund-Thread."""
    while True:
        try:
            from modules.prognose_auswertung import fuehre_tagespruefung_aus
            fuehre_tagespruefung_aus(lade_gespeicherte_standardwerte())
            check_automation_loop()
        except Exception as e:
            print(f"⚠️ Fehler im Hintergrund-Wächter: {e}")
        time.sleep(60) # Alle 60 Sekunden prüfen

def führe_fixierung_durch(region, zeitraum="1y", profil="MANUELL"):
    """
    Führt die eigentliche Fixierung für eine Region durch.
    Holt frische Daten und speichert sie.
    """
    print(f"[{_zeitstempel_str()} deutsche Zeit] Starte Fixierung für {profil}...")
    
    ticker_liste = hole_tickerliste_aus_universum()
    if not ticker_liste:
        print("Fehler: Ticker-Liste ist leer.")
        return False
        
    try:
        # Direkte Berechnung ohne Cache für maximale Aktualität
        df_live = berechne_vollstaendige_analyse(tuple(ticker_liste), zeitraum)
        df_region = filtere_nach_region(df_live, region)
        
        if df_region.empty:
            print(f"Keine Daten für Region {region} gefunden.")
            return False
            
        # Filter-Einstellungen laden (für die Historien-Metadaten)
        einstellungen = lade_gespeicherte_standardwerte()
        einstellungen["daten_geladen_zeitstempel"] = _zeitstempel_str()
        einstellungen["prognose_profil"] = profil
        
        # Speichern
        speichere_prognosen(df_region, einstellungen)
        protokolliere_fixierung(region, profil=profil)
        
        print(f"✅ Fixierung für {profil} erfolgreich abgeschlossen.")
        return True
    except Exception as e:
        print(f"❌ Fehler bei Fixierung {region}: {e}")
        return False

def check_automation_loop():
    """
    Prüft die Zeiten und führt ggf. die Fixierung aus.
    Wird vom Background-Worker aufgerufen.
    """
    lock_fd = _hole_automation_lock()
    if lock_fd is None:
        return []

    try:
        return _check_automation_loop_ohne_lock()
    finally:
        _gib_automation_lock_frei(lock_fd)


def _check_automation_loop_ohne_lock():
    einstellungen = lade_gespeicherte_standardwerte()
    if not einstellungen.get("auto_fix_aktiv", True):
        return []

    jetzt_be = _jetzt_berlin()
    if jetzt_be.weekday() >= 5:
        return []

    jetzt_ny = _jetzt_new_york()
    heutige_fixierungen = hole_profil_fixierungs_status() or {}

    regionen_fixiert = []

    for plan in FIXIERUNGS_PROFILE:
        region = plan["region"]
        profil = plan["profil"]
        jetzt = jetzt_be if plan["zeitzone"] == "berlin" else jetzt_ny
        
        if profil in heutige_fixierungen:
            continue
            
        # Verhindert, dass nachts (z.B. 00:01 Berlin) aufgrund der NY-Zeit vom Vortag (18:01) fixiert wird.
        if jetzt.date() < _jetzt_berlin().date():
            continue
            
        jetzt_minute = jetzt.hour * 60 + jetzt.minute
        ziel_minute = plan["h"] * 60 + plan["m"]
        if ziel_minute <= jetzt_minute < ziel_minute + FIXIERUNGS_FENSTER_MINUTEN:
            erfolg = führe_fixierung_durch(
                region,
                einstellungen.get("analyse_zeitraum", "1y"),
                profil=profil,
            )
            if erfolg:
                regionen_fixiert.append(profil)
                heutige_fixierungen[profil] = True
                
    return regionen_fixiert


def _hole_automation_lock():
    AUTOMATION_LOCK.parent.mkdir(parents=True, exist_ok=True)
    _entferne_verwaisten_automation_lock()
    try:
        return os.open(AUTOMATION_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None


def _gib_automation_lock_frei(lock_fd):
    os.close(lock_fd)
    try:
        AUTOMATION_LOCK.unlink()
    except FileNotFoundError:
        pass


def _entferne_verwaisten_automation_lock():
    if not AUTOMATION_LOCK.exists():
        return
    try:
        alter = time.time() - AUTOMATION_LOCK.stat().st_mtime
    except OSError:
        return
    if alter > AUTOMATION_LOCK_MAX_AGE_SECONDS:
        try:
            AUTOMATION_LOCK.unlink()
        except FileNotFoundError:
            pass


def fuehre_automatische_fixierung_aus(session_state):
    """
    Wrapper für die UI-Automatisierung. Ruft die zentrale Logik auf und
    zeigt ein Toast in der Streamlit-Benutzeroberfläche an, falls eine Region fixiert wurde.
    """
    import streamlit as st
    fixiert = check_automation_loop()
    if fixiert:
        for reg in fixiert:
            st.toast(f"✅ Prognosen für {reg} wurden fixiert!", icon="📈")
