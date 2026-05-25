$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

Write-Host "Trading Tool Update" -ForegroundColor Cyan
Write-Host "Projekt: $projectRoot"
Write-Host ""

if (-not (Test-Path ".git")) {
    throw "Dieser Ordner ist kein Git-Repository."
}

$status = git status --short
if ($status) {
    Write-Host "Lokale Aenderungen gefunden. Update wird gestoppt:" -ForegroundColor Yellow
    Write-Host $status
    throw "Bitte lokale Aenderungen zuerst committen oder sichern."
}

Write-Host "Hole neue Version von GitHub..."
git fetch --quiet

$localRev = git rev-parse "@"
$remoteRev = git rev-parse "@{u}"

if ($localRev -eq $remoteRev) {
    Write-Host "Keine neuen Code-Aenderungen gefunden." -ForegroundColor Green
} else {
    git pull --ff-only
    Write-Host "Code aktualisiert." -ForegroundColor Green
}

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "Aktualisiere Python-Abhaengigkeiten..."
    & $pythonPath -m pip install -r requirements.txt
} else {
    Write-Host ".venv nicht gefunden. Abhaengigkeiten wurden nicht aktualisiert." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Fertig. Falls der Worker-Code geaendert wurde, den Worker einmal neu starten." -ForegroundColor Green
