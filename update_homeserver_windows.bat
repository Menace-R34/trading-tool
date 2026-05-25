@echo off
cd /d "%USERPROFILE%\Documents\trading_tool"

powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_update_from_github.ps1"

echo.
pause
