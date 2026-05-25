@echo off
cd /d "%USERPROFILE%\Documents\trading_tool"

call .venv\Scripts\activate.bat

if "%TRADING_TOOL_STORAGE%"=="" set TRADING_TOOL_STORAGE=local
set TRADING_TOOL_START_WORKER=0

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
