@echo off
set "TRADING_TOOL_PROJECT_DIR=%TRADING_TOOL_PROJECT_DIR%"
if "%TRADING_TOOL_PROJECT_DIR%"=="" set "TRADING_TOOL_PROJECT_DIR=%~dp0"
cd /d "%TRADING_TOOL_PROJECT_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_update_from_github.ps1"

echo.
pause
