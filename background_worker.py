import time
import datetime
import sys
import os
import socket
import atexit
from pathlib import Path

# Projektpfad hinzufügen, damit Module auch bei Dienst-Starts gefunden werden
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from modules.logic.automation import check_automation_loop
from modules.prognose_auswertung import fuehre_tagespruefung_aus
from modules.prognose_speicher import hole_fixierungs_status


WORKER_LOCK_PORT = 47651
WORKER_PID_LOCK = PROJECT_ROOT / "data" / "background_worker.pid"


def _hole_worker_lock():
    pid_lock = _hole_worker_pid_lock()
    if pid_lock is None:
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", WORKER_LOCK_PORT))
        sock.listen(1)
        return (pid_lock, sock)
    except OSError:
        sock.close()
        _gib_worker_pid_lock_frei(pid_lock)
        return None


def _hole_worker_pid_lock():
    WORKER_PID_LOCK.parent.mkdir(parents=True, exist_ok=True)
    if WORKER_PID_LOCK.exists():
        return None

    try:
        fd = os.open(WORKER_PID_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None

    os.write(fd, str(os.getpid()).encode("utf-8"))
    os.close(fd)
    atexit.register(_gib_worker_pid_lock_frei, WORKER_PID_LOCK)
    return WORKER_PID_LOCK


def _gib_worker_pid_lock_frei(lock_path):
    try:
        if Path(lock_path).read_text(encoding="utf-8").strip() == str(os.getpid()):
            Path(lock_path).unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def main():
    worker_lock = _hole_worker_lock()
    if worker_lock is None:
        print("Ein Hintergrund-Worker laeuft bereits. Dieser zweite Start wird beendet.")
        return

    print("=========================================================")
    print(f"🚀 Trading-Tool Hintergrund-Wächter gestartet")
    print(f"🕒 Startzeit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=========================================================")
    letzter_status_log = None
    
    while True:
        try:
            fuehre_tagespruefung_aus()
            # Automatisierungs-Check ausführen
            fixiert = check_automation_loop()
            status = hole_fixierungs_status() or {}
            status_key = tuple(sorted(status.keys()))
            if fixiert or status_key != letzter_status_log:
                print(f"Fixierungsstatus heute: {status or 'noch keine Fixierung'}")
                letzter_status_log = status_key
        except Exception as e:
            print(f"⚠️ Fehler im Hintergrund-Worker: {e}")
            
        # 1 Minute warten bis zum nächsten Check
        time.sleep(60)

if __name__ == "__main__":
    main()
