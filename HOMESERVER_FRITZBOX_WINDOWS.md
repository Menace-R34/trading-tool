# Trading Tool auf Windows-10-Laptop mit FritzBox betreiben

Ziel:

- Windows-10-Laptop laeuft zuhause dauerhaft.
- Trading Tool ist im Heimnetz auf Handy, Tablet und anderen Rechnern erreichbar.
- Hintergrundsammler laeuft unabhaengig von der Web-Oberflaeche.
- Zugriff von unterwegs erfolgt sicher per FritzBox-VPN, nicht per offener Portfreigabe.

## 1. Windows-Laptop vorbereiten

Installieren:

- Git for Windows: `https://git-scm.com/download/win`
- Python 3.12 oder 3.13: `https://www.python.org/downloads/windows/`

Beim Python-Installer anhaken:

```text
Add python.exe to PATH
```

Danach `PowerShell` oeffnen:

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/Menace-R34/trading-tool.git trading_tool
cd trading_tool
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Falls PowerShell das Aktivieren blockiert:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Dann PowerShell neu oeffnen und erneut aktivieren.

## 2. Daten/Speicher

Der Homeserver bzw. Windows-Rechner ist die Datenquelle:

- `local`: Daten liegen im lokalen `data/`-Ordner.

Fuer lokale Daten brauchst du die bestehenden `data/`-Dateien auf dem Rechner.

Setze oder belasse:

```toml
TRADING_TOOL_STORAGE = "local"
```

Wenn bisher Daten in Google Sheets lagen, einmalig mit `python scripts/import_sheets_to_local.py` importieren und danach die Google-Secrets entfernen.

## 3. Feste IP in der FritzBox vergeben

In der FritzBox:

1. `http://fritz.box` oeffnen.
2. `Heimnetz` -> `Netzwerk`.
3. Windows-Laptop auswaehlen.
4. Aktivieren:

```text
Diesem Netzwerkgeraet immer die gleiche IPv4-Adresse zuweisen
```

Beispiel:

```text
192.168.178.50
```

## 4. Windows-Firewall erlauben

Beim ersten Start fragt Windows eventuell nach Netzwerkzugriff fuer Python/Streamlit.

Erlauben fuer:

```text
Private Netzwerke
```

Nicht noetig fuer:

```text
Oeffentliche Netzwerke
```

## 5. Web-App starten

In PowerShell:

```powershell
cd $env:USERPROFILE\Documents\trading_tool
.\start_homeserver_web_windows.bat
```

Auf einem anderen Geraet im selben WLAN:

```text
http://192.168.178.50:8501
```

IP an deine FritzBox-IP anpassen.

## 6. Hintergrundsammler starten

In einem zweiten PowerShell-Fenster:

```powershell
cd $env:USERPROFILE\Documents\trading_tool
.\start_homeserver_worker_windows.bat
```

Der Worker prueft regelmaessig, ob Europa oder USA fixiert werden muss.

## 7. Autostart unter Windows 10

Einfachster Weg im Windows-Benutzer, der die App betreiben soll:

```powershell
cd $env:USERPROFILE\Documents\trading_tool
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows_autostart.ps1
```

Alternativ manuell:

1. `Win + R`
2. Eingeben:

```text
shell:startup
```

3. Verknuepfungen zu diesen Dateien in den Autostart-Ordner legen:

```text
start_homeserver_web_windows.bat
start_homeserver_worker_windows.bat
```

Wichtig:

- Laptop muss angemeldet sein.
- Stromsparmodus deaktivieren.

## 8. Stromsparmodus deaktivieren

Windows 10:

1. Einstellungen -> System -> Netzbetrieb und Energiesparen
2. Bildschirm und Energiesparmodus auf Netzbetrieb passend einstellen:

```text
Nie in den Standbymodus wechseln
```

3. Laptop am Strom lassen.

## 9. Zugriff von unterwegs per FritzBox-VPN

Keine Portfreigabe auf `8501` einrichten.

Besser:

1. FritzBox -> `Internet` -> `Freigaben` -> `VPN`
2. WireGuard/VPN-Verbindung einrichten.
3. VPN-Profil auf Handy/Laptop importieren.
4. Von unterwegs VPN verbinden.
5. Danach im Browser:

```text
http://192.168.178.50:8501
```

## 10. Sicherheitsregeln

- Keine direkte Portfreigabe fuer Streamlit.
- Zugriff von unterwegs nur per VPN.
- Windows Updates regelmaessig installieren.
- Laptop am Strom lassen.
- Regelmaessige Backups einplanen.
- Service-Account-JSON-Dateien nicht offen im Editor lassen.

## 11. Updates per VPN vom Mac anstossen

Wenn der Windows-10-Homeserver per VPN und SSH erreichbar ist, kannst du Updates vom Mac aus starten.

Einmalig auf dem Mac setzen:

```bash
export TRADING_TOOL_SERVER="dein-user@192.168.178.50"
export TRADING_TOOL_SERVER_OS="windows"
```

Nach lokalen Code-Aenderungen:

```bash
git add .
git commit -m "Beschreibung der Aenderung"
git push
scripts/deploy_via_vpn.sh
```

Das Skript fuehrt auf Windows `git pull --ff-only` aus und installiert bei Bedarf die Python-Abhaengigkeiten aus `requirements.txt`.

Standardpfad auf Windows ist:

```text
%USERPROFILE%\Documents\trading_tool
```

Falls dein Projekt woanders liegt:

```bash
export TRADING_TOOL_SERVER_PATH="Documents\anderer_ordner"
```

Die Streamlit-Web-App erkennt Code-Aenderungen normalerweise selbst. Wenn du den Hintergrundsammler-Code aenderst, starte den Worker einmal neu.

## 12. Update-Button auf dem Windows-Desktop

Im Benutzer `tradingserver` ausfuehren:

```powershell
cd $env:USERPROFILE\Documents\trading_tool
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows_update_button.ps1
```

Danach liegt auf dem Desktop:

```text
Trading Tool aktualisieren
```

Ein Doppelklick zieht die neueste Version von GitHub und aktualisiert die Python-Abhaengigkeiten. Die Streamlit-Web-App erkennt Code-Aenderungen normalerweise selbst. Wenn der Worker-Code geaendert wurde, den Worker einmal neu starten.
