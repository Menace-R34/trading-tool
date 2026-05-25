$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$desktopDir = [Environment]::GetFolderPath("Desktop")
$buttonTarget = Join-Path $projectRoot "update_homeserver_windows.bat"

if (-not (Test-Path $buttonTarget)) {
    throw "Datei nicht gefunden: $buttonTarget"
}

$shortcutPath = Join-Path $desktopDir "Trading Tool aktualisieren.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $buttonTarget
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Save()

Write-Host "Update-Button erstellt: $shortcutPath"
