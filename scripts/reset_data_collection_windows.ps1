$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $projectRoot "data\backups\reset_$timestamp"

Write-Host "Trading Tool Datensammlung zuruecksetzen" -ForegroundColor Cyan
Write-Host "Projekt: $projectRoot"
Write-Host "Backup:  $backupDir"
Write-Host ""

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$filesToArchive = @(
    "data\prognosen_historie.csv",
    "data\prognosen_auswertung.csv",
    "data\prognosen_metadaten.json",
    "data\intraday_timing.csv",
    "data\prognosen_historie.csv.tmp",
    "data\prognosen_auswertung.csv.tmp",
    "data\prognosen_metadaten.json.tmp",
    "data\automation_check.lock",
    "data\background_worker.pid"
)

foreach ($relativePath in $filesToArchive) {
    $path = Join-Path $projectRoot $relativePath
    if (Test-Path $path) {
        Move-Item -Path $path -Destination $backupDir -Force
        Write-Host "Archiviert: $relativePath"
    }
}

$cacheDir = Join-Path $projectRoot "data\cache_kurse"
if (Test-Path $cacheDir) {
    $cacheBackup = Join-Path $backupDir "cache_kurse"
    Move-Item -Path $cacheDir -Destination $cacheBackup -Force
    Write-Host "Archiviert: data\cache_kurse"
}

$logDir = Join-Path $projectRoot "data\logs"
if (Test-Path $logDir) {
    $logBackup = Join-Path $backupDir "logs"
    Move-Item -Path $logDir -Destination $logBackup -Force
    Write-Host "Archiviert: data\logs"
}

New-Item -ItemType Directory -Path (Join-Path $projectRoot "data") -Force | Out-Null

$marker = Join-Path $backupDir "RESET_INFO.txt"
@(
    "Trading Tool Datensammlung zurueckgesetzt",
    "Zeitpunkt: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') deutsche Serverzeit",
    "Projekt: $projectRoot",
    "",
    "Archiviert wurden Prognosehistorie, Auswertung, Metadaten, Intraday-Cache, Kurscache und Logs.",
    "Behalten wurden Code, Einstellungen, Tickeruniversum, Optimierungshistorie und bestehende Backups."
) | Set-Content -Path $marker -Encoding UTF8

Write-Host ""
Write-Host "Fertig. Die neue Datensammlung startet beim naechsten Fixierungs-/Kontrolllauf." -ForegroundColor Green
