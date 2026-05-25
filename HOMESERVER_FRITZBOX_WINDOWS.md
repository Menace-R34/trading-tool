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

## 2. Daten/Speicher entscheiden

Kurzfristig:

- `local`: Daten liegen lokal auf dem Windows-Laptop.
- `google_sheets`: Daten bleiben weiter in Google Sheets.

Fuer lokale Daten brauchst du die bestehenden `data/`-Dateien auf dem Laptop.

Fuer Google Sheets brauchst du lokal eine `.streamlit/secrets.toml` mit:

```toml
TRADING_TOOL_STORAGE = "google_sheets"
GOOGLE_SHEETS_SPREADSHEET_ID = "..."
GOOGLE_SERVICE_ACCOUNT_JSON = '''...'''
```

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

Einfachster Weg:

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
