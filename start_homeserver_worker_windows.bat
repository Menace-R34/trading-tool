@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

set "TRADING_TOOL_START_LOCK=%TEMP%\trading_tool_worker_start.lock"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*background_worker.py*' }; if (-not $p -and (Test-Path '%TRADING_TOOL_START_LOCK%')) { Remove-Item '%TRADING_TOOL_START_LOCK%' -Force -Recurse }"
mkdir "%TRADING_TOOL_START_LOCK%" 2>nul
if errorlevel 1 (
    echo Trading Tool Worker-Start laeuft bereits.
    exit /b 0
)

set "TRADING_TOOL_PROJECT_DIR_PS=%TRADING_TOOL_PROJECT_DIR:\=\\%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$self=$PID; $p=Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $self -and $_.CommandLine -and $_.CommandLine -like '*background_worker.py*' }; if ($p) { exit 10 }"
if %ERRORLEVEL%==10 (
    echo Trading Tool Worker laeuft bereits.
    rmdir "%TRADING_TOOL_START_LOCK%" 2>nul
    exit /b 0
)

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=1
set TRADING_TOOL_PROCESS=worker

python "%TRADING_TOOL_PROJECT_DIR%\background_worker.py"
rmdir "%TRADING_TOOL_START_LOCK%" 2>nul
