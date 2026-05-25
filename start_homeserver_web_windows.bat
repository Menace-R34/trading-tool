@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=0
set TRADING_TOOL_PROCESS=web

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
