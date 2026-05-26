@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

set "TRADING_TOOL_START_LOCK=%TEMP%\trading_tool_worker_start.lock"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -and $_.CommandLine -like '*background_worker.py*' }; if (-not $p -and (Test-Path '%TRADING_TOOL_START_LOCK%')) { Remove-Item '%TRADING_TOOL_START_LOCK%' -Force -Recurse }; $pidLock=Join-Path '%TRADING_TOOL_PROJECT_DIR%' 'data\background_worker.pid'; if (-not $p -and (Test-Path $pidLock)) { Remove-Item $pidLock -Force }"
mkdir "%TRADING_TOOL_START_LOCK%" 2>nul
if errorlevel 1 (
    echo Trading Tool Worker-Start laeuft bereits.
    exit /b 0
)

call .venv\Scripts\activate.bat

if not exist "%TRADING_TOOL_PROJECT_DIR%\data\logs" mkdir "%TRADING_TOOL_PROJECT_DIR%\data\logs"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set TRADING_TOOL_START_WORKER=1
set TRADING_TOOL_PROCESS=worker

python "%TRADING_TOOL_PROJECT_DIR%\background_worker.py" >> "%TRADING_TOOL_PROJECT_DIR%\data\logs\background_worker.log" 2>&1
rmdir "%TRADING_TOOL_START_LOCK%" 2>nul
