@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

set "TRADING_TOOL_PROJECT_DIR_PS=%TRADING_TOOL_PROJECT_DIR:\=\\%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root='%TRADING_TOOL_PROJECT_DIR_PS%'; $p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like ('*' + $root + '*') -and $_.CommandLine -like '*streamlit run app.py*' }; if ($p) { exit 10 }"
if %ERRORLEVEL%==10 (
    echo Trading Tool Web-App laeuft bereits.
    exit /b 0
)

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=0
set TRADING_TOOL_PROCESS=web

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
