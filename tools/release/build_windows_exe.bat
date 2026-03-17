@echo off
setlocal

REM Build Keystone Bid Tracker as a windowed Windows executable with icon.
set "ROOT_DIR=%~dp0"
set "MAIN_SCRIPT=%ROOT_DIR%keystone_bid_tracker\main.py"
set "ICON_FILE=%ROOT_DIR%keystone_bid_tracker\Assets\icons\bidtracker.ico"

if not exist "%MAIN_SCRIPT%" (
  echo ERROR: main.py not found at "%MAIN_SCRIPT%"
  exit /b 1
)

if not exist "%ICON_FILE%" (
  echo ERROR: icon file not found at "%ICON_FILE%"
  exit /b 1
)

echo Building Keystone Bid Tracker executable...
python -m PyInstaller ^
  --noconfirm ^
  --windowed ^
  --name "Keystone Bid Tracker" ^
  --icon "%ICON_FILE%" ^
  --add-data "%ROOT_DIR%keystone_bid_tracker\Assets;Assets" ^
  "%MAIN_SCRIPT%"

if errorlevel 1 (
  echo.
  echo Build failed.
  exit /b 1
)

echo.
echo Build complete.
echo Output: "%ROOT_DIR%dist\Keystone Bid Tracker\Keystone Bid Tracker.exe"
exit /b 0
