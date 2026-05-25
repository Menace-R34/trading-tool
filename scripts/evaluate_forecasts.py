import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from modules.prognose_auswertung import fuehre_tagespruefung_aus


def main():
    ausgefuehrt = fuehre_tagespruefung_aus()
    if ausgefuehrt:
        print("Prognoseauswertung ausgefuehrt.")
    else:
        print("Prognoseauswertung heute bereits erledigt.")


if __name__ == "__main__":
    main()
