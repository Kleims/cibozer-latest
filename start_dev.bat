@echo off
echo ========================================
echo   Cibozer Development Server
echo ========================================
echo.

REM Check if Python is already running app.py
wmic process where "name='python.exe' and commandline like '%%app.py%%'" get processid 2>nul | find /c /v "" > temp.txt
set /p count=<temp.txt
del temp.txt

if %count% gtr 1 (
    echo ERROR: Cibozer is already running!
    echo Please run stop_dev.bat first.
    pause
    exit /b 1
)

REM Clean up old log files if they exist
if exist logs\cibozer.log.5 del logs\cibozer.log.5
if exist logs\cibozer.log.4 move logs\cibozer.log.4 logs\cibozer.log.5 >nul 2>&1
if exist logs\cibozer.log.3 move logs\cibozer.log.3 logs\cibozer.log.4 >nul 2>&1
if exist logs\cibozer.log.2 move logs\cibozer.log.2 logs\cibozer.log.3 >nul 2>&1
if exist logs\cibozer.log.1 move logs\cibozer.log.1 logs\cibozer.log.2 >nul 2>&1
if exist logs\cibozer.log move logs\cibozer.log logs\cibozer.log.1 >nul 2>&1

echo Starting Cibozer...
echo.
echo Admin Panel: http://localhost:5001/admin
echo Main App: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Set development environment
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the app
python app.py