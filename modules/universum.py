# =========================================================
# 01_IMPORTS
# =========================================================
import pandas as pd
from modules import storage


# =========================================================
# 02_KONSTANTEN
# =========================================================
STANDARD_DATEIPFAD = "data/trade_republic_universum.csv"

BENOETIGTE_SPALTEN = [
    "Ticker",
    "Name",
]

OPTIONALE_SPALTEN = [
    "ISIN",
    "Typ",
    "Sektor",
    "Land",
    "Waehrung",
    "Aktiv",
    "Analysieren",
    "Quelle",
]


# =========================================================
# 03_CSV_LADEN
# =========================================================
def lade_universum_csv(dateipfad=STANDARD_DATEIPFAD):
    """
    Lädt das Universum aus einer CSV-Datei.
    """
    df = storage.lese_tabelle("trade_republic_universum")
    if df is None:
        df = pd.read_csv(dateipfad)

    fehlende_spalten = [sp for sp in BENOETIGTE_SPALTEN if sp not in df.columns]
    if fehlende_spalten:
        raise ValueError(
            f"Fehlende Pflichtspalten in der Universum-Datei: {', '.join(fehlende_spalten)}"
        )

    return df


# =========================================================
# 04_BOOL_HILFSFUNKTION
# =========================================================
def _zu_bool_standard(wert, default=True):
    """
    Wandelt typische CSV-Werte robust in Bool um.
    """
    if pd.isna(wert):
        return default

    text = str(wert).strip().lower()

    if text in ["true", "1", "ja", "yes", "y", "x"]:
        return True
    if text in ["false", "0", "nein", "no", "n"]:
        return False

    return default


# =========================================================
# 05_UNIVERSUM_BEREINIGEN
# =========================================================
def bereinige_universum(df):
    """
    Bereinigt das geladene Universum:
    - Pflichtfelder prüfen
    - Ticker standardisieren
    - optionale Spalten ergänzen
    - Dubletten entfernen
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=BENOETIGTE_SPALTEN + OPTIONALE_SPALTEN)

    df = df.copy()

    # -----------------------------------------------------
    # Pflichtspalten bereinigen
    # -----------------------------------------------------
    for spalte in BENOETIGTE_SPALTEN:
        df[spalte] = df[spalte].astype(str).str.strip()

    df = df.dropna(subset=["Ticker", "Name"])
    df = df[
        (df["Ticker"] != "")
        & (df["Name"] != "")
    ].copy()

    # -----------------------------------------------------
    # Optionale Spalten ergänzen
    # -----------------------------------------------------
    for spalte in OPTIONALE_SPALTEN:
        if spalte not in df.columns:
            if spalte in ["Aktiv", "Analysieren"]:
                df[spalte] = True
            else:
                df[spalte] = ""

    # -----------------------------------------------------
    # Standardisierung
    # -----------------------------------------------------
    df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    df["Name"] = df["Name"].astype(str).str.strip()
    df["ISIN"] = df["ISIN"].astype(str).str.strip().str.upper()
    df["Typ"] = df["Typ"].astype(str).str.strip()
    df["Sektor"] = df["Sektor"].astype(str).str.strip()
    df["Land"] = df["Land"].astype(str).str.strip().str.upper()
    df["Waehrung"] = df["Waehrung"].astype(str).str.strip().str.upper()
    df["Quelle"] = df["Quelle"].astype(str).str.strip()

    # -----------------------------------------------------
    # Bool-Spalten vereinheitlichen
    # -----------------------------------------------------
    df["Aktiv"] = df["Aktiv"].apply(_zu_bool_standard, default=True)
    df["Analysieren"] = df["Analysieren"].apply(_zu_bool_standard, default=True)

    # -----------------------------------------------------
    # Dubletten entfernen
    # -----------------------------------------------------
    if "ISIN" in df.columns and (df["ISIN"].fillna("").str.strip() != "").any():
        df = df.drop_duplicates(subset=["Ticker", "ISIN"]).reset_index(drop=True)
    else:
        df = df.drop_duplicates(subset=["Ticker"]).reset_index(drop=True)

    return df


# =========================================================
# 06_AKTIEN_UNIVERSUM_FILTER
# =========================================================
def filtere_aktien_universum(df, nur_aktive=True, nur_analysieren=True):
    """
    Filtert das Universum auf analysierbare Aktien.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "Typ" in df.columns:
        typ_bereinigt = df["Typ"].astype(str).str.strip().str.lower()
        erlaubte_typen = ["", "aktie", "stock", "equity"]
        df = df[typ_bereinigt.isin(erlaubte_typen)]

    if nur_aktive and "Aktiv" in df.columns:
        df = df[df["Aktiv"] == True]

    if nur_analysieren and "Analysieren" in df.columns:
        df = df[df["Analysieren"] == True]

    df = df.reset_index(drop=True)

    return df


# =========================================================
# 07_GESAMTFUNKTION_UNIVERSUM_LADEN
# =========================================================
def lade_trade_republic_universum(
    dateipfad=STANDARD_DATEIPFAD,
    nur_aktive=True,
    nur_analysieren=True,
):
    """
    Lädt, bereinigt und filtert das Trade-Republic-Universum.
    """
    df = lade_universum_csv(dateipfad=dateipfad)
    df = bereinige_universum(df)
    df = filtere_aktien_universum(
        df,
        nur_aktive=nur_aktive,
        nur_analysieren=nur_analysieren
    )
    return df


# =========================================================
# 08_TICKERLISTE_AUSGEBEN
# =========================================================
def hole_tickerliste_aus_universum(
    dateipfad=STANDARD_DATEIPFAD,
    nur_aktive=True,
    nur_analysieren=True,
):
    """
    Gibt die bereinigte Tickerliste aus dem Universum zurück.
    """
    df = lade_trade_republic_universum(
        dateipfad=dateipfad,
        nur_aktive=nur_aktive,
        nur_analysieren=nur_analysieren
    )

    if df.empty:
        return []

    return (
        df["Ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .drop_duplicates()
        .tolist()
    )
