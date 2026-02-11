@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting MySQL MCP Server...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

python -c "import fastmcp" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo Starting server on http://localhost:%PORT%
echo Press Ctrl+C to stop
echo.

python mysql_mcp_server.py --port %PORT%
