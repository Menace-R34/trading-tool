@echo off
cd /d "%USERPROFILE%\Documents\trading_tool"

call .venv\Scripts\activate.bat

set TRADING_TOOL_START_WORKER=1

python background_worker.py
