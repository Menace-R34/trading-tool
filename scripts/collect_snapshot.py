import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.logic.automation import check_automation_loop


def main():
    fixiert = check_automation_loop()
    if fixiert:
        print(f"Fixiert: {', '.join(fixiert)}")
    else:
        print("Keine Fixierung faellig.")


if __name__ == "__main__":
    main()
