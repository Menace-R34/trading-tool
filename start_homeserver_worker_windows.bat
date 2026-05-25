@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=1
set TRADING_TOOL_PROCESS=worker

python background_worker.py
