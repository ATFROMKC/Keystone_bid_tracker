@echo off
setlocal

REM 1-click launcher for built app (no Python terminal window).
set "ROOT_DIR=%~dp0"
set "APP_EXE=%ROOT_DIR%dist\Keystone Bid Tracker\Keystone Bid Tracker.exe"

if not exist "%APP_EXE%" (
  echo App executable not found.
  echo Run "build_windows_exe.bat" first.
  exit /b 1
)

start "" "%APP_EXE%"
exit /b 0
