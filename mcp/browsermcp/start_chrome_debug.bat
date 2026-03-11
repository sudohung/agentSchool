@echo off
echo Starting Chrome with remote debugging on port 9222...
echo.
echo Close this window to stop the browser.
echo.

REM Try different Chrome paths
set CHROME_PATH=""

REM Check common Chrome locations
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    set CHROME_PATH="C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    echo Chrome not found, using Edge instead...
) else (
    echo ERROR: Chrome or Edge not found!
    echo Please install Chrome or modify this script to point to your browser.
    pause
    exit /b 1
)

echo Using browser: %CHROME_PATH%
echo Remote debugging URL: http://127.0.0.1:9222
echo.

%CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug-profile"