import json
import os
import sys
from pathlib import Path

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
    Path("data").mkdir(parents=True, exist_ok=True)

    for logical_name, path in TABLE_FILES.items():
        df = storage.lese_tabelle(logical_name)
        if df is None:
            print(f"Ueberspringe {logical_name}: keine Tabelle gefunden.")
            continue
        df.to_csv(path, index=False)
        print(f"Importiert: {logical_name} -> {path}")

    for logical_name, path in JSON_FILES.items():
        daten = storage.lese_json(logical_name, default=None)
        if daten is None:
            print(f"Ueberspringe {logical_name}: keine JSON-Daten gefunden.")
            continue
        with path.open("w", encoding="utf-8") as handle:
            json.dump(daten, handle, ensure_ascii=False, indent=2)
        print(f"Importiert: {logical_name} -> {path}")


if __name__ == "__main__":
    main()
