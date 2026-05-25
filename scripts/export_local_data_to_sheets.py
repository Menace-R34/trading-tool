import json
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from modules import storage


TABLE_FILES = {
    "trade_republic_universum": Path("data/trade_republic_universum.csv"),
    "prognosen_historie": Path("data/prognosen_historie.csv"),
    "prognosen_auswertung": Path("data/prognosen_auswertung.csv"),
}

JSON_FILES = {
    "standardwerte_vorschlag": Path("data/standardwerte_vorschlag.json"),
    "prognosen_metadaten": Path("data/prognosen_metadaten.json"),
    "optimierungsvorschlaege_historie": Path("data/optimierungsvorschlaege_historie.json"),
}


def main():
    os.environ["TRADING_TOOL_STORAGE"] = "google_sheets"

    for logical_name, path in TABLE_FILES.items():
        if not path.exists():
            print(f"Ueberspringe {path}: Datei fehlt.")
            continue
        df = pd.read_csv(path)
        storage.schreibe_tabelle(logical_name, df)
        print(f"Exportiert: {path} -> {logical_name}")

    for logical_name, path in JSON_FILES.items():
        if not path.exists():
            print(f"Ueberspringe {path}: Datei fehlt.")
            continue
        with path.open("r", encoding="utf-8") as handle:
            daten = json.load(handle)
        storage.schreibe_json(logical_name, daten)
        print(f"Exportiert: {path} -> {logical_name}")


if __name__ == "__main__":
    main()
