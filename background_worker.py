import time
import datetime
import sys
import os
import socket
from pathlib import Path

# Projektpfad hinzufügen, damit Module auch bei Dienst-Starts gefunden werden
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from modules.logic.automation import check_automation_loop
from modules.prognose_auswertung import fuehre_tagespruefung_aus


WORKER_LOCK_PORT = 47651


def _hole_worker_lock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", WORKER_LOCK_PORT))
        sock.listen(1)
        return sock
    except OSError:
        sock.close()
        return None

def main():
    worker_lock = _hole_worker_lock()
    if worker_lock is None:
        print("Ein Hintergrund-Worker laeuft bereits. Dieser zweite Start wird beendet.")
        return

    print("=========================================================")
    print(f"🚀 Trading-Tool Hintergrund-Wächter gestartet")
    print(f"🕒 Startzeit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=========================================================")
    
    while True:
        try:
            fuehre_tagespruefung_aus()
            # Automatisierungs-Check ausführen
            check_automation_loop()
        except Exception as e:
            print(f"⚠️ Fehler im Hintergrund-Worker: {e}")
            
        # 1 Minute warten bis zum nächsten Check
        time.sleep(60)

if __name__ == "__main__":
    main()
