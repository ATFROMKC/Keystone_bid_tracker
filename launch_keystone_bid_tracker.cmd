@echo off
REM Run Keystone Bid Tracker (no console): start pythonw detached so this cmd window closes.
REM Uses scripts\launch_app.py: repo root cwd + %%TEMP%%\KeystoneBidTracker_last_error.txt on Python errors.
setlocal
cd /d "%~dp0"
set "APP_SCRIPT=%~dp0scripts\launch_app.py"
set "PYW=%~dp0.venv\Scripts\pythonw.exe"

if exist "%PYW%" (
  start "" "%PYW%" "%APP_SCRIPT%"
  exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
  start "" pythonw "%APP_SCRIPT%"
  exit /b 0
)
where pyw >nul 2>&1
if %ERRORLEVEL% equ 0 (
  start "" pyw -3 "%APP_SCRIPT%"
  exit /b 0
)

echo No windowed Python found, and no .venv\Scripts\pythonw.exe.
echo.
echo One-time setup from this folder:
echo   py -3 -m venv .venv
echo   .venv\Scripts\activate
echo   pip install -r requirements.txt
echo.
echo Then run this launcher again.
pause
exit /b 1
