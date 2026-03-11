@echo off

echo activity venv .browserVenv
echo.

call .browserVenv\Scripts\activate

echo Starting mcp server on port 8500...
echo.

python server.py --mode sse --port 8500

echo Remote mcp server : http://127.0.0.1:8500/sse
echo.
