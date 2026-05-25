# Kostenloser Online-Start mit GitHub, Streamlit Cloud und Google Sheets

Ziel:

- App online auf mehreren Endgeraeten nutzen.
- Daten langfristig in Google Sheets sammeln.
- Lokal weiterentwickeln und per GitHub deployen.
- Automatische Sammlung ueber GitHub Actions ausfuehren.

## 1. Google Sheet anlegen

Lege ein neues Google Sheet an. Die Tabellenblaetter werden bei Bedarf automatisch angelegt:

- `universum`
- `settings`
- `prognosen_historie`
- `prognosen_auswertung`
- `metadaten`
- `optimierung`

Notiere die Spreadsheet-ID aus der URL:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

## 2. Google Service Account vorbereiten

Die Nutzung fuer diesen Zweck ist normalerweise kostenlos:

- Google Sheets selbst ist mit einem normalen Google-Konto kostenlos nutzbar.
- Ein Google Cloud Service Account und ein JSON-Schluessel kosten nichts.
- Die Google Sheets API hat Quotas/Limits, aber fuer unsere wenigen geplanten Lese-/Schreibvorgaenge fallen normalerweise keine Kosten an.

Wichtig: Keine Compute-Instanzen, Datenbanken oder andere kostenpflichtige Google-Cloud-Dienste aktivieren.

### Service Account erstellen

1. Oeffne die Google Cloud Console: `https://console.cloud.google.com/`
2. Erstelle ein neues Projekt, z. B. `trading-tool`.
3. Aktiviere die Google Sheets API:
   - `APIs & Services`
   - `Library`
   - `Google Sheets API`
   - `Enable`
4. Gehe zu:
   - `IAM & Admin`
   - `Service Accounts`
5. Erstelle einen Service Account, z. B. `trading-tool-sheets`.
6. Beim Rollen-Schritt kann fuer unseren Zweck meist keine Projektrolle vergeben werden. Der eigentliche Zugriff kommt gleich ueber das Teilen des Sheets.
7. Oeffne den Service Account.
8. Tab `Keys`.
9. `Add key` -> `Create new key`.
10. `JSON` auswaehlen und erstellen.

Der JSON-Schluessel wird einmalig heruntergeladen. Bewahre ihn sicher auf und pushe ihn niemals nach GitHub.

Teile das Google Sheet mit der `client_email` aus dem JSON-Schluessel. Die Adresse sieht ungefaehr so aus:

```text
name@projekt.iam.gserviceaccount.com
```

Der Service Account braucht Bearbeitungsrechte auf dem Sheet.

## 3. Lokale Secrets setzen

Kopiere die Vorlage:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Trage dort ein:

- `TRADING_TOOL_STORAGE = "google_sheets"`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

Die Datei `.streamlit/secrets.toml` wird nicht nach GitHub gepusht.

## 4. Lokale Daten einmalig nach Google Sheets exportieren

```bash
python scripts/export_local_data_to_sheets.py
```

Danach kannst du lokal testweise mit Google Sheets starten:

```bash
TRADING_TOOL_STORAGE=google_sheets streamlit run app.py
```

## 5. GitHub Secrets setzen

Im GitHub Repository unter `Settings -> Secrets and variables -> Actions` diese Secrets anlegen:

- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

Damit kann GitHub Actions automatisch in dein Google Sheet schreiben.

## 6. Streamlit Community Cloud einrichten

Bei Streamlit Community Cloud die App aus GitHub deployen:

- Repository: `Menace-R34/trading-tool`
- Branch: `main`
- Main file path: `app.py`

In den Streamlit App-Secrets dieselben Werte hinterlegen wie lokal:

```toml
TRADING_TOOL_STORAGE = "google_sheets"
GOOGLE_SHEETS_SPREADSHEET_ID = "..."
GOOGLE_SERVICE_ACCOUNT_JSON = '''...'''
```

## 7. Automatische Sammlung

Die GitHub Action `.github/workflows/collect-snapshots.yml` startet den Sammler automatisch:

- `07:24 UTC` und `08:24 UTC`: Europa-Fenster fuer Sommer-/Winterzeit
- `13:54 UTC` und `14:54 UTC`: USA-Fenster fuer Sommer-/Winterzeit

Der Workflow kann in GitHub auch manuell gestartet werden.

Die GitHub Action `.github/workflows/evaluate-forecasts.yml` wertet die Prognosen taeglich automatisch aus:

- `22:30 UTC`: Prognoseauswertung nach US-Boersenschluss

Auch dieser Workflow kann in GitHub manuell gestartet werden.

## 8. Entwicklungsablauf

Lokal entwickeln:

```bash
git status
git add .
git commit -m "Prepare online Google Sheets storage"
git push
```

Streamlit Community Cloud aktualisiert die App aus GitHub. GitHub Actions nutzt ebenfalls den aktuellen Code aus GitHub.
