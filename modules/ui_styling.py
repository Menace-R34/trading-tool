# =========================================================
# 01_STYLING_HILFSFUNKTIONEN
# =========================================================
import pandas as pd


def style_ja_nein_zelle(wert):
    text = str(wert).strip().upper()

    if text == "JA":
        return "background-color: #00B050; color: #FFFFFF;"

    return "background-color: #C00000; color: #FFFFFF;"


def style_signalstaerke_zelle(wert):
    text = str(wert).strip().lower()

    if text == "stark":
        return "background-color: #00B050; color: #FFFFFF;"
    if text == "mittel":
        return "background-color: #FFC000; color: #000000;"

    return "background-color: #C00000; color: #FFFFFF;"


def style_handelsfenster_zelle(wert):
    text = str(wert).strip().lower()

    if text == "us offen":
        return "background-color: #00B050; color: #FFFFFF;"
    if text == "europa offen":
        return "background-color: #00B050; color: #FFFFFF;"
    if text == "us vor open" or text == "europa vor open":
        return "background-color: #FFC000; color: #000000;"
    if text == "us nachbörslich" or text == "europa nachbörslich":
        return "background-color: #FFC000; color: #000000;"
    if text == "europa spätbörslich":
        return "background-color: #FF9900; color: #000000;"
    if text == "europa geschlossen" or text == "us geschlossen":
        return "background-color: #C00000; color: #FFFFFF;"
    if text == "unbekannt":
        return "background-color: #D9D9D9; color: #000000;"

    return ""


# =========================================================
# 02_ANZEIGE_DF_FORMATIEREN
# =========================================================
def formatiere_anzeige_df(df):
    if df.empty:
        return df

    anzeige_df = df.copy()

    # --- KOMPAKTE ABKÜRZUNGEN ---
    rename_map = {
        "Hist. Prognosegenauigkeit %": "Acc %",
        "Anzahl Hist. Prognosen": "#",
        "Handelsfenster": "Status",
        "Day Netto €": "Day €",
        "Swing Netto €": "Swing €",
        "Day Signalstärke": "Sig. (D)",
        "Swing Signalstärke": "Sig. (S)",
        "Letzter Kurs €": "Kurs €",
        "Day Score": "Score (D)",
        "Swing Score": "Score (S)",
        "Day CRV": "CRV (D)",
        "Swing CRV": "CRV (S)",
        "Hist. Idealer Hold (Day)": "Hold (D)",
        "Hist. Idealer Hold (Swing)": "Hold (S)",
        "Saison-Score": "Saison",
        "News-Score": "News"
    }
    # Nur umbenennen was da ist
    for alt, neu in rename_map.items():
        if alt in anzeige_df.columns:
            anzeige_df = anzeige_df.rename(columns={alt: neu})

    priorisierte_spalten = [
        "Ticker",
        "Land",
        "Acc %",
        "#",
        "Status",
        "Day Kauf",
        "Swing Kauf",
        "Sig. (D)",
        "Sig. (S)",
        "Score (D)",
        "Score (S)",
        "Day €",
        "Swing €",
        "Kurs €",
    ]

    restliche_spalten = [sp for sp in anzeige_df.columns if sp not in priorisierte_spalten]
    neue_reihenfolge = priorisierte_spalten + restliche_spalten
    neue_reihenfolge = [sp for sp in neue_reihenfolge if sp in anzeige_df.columns]

    return anzeige_df[neue_reihenfolge]


# =========================================================
# 03_STYLER_AUFBAUEN
# =========================================================
def baue_styler(df):
    if df.empty:
        return df

    # Erst die Spalten umbenennen und sortieren
    anzeige_df = formatiere_anzeige_df(df)
    
    # Formatierung definieren
    format_dict = {
        "Kurs €": "{:.2f}",
        "Day €": "{:.2f}",
        "Swing €": "{:.2f}",
        "Acc %": "{:.1f}",
        "#": "{:d}",
        "Score (D)": "{:.1f}",
        "Score (S)": "{:.1f}",
        "CRV (D)": "{:.2f}",
        "CRV (S)": "{:.2f}",
        "Hold (D)": "{:d}",
        "Hold (S)": "{:d}",
        "Ø Tagesrange %": "{:.2f}",
        "ATR relativ %": "{:.2f}",
        "RSI 14": "{:.2f}",
        "Saison": "{:.2f}",
        "News": "{:.2f}",
    }

    # NaN-Werte in den zu formatierenden Spalten abfangen
    for col in format_dict.keys():
        if col in anzeige_df.columns:
            anzeige_df[col] = pd.to_numeric(
                anzeige_df[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )
            # Für Ganzzahlen 0, für Floats 0.0
            fill_val = 0 if format_dict[col] == "{:d}" else 0.0
            anzeige_df[col] = anzeige_df[col].fillna(fill_val)
    
    # Dann den Styler auf dem umbenannten DF erstellen
    styler = anzeige_df.style

    # Styling-Regeln an neue Namen anpassen
    if "Day Kauf" in anzeige_df.columns:
        styler = styler.map(style_ja_nein_zelle, subset=["Day Kauf"])
    if "Swing Kauf" in anzeige_df.columns:
        styler = styler.map(style_ja_nein_zelle, subset=["Swing Kauf"])
    if "Sig. (D)" in anzeige_df.columns:
        styler = styler.map(style_signalstaerke_zelle, subset=["Sig. (D)"])
    if "Sig. (S)" in anzeige_df.columns:
        styler = styler.map(style_signalstaerke_zelle, subset=["Sig. (S)"])
    if "Status" in anzeige_df.columns:
        styler = styler.map(style_handelsfenster_zelle, subset=["Status"])

    vorhandene_formatierung = {
        key: value
        for key, value in format_dict.items()
        if key in anzeige_df.columns
    }

    if vorhandene_formatierung:
        styler = styler.format(vorhandene_formatierung)

    return styler
