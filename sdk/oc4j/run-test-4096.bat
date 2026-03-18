@echo off
set "JAVA_HOME=C:\Program Files\Java\jdk-17.0.18"
set "PATH=%JAVA_HOME%\bin;E:\workspace\maven\apache-maven-3.6.2\bin;%PATH%"

echo Using JAVA_HOME: %JAVA_HOME%
java -version
echo.
echo Running Maven tests...
cd /d %~dp0
mvn clean test