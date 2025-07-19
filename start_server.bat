@echo off
echo Starting Cibozer Server...
echo.

REM Kill any existing Python processes on port 5001
echo Killing existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /PID %%a /F 2>nul
)

REM Clear Python cache
echo Clearing Python cache...
del /S /Q __pycache__\*.pyc 2>nul
del /S /Q *.pyc 2>nul

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set TEMPLATES_AUTO_RELOAD=True
set SEND_FILE_MAX_AGE_DEFAULT=0

echo.
echo Starting Flask server on port 5001...
echo Press Ctrl+C to stop the server
echo.

python -m flask run --port 5001 --reload --debugger