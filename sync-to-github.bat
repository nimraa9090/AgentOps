
@echo off
cd /d "%~dp0"

echo.
echo =====================================
echo       AGENTOPS GITHUB SYNC
echo =====================================
echo.

git add -A

set /p message="Enter today's progress message: "

if "%message%"=="" set message=Daily AgentOps progress

git commit -m "%message%"

if errorlevel 1 (
    echo.
    echo No commit created. Check the message or Git status.
    pause
    exit /b 1
)

git push

if errorlevel 1 (
    echo.
    echo Push failed. Please check your connection.
    pause
    exit /b 1
)

echo.
echo SUCCESS! AgentOps is synced to GitHub.
pause
