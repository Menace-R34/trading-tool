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
$requirementsBefore = git rev-parse "HEAD:requirements.txt" 2>$null
$updated = $false

if ($localRev -eq $remoteRev) {
    Write-Host "Keine neuen Code-Aenderungen gefunden." -ForegroundColor Green
} else {
    Write-Host "Stoppe laufende Trading-Tool-Prozesse..."
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -like "*$projectRoot*" -and
            (
                $_.CommandLine -like "*streamlit run app.py*" -or
                $_.CommandLine -like "*background_worker.py*"
            )
        } |
        ForEach-Object {
            Write-Host "Stoppe Prozess $($_.ProcessId): $($_.Name)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }

    git pull --ff-only
    Write-Host "Code aktualisiert." -ForegroundColor Green
    $updated = $true
}

$requirementsAfter = git rev-parse "HEAD:requirements.txt" 2>$null
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if ((Test-Path $pythonPath) -and ($requirementsBefore -ne $requirementsAfter)) {
    Write-Host "Aktualisiere Python-Abhaengigkeiten..."
    & $pythonPath -m pip install -r requirements.txt
} elseif (Test-Path $pythonPath) {
    Write-Host "requirements.txt unveraendert, ueberspringe pip install."
} else {
    Write-Host ".venv nicht gefunden. Abhaengigkeiten wurden nicht aktualisiert." -ForegroundColor Yellow
}

if ($updated) {
    Write-Host "Starte Web-App und Worker neu..."
    Start-Process -FilePath (Join-Path $projectRoot "start_homeserver_web_windows.bat") -WorkingDirectory $projectRoot
    Start-Process -FilePath (Join-Path $projectRoot "start_homeserver_worker_windows.bat") -WorkingDirectory $projectRoot
}

Write-Host ""
Write-Host "Fertig." -ForegroundColor Green
