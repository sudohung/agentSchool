@echo off
REM Run Java SDK Integration Tests
set "JAVA_HOME=C:\Program Files\Java\jdk1.8.0_202"
set "PATH=%JAVA_HOME%\bin;%PATH%"

echo JAVA_HOME: %JAVA_HOME%
echo.

cd /d %~dp0
mvn clean test -Dtest=IntegrationTest -DfailIfNoTests=false
