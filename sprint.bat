@echo off
echo.
echo ========================================
echo      CIBOZER SPRINT MANAGER
echo ========================================
echo.

if "%1"=="" (
    echo Starting new sprint cycle...
    python new_sprint.py
) else if "%1"=="status" (
    python new_sprint.py status
) else if "%1"=="history" (
    python new_sprint.py history
) else if "%1"=="commit" (
    echo Committing sprint changes...
    git add -A
    git commit -F .sprint/next_commit.txt
    echo Sprint committed!
) else (
    echo Unknown command: %1
    echo.
    echo Usage:
    echo   sprint          - Start new sprint cycle
    echo   sprint status   - Check current status
    echo   sprint history  - View sprint history
    echo   sprint commit   - Commit sprint changes
)

echo.