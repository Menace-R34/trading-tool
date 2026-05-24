import time
import datetime
import sys
import os

# Pfad hinzufügen, damit Module gefunden werden
sys.path.append(os.getcwd())

from modules.logic.automation import check_automation_loop

def main():
    print("=========================================================")
    print(f"🚀 Trading-Tool Hintergrund-Wächter gestartet")
    print(f"🕒 Startzeit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=========================================================")
    
    while True:
        try:
            # Automatisierungs-Check ausführen
            check_automation_loop()
        except Exception as e:
            print(f"⚠️ Fehler im Hintergrund-Worker: {e}")
            
        # 1 Minute warten bis zum nächsten Check
        time.sleep(60)

if __name__ == "__main__":
    main()
