# =========================================================
# 01_IMPORTS
# =========================================================
import json
import pandas as pd
from pathlib import Path

from modules.prognose_speicher import _lese_csv_sicher, _zeitstempel_str, DATA_ORDNER, DATEI_AUSWERTUNG

# =========================================================
# 02_KONSTANTEN
# =========================================================
DATEI_VORSCHLAEGE_HISTORIE = DATA_ORDNER / "optimierungsvorschlaege_historie.json"

# =========================================================
# 03_VORSCHLAEGE HISTORIE LADEN / SPEICHERN
# =========================================================
def lade_vorschlaege_historie():
    if not Path(DATEI_VORSCHLAEGE_HISTORIE).exists():
        return []
    try:
        with open(DATEI_VORSCHLAEGE_HISTORIE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _speichere_vorschlaege_historie(historie):
    DATA_ORDNER.mkdir(parents=True, exist_ok=True)
    with open(DATEI_VORSCHLAEGE_HISTORIE, "w", encoding="utf-8") as f:
        json.dump(historie, f, ensure_ascii=False, indent=2)

# =========================================================
# 04_OPTIMIERUNGSVORSCHLAEGE BERECHNEN
# =========================================================
def hole_standardwerte_vorschlag_basis():
    return {
        "day_min_atr_rel": 1.8,
        "day_min_range": 1.5,
        "day_min_hitrate2": 30.0,
        "day_min_crv": 1.3,
        "day_min_potenzial": 5.0,
        "swing_min_crv": 1.5,
        "swing_min_potenzial": 10.0,
        "swing_min_rsi": 30,
        "swing_max_rsi": 75,
        "day_haltedauer": 3,
        "swing_haltedauer": 10,
    }

def schlage_standardwerte_vor(datei_auswertung=DATEI_AUSWERTUNG, force=False):
    """
    Berechnet basierend auf erfolgreichen Trades neue Filter-Werte.
    Speichert den Vorschlag in der Historie.
    Wenn force=False, wird nur berechnet, wenn genügend NEUE Treffer 
    seit dem letzten Vorschlag gesammelt wurden.
    """
    df = _lese_csv_sicher(datei_auswertung)
    if df.empty:
        return {}

    day_treffer = df[df["Day Treffer"] == 1].copy() if "Day Treffer" in df.columns else pd.DataFrame()
    swing_treffer = df[df["Swing Treffer"] == 1].copy() if "Swing Treffer" in df.columns else pd.DataFrame()

    total_hits = len(day_treffer) + len(swing_treffer)
    if total_hits < 5:
        return {}

    # Check against history if not forced
    historie = lade_vorschlaege_historie()
    if not force and historie:
        letzter_vorschlag = historie[-1]
        letzte_basis_groesse = letzter_vorschlag.get("Datenbasis_Treffer", 0)
        # Wenn weniger als 10 neue Treffer dazu kamen, keinen neuen Vorschlag generieren
        if total_hits - letzte_basis_groesse < 10:
            return letzter_vorschlag.get("Werte", {})

    vorschlag = hole_standardwerte_vorschlag_basis()

    if len(day_treffer) >= 5:
        if "ATR relativ %" in day_treffer.columns:
            vorschlag["day_min_atr_rel"] = round(max(1.0, day_treffer["ATR relativ %"].median() * 0.8), 2)
        if "Ø Tagesrange %" in day_treffer.columns:
            vorschlag["day_min_range"] = round(max(1.0, day_treffer["Ø Tagesrange %"].median() * 0.8), 2)
        if "Hit-Rate > 2 %" in day_treffer.columns:
            vorschlag["day_min_hitrate2"] = round(max(20.0, day_treffer["Hit-Rate > 2 %"].median() * 0.8), 2)
        if "Day CRV" in day_treffer.columns:
            vorschlag["day_min_crv"] = round(max(1.1, day_treffer["Day CRV"].median() * 0.9), 2)
        if "Day Potenzial €" in day_treffer.columns:
            vorschlag["day_min_potenzial"] = round(max(3.0, day_treffer["Day Potenzial €"].median() * 0.8), 2)
        if "Day Haltedauer" in day_treffer.columns:
            # Optimierung: Nimm den Median der Treffer für maximale Effizienz
            vorschlag["day_haltedauer"] = int(max(1, day_treffer["Day Haltedauer"].median()))

    if len(swing_treffer) >= 5:
        if "Swing CRV" in swing_treffer.columns:
            vorschlag["swing_min_crv"] = round(max(1.2, swing_treffer["Swing CRV"].median() * 0.9), 2)
        if "Swing Potenzial €" in swing_treffer.columns:
            vorschlag["swing_min_potenzial"] = round(max(5.0, swing_treffer["Swing Potenzial €"].median() * 0.8), 2)
        if "RSI 14" in swing_treffer.columns:
            vorschlag["swing_min_rsi"] = int(max(20, swing_treffer["RSI 14"].quantile(0.20)))
            vorschlag["swing_max_rsi"] = int(min(80, swing_treffer["RSI 14"].quantile(0.80)))
        if "Swing Haltedauer" in swing_treffer.columns:
            # Optimierung: Nimm den Median der Treffer
            vorschlag["swing_haltedauer"] = int(max(2, swing_treffer["Swing Haltedauer"].median()))

    neuer_eintrag = {
        "Vorschlags_ID": _zeitstempel_str().replace(":", "").replace(" ", "_").replace("-", ""),
        "Zeitstempel": _zeitstempel_str(),
        "Bereich": "Kombiniert",
        "Werte": vorschlag,
        "Datenbasis_Treffer": total_hits,
        "Automatisch_Generiert": not force
    }

    # Dublettencheck
    if historie:
        letzte_werte = historie[-1].get("Werte", {})
        if letzte_werte == vorschlag:
            return vorschlag # Nichts tun, ist identisch

    historie.append(neuer_eintrag)
    _speichere_vorschlaege_historie(historie)
    return vorschlag
