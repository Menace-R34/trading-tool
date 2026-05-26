# Trading Tool online betreiben und weiterentwickeln

Kostenloser Start: siehe `ONLINE_SETUP.md`.

Zielbild:

- Ein Server laeuft dauerhaft online.
- Die Web-Oberflaeche ist von mehreren Geraeten erreichbar.
- Die automatische Fixierung laeuft innerhalb der Web-App als Hintergrundthread.
- GitHub ist die Code-Zentrale.
- Du entwickelst lokal weiter, pushst nach GitHub, und der Server zieht fertige Aenderungen von GitHub.

Das Projekt braucht auf dem Windows-Homeserver nur einen laufenden Prozess:

- Web-Oberflaeche: `streamlit run app.py`

Die Web-App startet beim Programmstart einen integrierten Hintergrundthread. Dieser prueft jede Minute die Automatik. Wenn `auto_fix_aktiv` aktiv ist, fixiert er Europa und USA nach den gespeicherten Zeiten und schreibt die Daten auf dem Homeserver nach `data/`.

Der integrierte Hintergrundthread kann mit `TRADING_TOOL_START_WORKER=0` deaktiviert werden. Der separate Start ueber `background_worker.py` bleibt nur als manuelle Notfalloption erhalten.

## Empfohlene Architektur

```text
Dein Mac / lokale Entwicklung
  -> Code aendern, testen, committen
  -> git push nach GitHub

GitHub
  -> zentrale Code-Version
  -> keine privaten Sammeldaten

Server / Live-Version
  -> git pull von GitHub
  -> Streamlit Web-App per Docker
  -> Background Worker per Docker
  -> persistenter data/-Ordner
  -> HTTPS + Passwortschutz vor der Web-App
```

Der wichtigste Grundsatz: Code und Daten getrennt behandeln. Code liegt in GitHub. `data/` ist der Zustand des Live-Systems und bleibt auf dem Server.

## GitHub-Workflow

Lokal auf deinem Mac:

```bash
git status
git add .
git commit -m "Deploy trading tool services"
git push
```

Auf dem Server:

```bash
cd /opt/trading_tool
git pull
docker compose up -d --build
```

Damit wird nur der Code aktualisiert. Die Daten bleiben erhalten, weil `docker-compose.yml` den lokalen Ordner `./data` in die Container einbindet.

Wenn der Homeserver per VPN erreichbar ist, kannst du das Update auch direkt von deinem Mac aus anstossen. Fuer Windows 10 einmalig lokal setzen:

```bash
export TRADING_TOOL_SERVER="dein-user@192.168.178.50"
export TRADING_TOOL_SERVER_OS="windows"
```

Nach einem Commit und Push:

```bash
scripts/deploy_via_vpn.sh
```

Standardpfad auf Windows ist `%USERPROFILE%\Documents\trading_tool`. Falls dein Projekt woanders liegt:

```bash
export TRADING_TOOL_SERVER_PATH="Documents\anderer_ordner"
```

Das Skript fuehrt auf Windows `git pull --ff-only` aus und installiert geaenderte Python-Abhaengigkeiten. Der Windows-Update-Button stoppt Web-App und Worker vor dem Update und startet beide danach neu.

Auf dem Windows-Desktop kann auch ein Update-Button angelegt werden:

```powershell
cd $env:USERPROFILE\Documents\trading_tool
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows_update_button.ps1
```

Der Button startet `update_homeserver_windows.bat`.

Wichtig: Die folgenden Live-Daten sollen nicht in GitHub liegen:

- `data/prognosen_historie.csv`
- `data/prognosen_auswertung.csv`
- `data/prognosen_metadaten.json`
- `data/standardwerte_vorschlag.json`
- `data/cache_kurse/`
- `data/backups/`

Das ist bereits in `.gitignore` so vorbereitet. Die Datei `data/trade_republic_universum.csv` ist die Ticker-Grundlage und kann im Repository bleiben, wenn sie keine privaten Daten enthaelt.

## Empfohlen: Docker Compose auf einem VPS

Die Dateien `Dockerfile`, `docker-compose.yml` und `deploy/caddy/Caddyfile` starten drei Dienste:

- `web`: Streamlit-App
- `worker`: Hintergrundsammler
- `caddy`: HTTPS-Reverse-Proxy mit Passwortschutz

### 1. Server vorbereiten

Auf dem Server Docker und Docker Compose installieren. Danach Repository von GitHub klonen, zum Beispiel nach:

```bash
sudo mkdir -p /opt
cd /opt
git clone DEIN_GITHUB_REPO trading_tool
cd /opt/trading_tool
```

### 2. Daten mitnehmen

Vom alten Rechner einmalig auf den Server kopieren:

```bash
data/trade_republic_universum.csv
data/standardwerte_vorschlag.json
data/prognosen_historie.csv
data/prognosen_auswertung.csv
data/prognosen_metadaten.json
```

Optional:

```bash
data/cache_kurse/
data/backups/
```

### 3. Domain und Passwort setzen

Die Standarddatei `deploy/caddy/Caddyfile` startet ohne Domain auf Port `80`. Fuer echte Online-Nutzung die sichere Vorlage kopieren:

```bash
cp deploy/caddy/Caddyfile.secure.example deploy/caddy/Caddyfile
```

Danach in `deploy/caddy/Caddyfile` ersetzen:

- `deine-email@example.com`
- `deine-domain.example.com`
- `deinname`
- den Passwort-Hash

Passwort-Hash erzeugen:

```bash
docker run --rm caddy:2 caddy hash-password --plaintext 'DEIN_PASSWORT'
```

Den erzeugten Hash in die `basicauth`-Zeile eintragen.

### 4. Live-System starten

```bash
docker compose up -d --build
```

Status:

```bash
docker compose ps
```

Logs:

```bash
docker compose logs -f worker
docker compose logs -f web
```

Update nach Code-Aenderungen:

```bash
git pull
docker compose up -d --build
```

Dabei bleibt `data/` erhalten, weil es als lokaler Server-Ordner in die Container eingebunden ist.

## Wichtig beim Umzug

Die Sammeldaten sind lokale Dateien und werden groesstenteils nicht von Git verwaltet. Beim Umzug oder Backup diese Dateien/Ordner mitnehmen:

- `data/trade_republic_universum.csv`
- `data/standardwerte_vorschlag.json`
- `data/prognosen_historie.csv`
- `data/prognosen_auswertung.csv`
- `data/prognosen_metadaten.json`
- `data/optimierungsvorschlaege_historie.json`
- optional: `data/cache_kurse/`
- optional: `data/backups/`

## Alternative: Linux-Server mit systemd

Empfohlener Zielpfad in den Vorlagen: `/opt/trading_tool`.

```bash
cd /opt/trading_tool
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Dienste installieren:

```bash
sudo cp deploy/systemd/trading-tool-web.service /etc/systemd/system/
sudo cp deploy/systemd/trading-tool-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now trading-tool-web trading-tool-worker
```

Status und Logs:

```bash
systemctl status trading-tool-web trading-tool-worker
journalctl -u trading-tool-worker -f
journalctl -u trading-tool-web -f
```

Die Web-Oberflaeche laeuft dann auf Port `8501`.

## Alternative: Dieser Mac mit launchd

Dienste laden:

```bash
cp deploy/launchd/com.trading-tool.web.plist ~/Library/LaunchAgents/
cp deploy/launchd/com.trading-tool.worker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.trading-tool.web.plist
launchctl load ~/Library/LaunchAgents/com.trading-tool.worker.plist
```

Stoppen:

```bash
launchctl unload ~/Library/LaunchAgents/com.trading-tool.web.plist
launchctl unload ~/Library/LaunchAgents/com.trading-tool.worker.plist
```

Logs:

```bash
tail -f logs/worker.out.log logs/worker.err.log
tail -f logs/streamlit.out.log logs/streamlit.err.log
```

## Pruefen, ob die Datensammlung laeuft

Nach einem geplanten Fixierungszeitpunkt sollten diese Dateien aktualisiert werden:

- `data/prognosen_historie.csv`
- `data/prognosen_metadaten.json`

Die aktuellen Zeiten kommen aus `data/standardwerte_vorschlag.json`. Wenn die Datei fehlt, gelten die Standardwerte aus `modules/ui_einstellungen.py`.
