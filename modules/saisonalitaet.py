# =========================================================
# 01_IMPORTS
# =========================================================
import pandas as pd

from modules.markt_daten import hole_close_serie


# =========================================================
# 02_KONSTANTEN
# =========================================================
MONATSNAMEN = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}

WINTER_MONATE = [11, 12, 1, 2, 3, 4]
SOMMER_MONATE = [5, 6, 7, 8, 9, 10]


# =========================================================
# 03_HILFSFUNKTIONEN
# =========================================================
def monat_als_text(monatsnummer):
    return MONATSNAMEN.get(int(monatsnummer), str(monatsnummer))


def bestimme_monatsdrittel(tag_im_monat):
    """
    1 = Monatsanfang
    2 = Monatsmitte
    3 = Monatsende
    """
    if tag_im_monat <= 10:
        return 1
    if tag_im_monat <= 20:
        return 2
    return 3


def berechne_trefferquote(serie):
    if serie is None or len(serie) == 0:
        return 0.0
    return float((serie > 0).mean() * 100)


def mittelwert_fuer_monate(monatsrenditen, monatsliste):
    daten = monatsrenditen[monatsrenditen.index.month.isin(monatsliste)]
    if daten.empty:
        return 0.0
    return float(daten.mean())


# =========================================================
# 04_SAISONALITAET
# =========================================================
def berechne_saisonalitaet(df, jahre_fokus=3):
    """
    Erweiterte Saisonalitätsanalyse auf Basis historischer Monatsrenditen.

    Rückgabe:
        dict mit saisonalen Kennzahlen für Ranking und Signal-Logik
    """
    fallback = {
        "Saison-Score": 0.0,
        "Saison-Label": "Neutral",
        "Aktueller Monat": "",
        "Nächster Monat": "",
        "Starke Monate": "",
        "Schwache Monate": "",
        "Trefferquote aktueller Monat %": 0.0,
        "Ø Monatsrendite aktueller Monat %": 0.0,
        "Median Monatsrendite aktueller Monat %": 0.0,
        "Ø Monatsrendite nächster Monat %": 0.0,
        "Trefferquote nächster Monat %": 0.0,
        "Winterhalbjahr Ø %": 0.0,
        "Sommerhalbjahr Ø %": 0.0,
        "Saison-Favorit": "Neutral",
        "Monatsanfang Ø %": 0.0,
        "Monatsmitte Ø %": 0.0,
        "Monatsende Ø %": 0.0,
        "Monatsdrittel-Bias": "Neutral",
        "Historische Monate berücksichtigt": 0,
    }

    if df is None or df.empty:
        return fallback

    close_serie = hole_close_serie(df)
    if close_serie.empty or len(close_serie) < 252:
        return fallback

    close_serie = close_serie.sort_index()

    # -----------------------------------------------------
    # Historie auf Fokuszeitraum begrenzen
    # -----------------------------------------------------
    letztes_datum = close_serie.index.max()
    start_datum = letztes_datum - pd.DateOffset(years=jahre_fokus)
    close_fokus = close_serie[close_serie.index >= start_datum].copy()

    if close_fokus.empty or len(close_fokus) < 252:
        return fallback

    # -----------------------------------------------------
    # Monatsultimo-Kurse und Monatsrenditen
    # -----------------------------------------------------
    monats_close = close_fokus.resample("ME").last().dropna()
    if len(monats_close) < 12:
        return fallback

    monatsrenditen = monats_close.pct_change().dropna() * 100
    if monatsrenditen.empty:
        return fallback

    gruppiert = monatsrenditen.groupby(monatsrenditen.index.month)

    durchschnitt_monat = gruppiert.mean()
    median_monat = gruppiert.median()
    trefferquote_monat = gruppiert.apply(berechne_trefferquote)
    anzahl_monate = gruppiert.count()

    if durchschnitt_monat.empty:
        return fallback

    # -----------------------------------------------------
    # Aktueller und nächster Monat
    # -----------------------------------------------------
    aktuelle_monatsnummer = int(close_fokus.index[-1].month)
    naechste_monatsnummer = 1 if aktuelle_monatsnummer == 12 else aktuelle_monatsnummer + 1

    aktueller_monat_rendite = float(durchschnitt_monat.get(aktuelle_monatsnummer, 0.0))
    aktueller_monat_median = float(median_monat.get(aktuelle_monatsnummer, 0.0))
    aktueller_monat_trefferquote = float(trefferquote_monat.get(aktuelle_monatsnummer, 0.0))
    aktueller_monat_anzahl = int(anzahl_monate.get(aktuelle_monatsnummer, 0))

    naechster_monat_rendite = float(durchschnitt_monat.get(naechste_monatsnummer, 0.0))
    naechster_monat_trefferquote = float(trefferquote_monat.get(naechste_monatsnummer, 0.0))

    # -----------------------------------------------------
    # Saison-Favorit Winter/Sommer
    # -----------------------------------------------------
    winter_avg = mittelwert_fuer_monate(monatsrenditen, WINTER_MONATE)
    sommer_avg = mittelwert_fuer_monate(monatsrenditen, SOMMER_MONATE)

    if winter_avg > sommer_avg + 0.25:
        saison_favorit = "Winterhalbjahr"
    elif sommer_avg > winter_avg + 0.25:
        saison_favorit = "Sommerhalbjahr"
    else:
        saison_favorit = "Neutral"

    # -----------------------------------------------------
    # Monatsdrittel-Bias auf Tagesbasis
    # -----------------------------------------------------
    tagesrenditen = close_fokus.pct_change().dropna() * 100
    if not tagesrenditen.empty:
        drittel_df = pd.DataFrame({
            "Rendite": tagesrenditen
        })
        drittel_df["Monatsdrittel"] = drittel_df.index.day.map(bestimme_monatsdrittel)

        drittel_stats = drittel_df.groupby("Monatsdrittel")["Rendite"].mean()

        monatsanfang_avg = float(drittel_stats.get(1, 0.0))
        monatsmitte_avg = float(drittel_stats.get(2, 0.0))
        monatsende_avg = float(drittel_stats.get(3, 0.0))
    else:
        monatsanfang_avg = 0.0
        monatsmitte_avg = 0.0
        monatsende_avg = 0.0

    drittel_map = {
        "Monatsanfang": monatsanfang_avg,
        "Monatsmitte": monatsmitte_avg,
        "Monatsende": monatsende_avg,
    }
    bestes_drittel = max(drittel_map, key=drittel_map.get)
    schlechtestes_drittel = min(drittel_map, key=drittel_map.get)

    if drittel_map[bestes_drittel] > 0.15:
        monatsdrittel_bias = bestes_drittel
    elif drittel_map[schlechtestes_drittel] < -0.15 and abs(drittel_map[schlechtestes_drittel]) > drittel_map[bestes_drittel]:
        monatsdrittel_bias = f"Schwach: {schlechtestes_drittel}"
    else:
        monatsdrittel_bias = "Neutral"

    # -----------------------------------------------------
    # Saison-Score
    # Gewichtung:
    # - aktueller Monat
    # - nächster Monat
    # - Trefferquote
    # - Median als Robustheitskomponente
    # - leichter Bonus für bevorzugtes Halbjahr
    # - Datenqualitätsfaktor
    # -----------------------------------------------------
    basis_score = (
        aktueller_monat_rendite * 0.40
        + naechster_monat_rendite * 0.20
        + aktueller_monat_median * 0.15
        + ((aktueller_monat_trefferquote - 50) / 10) * 0.15
    )

    halbjahres_bonus = 0.0
    if saison_favorit == "Winterhalbjahr" and aktuelle_monatsnummer in WINTER_MONATE:
        halbjahres_bonus = 0.35
    elif saison_favorit == "Sommerhalbjahr" and aktuelle_monatsnummer in SOMMER_MONATE:
        halbjahres_bonus = 0.35

    drittel_bonus = 0.0
    if monatsdrittel_bias == "Monatsanfang":
        drittel_bonus = 0.10
    elif monatsdrittel_bias == "Monatsmitte":
        drittel_bonus = 0.05
    elif monatsdrittel_bias == "Monatsende":
        drittel_bonus = 0.10

    if aktueller_monat_anzahl >= 5:
        datenfaktor = 1.0
    elif aktueller_monat_anzahl >= 3:
        datenfaktor = 0.8
    else:
        datenfaktor = 0.6

    saison_score = (basis_score + halbjahres_bonus + drittel_bonus) * datenfaktor

    # -----------------------------------------------------
    # Saison-Label
    # -----------------------------------------------------
    if saison_score >= 1.5:
        saison_label = "Positiv"
    elif saison_score <= -1.5:
        saison_label = "Negativ"
    else:
        saison_label = "Neutral"

    # -----------------------------------------------------
    # Starke / schwache Monate
    # -----------------------------------------------------
    auswertung_df = pd.DataFrame({
        "Monat": durchschnitt_monat.index,
        "Ø Rendite": durchschnitt_monat.values,
        "Median Rendite": median_monat.reindex(durchschnitt_monat.index).values,
        "Trefferquote": trefferquote_monat.reindex(durchschnitt_monat.index).values,
        "Anzahl": anzahl_monate.reindex(durchschnitt_monat.index).values,
    })

    auswertung_df["Monatsname"] = auswertung_df["Monat"].map(monat_als_text)

    starke_df = auswertung_df.sort_values(
        by=["Ø Rendite", "Trefferquote", "Median Rendite"],
        ascending=[False, False, False]
    ).head(3)

    schwache_df = auswertung_df.sort_values(
        by=["Ø Rendite", "Trefferquote", "Median Rendite"],
        ascending=[True, True, True]
    ).head(3)

    starke_monate_text = ", ".join(starke_df["Monatsname"].tolist())
    schwache_monate_text = ", ".join(schwache_df["Monatsname"].tolist())

    return {
        "Saison-Score": round(float(saison_score), 2),
        "Saison-Label": saison_label,
        "Aktueller Monat": monat_als_text(aktuelle_monatsnummer),
        "Nächster Monat": monat_als_text(naechste_monatsnummer),
        "Starke Monate": starke_monate_text,
        "Schwache Monate": schwache_monate_text,
        "Trefferquote aktueller Monat %": round(float(aktueller_monat_trefferquote), 2),
        "Ø Monatsrendite aktueller Monat %": round(float(aktueller_monat_rendite), 2),
        "Median Monatsrendite aktueller Monat %": round(float(aktueller_monat_median), 2),
        "Ø Monatsrendite nächster Monat %": round(float(naechster_monat_rendite), 2),
        "Trefferquote nächster Monat %": round(float(naechster_monat_trefferquote), 2),
        "Winterhalbjahr Ø %": round(float(winter_avg), 2),
        "Sommerhalbjahr Ø %": round(float(sommer_avg), 2),
        "Saison-Favorit": saison_favorit,
        "Monatsanfang Ø %": round(float(monatsanfang_avg), 3),
        "Monatsmitte Ø %": round(float(monatsmitte_avg), 3),
        "Monatsende Ø %": round(float(monatsende_avg), 3),
        "Monatsdrittel-Bias": monatsdrittel_bias,
        "Historische Monate berücksichtigt": int(len(monatsrenditen)),
    }