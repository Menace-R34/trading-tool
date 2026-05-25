@echo off
cd /d "%USERPROFILE%\Documents\trading_tool"

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=0

streamlit run app.py --server.address 0.0.0.0 --server.port 8501
