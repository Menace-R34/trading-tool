$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$startupDir = [Environment]::GetFolderPath("Startup")

$shortcuts = @(
    @{
        Name = "Trading Tool Web.lnk"
        Target = Join-Path $projectRoot "start_homeserver_web_windows.bat"
    },
    @{
        Name = "Trading Tool Worker.lnk"
        Target = Join-Path $projectRoot "start_homeserver_worker_windows.bat"
    }
)

$shell = New-Object -ComObject WScript.Shell

foreach ($item in $shortcuts) {
    if (-not (Test-Path $item.Target)) {
        throw "Datei nicht gefunden: $($item.Target)"
    }

    $shortcutPath = Join-Path $startupDir $item.Name
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $item.Target
    $shortcut.WorkingDirectory = $projectRoot
    $shortcut.Save()

    Write-Host "Autostart eingerichtet: $shortcutPath"
}

Write-Host ""
Write-Host "Fertig. Beim naechsten Login dieses Windows-Benutzers starten Web-App und Worker automatisch."
