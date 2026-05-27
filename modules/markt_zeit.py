# =========================================================
# 01_IMPORTS
# =========================================================
from datetime import datetime

from modules.prognose_speicher import ZEITZONE_BERLIN, ZEITZONE_NEW_YORK


# =========================================================
# 02_ZEITFUNKTIONEN
# =========================================================
def hole_zeit_berlin():
    return datetime.now(ZEITZONE_BERLIN)


def hole_zeit_new_york():
    return datetime.now(ZEITZONE_NEW_YORK)


# =========================================================
# 03_MARKTSTATUS
# =========================================================
def ist_eu_markt_offen():
    jetzt = hole_zeit_berlin()

    if jetzt.weekday() >= 5:
        return False

    minuten = jetzt.hour * 60 + jetzt.minute
    start = 9 * 60
    ende = 17 * 60 + 30

    return start <= minuten <= ende


def ist_us_kernmarkt_offen():
    jetzt = hole_zeit_new_york()

    if jetzt.weekday() >= 5:
        return False

    minuten = jetzt.hour * 60 + jetzt.minute
    start = 9 * 60 + 30
    ende = 16 * 60

    return start <= minuten <= ende


# =========================================================
# 04_HANDELSFENSTER
# =========================================================
def bestimme_handelsfenster(land):
    land = str(land).strip().upper()

    if land == "US":
        jetzt_ny = hole_zeit_new_york()
        if jetzt_ny.weekday() >= 5:
            return "US geschlossen"
            
        minuten_ny = jetzt_ny.hour * 60 + jetzt_ny.minute
        
        if 570 <= minuten_ny <= 960:      # 09:30 - 16:00 NY (15:30 - 22:00 DE)
            return "US offen"
        elif 240 <= minuten_ny < 570:     # 04:00 - 09:30 NY (10:00 - 15:30 DE)
            return "US vor Open"
        elif 960 < minuten_ny <= 1200:    # 16:00 - 20:00 NY (22:00 - 02:00 DE)
            return "US nachbörslich"
        else:
            return "US geschlossen"

    if land in ["DE", "EU", "FR", "NL", "IT", "ES", "CH", "UK"]:
        jetzt_berlin = hole_zeit_berlin()
        if jetzt_berlin.weekday() >= 5:
            return "Europa geschlossen"
            
        minuten_de = jetzt_berlin.hour * 60 + jetzt_berlin.minute
        
        if 540 <= minuten_de <= 1050:      # 09:00 - 17:30
            return "Europa offen"
        elif 480 <= minuten_de < 540:      # 08:00 - 09:00
            return "Europa vor Open"
        elif 1050 < minuten_de <= 1140:    # 17:30 - 19:00
            return "Europa nachbörslich"
        elif 1140 < minuten_de <= 1320:    # 19:00 - 22:00
            return "Europa spätbörslich"
        else:
            return "Europa geschlossen"

    return "Unbekannt"
