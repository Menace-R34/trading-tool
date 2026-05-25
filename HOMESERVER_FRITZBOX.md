# Trading Tool auf altem Laptop mit FritzBox betreiben

Ziel:

- Alter Laptop laeuft zuhause dauerhaft.
- Trading Tool ist im Heimnetz auf Handy, Tablet und anderen Rechnern erreichbar.
- Der Hintergrundsammler laeuft unabhaengig von der Web-Oberflaeche.
- Zugriff von unterwegs erfolgt sicher per FritzBox-VPN, nicht per offener Portfreigabe.

## Zielarchitektur

```text
Alter Laptop
  -> Streamlit Web-App auf Port 8501
  -> Background Worker
  -> lokale Daten im Projektordner

FritzBox
  -> feste lokale IP fuer den Laptop
  -> optional VPN fuer Zugriff von unterwegs

Andere Geraete
  -> Browser: http://LAPTOP-IP:8501
```

## 1. Laptop vorbereiten

Auf dem Laptop:

```bash
cd ~/Documents
git clone https://github.com/Menace-R34/trading-tool.git trading_tool
cd trading_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Falls das Projekt schon auf dem Laptop liegt:

```bash
cd ~/Documents/trading_tool
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Stromsparmodus deaktivieren

Der Laptop muss wach bleiben.

macOS:

- Systemeinstellungen -> Batterie / Energie
- Ruhezustand bei Netzbetrieb verhindern
- Automatisches Ausschalten deaktivieren
- Laptop am Strom lassen

## 3. Feste IP in der FritzBox vergeben

In der FritzBox:

1. `http://fritz.box` oeffnen.
2. `Heimnetz` -> `Netzwerk`.
3. Den alten Laptop auswaehlen.
4. Option aktivieren:

```text
Diesem Netzwerkgeraet immer die gleiche IPv4-Adresse zuweisen
```

Beispiel-IP:

```text
192.168.178.50
```

## 4. Web-App im Heimnetz starten

Auf dem Laptop:

```bash
cd ~/Documents/trading_tool
chmod +x start_homeserver_web.command
./start_homeserver_web.command
```

Dann auf einem anderen Geraet im selben WLAN:

```text
http://192.168.178.50:8501
```

Die IP an deine FritzBox-IP anpassen.

## 5. Hintergrundsammler starten

In einem zweiten Terminal auf dem Laptop:

```bash
cd ~/Documents/trading_tool
chmod +x start_homeserver_worker.command
./start_homeserver_worker.command
```

Der Worker prueft regelmaessig, ob Europa oder USA fixiert werden muss.

## 6. Autostart auf macOS

Die Vorlagen liegen hier:

```text
deploy/launchd/com.trading-tool.web.plist
deploy/launchd/com.trading-tool.worker.plist
```

Wenn der Projektpfad auf dem alten Laptop ebenfalls `~/Documents/trading_tool` ist:

```bash
mkdir -p logs
cp deploy/launchd/com.trading-tool.web.plist ~/Library/LaunchAgents/
cp deploy/launchd/com.trading-tool.worker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.trading-tool.web.plist
launchctl load ~/Library/LaunchAgents/com.trading-tool.worker.plist
```

Logs:

```bash
tail -f logs/streamlit.out.log logs/streamlit.err.log
tail -f logs/worker.out.log logs/worker.err.log
```

Stoppen:

```bash
launchctl unload ~/Library/LaunchAgents/com.trading-tool.web.plist
launchctl unload ~/Library/LaunchAgents/com.trading-tool.worker.plist
```

## 7. Zugriff von unterwegs per FritzBox-VPN

Keine Portfreigabe fuer Streamlit einrichten.

Stattdessen:

1. FritzBox oeffnen: `http://fritz.box`
2. `Internet` -> `Freigaben` -> `VPN`
3. VPN-Benutzer bzw. WireGuard-Verbindung einrichten.
4. VPN-Profil auf Handy/Laptop importieren.
5. Von unterwegs VPN verbinden.
6. Danach im Browser oeffnen:

```text
http://192.168.178.50:8501
```

## 8. Speicher

Der Homeserver ist die Datenquelle. Die App und der Worker speichern lokal im Projektordner:

```text
data/
```

## 9. Wichtige Sicherheitsregeln

- Keine Portfreigabe direkt auf `8501`.
- Zugriff von unterwegs nur ueber VPN.
- Laptop regelmaessig aktualisieren.
- Backups der Daten regelmaessig erstellen.
