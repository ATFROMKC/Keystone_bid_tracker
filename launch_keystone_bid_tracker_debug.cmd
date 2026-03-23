@echo off
REM Same as launch_keystone_bid_tracker.cmd but uses python.exe so errors print in this window.
REM Use this when the normal launcher flashes and exits.
title Keystone Bid Tracker (debug)
cd /d "%~dp0"
set "APP_SCRIPT=%~dp0scripts\launch_app.py"

if exist ".venv\Scripts\python.exe" (
  echo Using .venv\Scripts\python.exe
  ".venv\Scripts\python.exe" "%APP_SCRIPT%"
) else (
  echo No .venv — trying py -3
  py -3 "%APP_SCRIPT%"
)
set EXITCODE=%ERRORLEVEL%

echo.
echo Exit code: %EXITCODE%
echo.
echo Trace log:    %%TEMP%%\KeystoneBidTracker_launch_trace.txt
echo Error log:    %%TEMP%%\KeystoneBidTracker_last_error.txt
echo Crash log:    %%TEMP%%\KeystoneBidTracker_faulthandler.log
echo.
pause
exit /b %EXITCODE%
