# Online-Betrieb auf dem eigenen Homeserver

Ziel:

- App online auf mehreren Endgeraeten nutzen.
- Daten langfristig auf dem Homeserver im Ordner `data/` sammeln.
- Lokal weiterentwickeln und per GitHub deployen.
- Automatische Sammlung ueber den Homeserver-Worker ausfuehren.

## 1. Homeserver als Datenquelle nutzen

Das Docker-Setup speichert lokal auf dem Server:

```text
data/trade_republic_universum.csv
data/standardwerte_vorschlag.json
data/prognosen_historie.csv
data/prognosen_auswertung.csv
data/prognosen_metadaten.json
data/optimierungsvorschlaege_historie.json
data/backups/
```

Im Docker Compose ist `TRADING_TOOL_STORAGE=local` gesetzt. Es werden keine Google-Secrets benoetigt.

## 2. Daten aus Google Sheets einmalig uebernehmen

Falls deine bisherigen Live-Daten noch in Google Sheets liegen, importiere sie einmalig auf dem Homeserver:

```bash
cd /opt/trading_tool
python scripts/import_sheets_to_local.py
```

Dafuer muessen die alten Google-Secrets nur fuer diesen einen Import noch vorhanden sein. Danach kannst du sie vom Server, aus Streamlit und aus GitHub entfernen.

## 3. Server starten

```bash
cd /opt/trading_tool
docker compose up -d --build
```

Status:

```bash
docker compose ps
docker compose logs -f web
docker compose logs -f worker
```

## 4. Entwicklungsablauf

Lokal entwickeln:

```bash
git status
git add .
git commit -m "Use homeserver local storage"
git push
```

Auf dem Homeserver aktualisieren:

```bash
cd /opt/trading_tool
git pull
docker compose up -d --build
```

Automatisch aktualisieren lassen:

```bash
cd /opt/trading_tool
chmod +x scripts/homeserver_auto_update.sh
crontab -e
```

Diese Zeile eintragen:

```cron
*/5 * * * * cd /opt/trading_tool && bash scripts/homeserver_auto_update.sh >> logs/auto_update.log 2>&1
```

Danach genuegt lokal `git push`. Der Homeserver holt die neue Version automatisch.

Update per VPN direkt anstossen:

```bash
export TRADING_TOOL_SERVER="dein-user@192.168.178.50"
export TRADING_TOOL_SERVER_OS="windows"
git push
scripts/deploy_via_vpn.sh
```

Falls der Serverpfad anders ist:

```bash
export TRADING_TOOL_SERVER_PATH="Documents\anderer_ordner"
```
