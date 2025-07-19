@echo off
echo ========================================
echo   Stopping Cibozer Development Server
echo ========================================
echo.

echo Searching for Cibozer processes...

REM Kill all Python processes running app.py
wmic process where "name='python.exe' and commandline like '%%app.py%%'" delete >nul 2>&1

REM Also try to kill by window title
taskkill /FI "WINDOWTITLE eq Cibozer*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq *app.py*" /F >nul 2>&1

echo.
echo Cibozer has been stopped.
echo.
pause