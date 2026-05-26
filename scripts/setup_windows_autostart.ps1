$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$startupDir = [Environment]::GetFolderPath("Startup")

$shortcuts = @(
    @{
        Name = "Trading Tool Web.lnk"
        Target = Join-Path $projectRoot "start_homeserver_web_windows.bat"
    }
)

$shell = New-Object -ComObject WScript.Shell
$existing = @(
    Join-Path $startupDir "Trading Tool Web.lnk"
    Join-Path $startupDir "Trading Tool Worker.lnk"
)

foreach ($path in $existing) {
    if (Test-Path $path) {
        Remove-Item $path -Force
    }
}

foreach ($item in $shortcuts) {
    if (-not (Test-Path $item.Target)) {
        throw "Datei nicht gefunden: $($item.Target)"
    }

    $shortcutPath = Join-Path $startupDir $item.Name
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $item.Target
    $shortcut.WorkingDirectory = [string]$projectRoot
    $shortcut.Save()

    Write-Host "Autostart eingerichtet: $shortcutPath"
}

Write-Host ""
Write-Host "Fertig. Beim naechsten Login dieses Windows-Benutzers startet die Web-App automatisch."
Write-Host "Die automatische Fixierung laeuft innerhalb der Web-App."
