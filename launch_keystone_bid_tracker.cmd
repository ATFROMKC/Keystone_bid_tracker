@echo off
REM Run Keystone Bid Tracker (no console): prefers pythonw / pyw only.
cd /d "%~dp0"
set "MAIN=%~dp0keystone_bid_tracker\main.py"

if exist ".venv\Scripts\pythonw.exe" (
  ".venv\Scripts\pythonw.exe" "%MAIN%"
  exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
  pythonw "%MAIN%"
  exit /b 0
)
where pyw >nul 2>&1
if %ERRORLEVEL% equ 0 (
  pyw -3 "%MAIN%"
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
