import threading
import time
import datetime
import os
import pandas as pd
from pathlib import Path

from modules.prognose_speicher import (
    speichere_prognosen,
    protokolliere_fixierung,
    hole_fixierungs_status,
    lade_gespeicherte_standardwerte,
    _jetzt_berlin,
    _jetzt_new_york
)
from modules.universum import hole_tickerliste_aus_universum
from modules.logic.analysis import berechne_vollstaendige_analyse
from modules.region_logik import filtere_nach_region

# Globaler Status, um Mehrfachstarts zu verhindern
_worker_gestartet = False
_worker_lock = threading.Lock()
AUTOMATION_LOCK = Path("data/automation_check.lock")
AUTOMATION_LOCK_MAX_AGE_SECONDS = 3 * 60 * 60

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

def führe_fixierung_durch(region, zeitraum="1y"):
    """
    Führt die eigentliche Fixierung für eine Region durch.
    Holt frische Daten und speichert sie.
    """
    print(f"[{datetime.datetime.now()}] Starte Fixierung für {region}...")
    
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
        
        # Speichern
        speichere_prognosen(df_region, einstellungen)
        protokolliere_fixierung(region)
        
        print(f"✅ Fixierung für {region} erfolgreich abgeschlossen.")
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

    heutige_fixierungen = hole_fixierungs_status() or {}
    if all(region in heutige_fixierungen for region in ["Europa", "USA"]):
        return []

    jetzt_be = _jetzt_berlin()
    jetzt_ny = _jetzt_new_york()
    
    offset_eu = einstellungen.get("auto_fix_offset_eu", 20)
    offset_us = einstellungen.get("auto_fix_offset_us", 20)

    # Zeiten berechnen
    target_eu_h = 9 + (offset_eu // 60)
    target_eu_m = offset_eu % 60
    
    total_us_m = 30 + offset_us
    target_us_h = 9 + (total_us_m // 60)
    target_us_m = total_us_m % 60

    pläne = [
        {"region": "Europa", "jetzt": jetzt_be, "h": target_eu_h, "m": target_eu_m},
        {"region": "USA",    "jetzt": jetzt_ny, "h": target_us_h, "m": target_us_m}
    ]

    regionen_fixiert = []

    for plan in pläne:
        region = plan["region"]
        jetzt = plan["jetzt"]
        
        if region in heutige_fixierungen:
            continue
            
        # Verhindert, dass nachts (z.B. 00:01 Berlin) aufgrund der NY-Zeit vom Vortag (18:01) fixiert wird.
        if jetzt.date() < _jetzt_berlin().date():
            continue
            
        if jetzt.hour > plan["h"] or (jetzt.hour == plan["h"] and jetzt.minute >= plan["m"]):
            erfolg = führe_fixierung_durch(region, einstellungen.get("analyse_zeitraum", "1y"))
            if erfolg:
                regionen_fixiert.append(region)
                heutige_fixierungen[region] = True
                
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
