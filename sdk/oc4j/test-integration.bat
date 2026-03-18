@echo off
REM Integration Test Script for Java OpenCode SDK
REM Prerequisites: Java 8+, Maven, OpenCode server running at http://127.0.0.1:4097

echo ========================================
echo Java OpenCode SDK Integration Test
echo ========================================
echo.

REM Set JAVA_HOME if needed
if not defined JAVA_HOME (
    echo Setting JAVA_HOME...
    set "JAVA_HOME=C:\Program Files\Java\jdk1.8.0_202"
)

echo JAVA_HOME: %JAVA_HOME%
echo.

REM Check if server is running
echo Checking server connection...
curl -s http://127.0.0.1:4097/global/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Server is running at http://127.0.0.1:4097
) else (
    echo ✗ Server is not responding at http://127.0.0.1:4097
    echo Please start the OpenCode server first
    exit /b 1
)
echo.

REM Run integration tests
echo Running integration tests...
echo.
mvn test -Dtest=IntegrationTest

echo.
echo ========================================
echo Integration test completed
echo ========================================
