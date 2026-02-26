@echo off
REM ============================================
REM FAISS MCP + Memory API 快速启动脚本 (Windows)
REM ============================================

echo.
echo ========================================
echo   FAISS MCP + Memory API 启动脚本
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
python -c "import fastmcp, faiss, numpy, sentence_transformers, fastapi" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少依赖，正在安装...
    pip install -q fastmcp faiss-cpu numpy sentence-transformers fastapi uvicorn python-dotenv
)

REM 获取配置
set FAISS_PORT=8401
set MEMORY_PORT=8425
set HOST=127.0.0.1

echo [2/4] 启动 Memory API 服务 (端口：%MEMORY_PORT%)
start "Memory API" python memory_api.py --port %MEMORY_PORT%
timeout /t 2 /nobreak >nul

echo [3/4] 启动 FAISS MCP 服务 (端口：%FAISS_PORT%)
start "FAISS MCP" python faiss_mcp_server.py --transport streamable_http --port %FAISS_PORT%
timeout /t 2 /nobreak >nul

echo.
echo [4/4] 服务启动完成！
echo.
echo ========================================
echo   服务地址
echo ========================================
echo   FAISS MCP:  http://%HOST%:%FAISS_PORT%
echo   Memory API: http://%HOST%:%MEMORY_PORT%
echo.
echo   健康检查:
echo   - FAISS:    http://%HOST%:%FAISS_PORT%/health
echo   - Memory:   http://%HOST%:%MEMORY_PORT%/health
echo.
echo   API 测试:
echo   - 添加文档：curl -X POST http://%HOST%:%FAISS_PORT%/call_tool ^
echo       -H "Content-Type: application/json" ^
echo       -d "{\"tool\":\"faiss_add_items\",\"arguments\":{\"params\":[{\"metadata\":{\"source\":\"test.md\"},\"document\":\"测试内容\"}]}}"
echo.
echo   - 搜索：curl -X POST http://%HOST%:%FAISS_PORT%/call_tool ^
echo       -H "Content-Type: application/json" ^
echo       -d "{\"tool\":\"faiss_search\",\"arguments\":{\"params\":{\"query_text\":\"搜索内容\",\"k\":5}}}"
echo.
echo ========================================
echo.
echo 按 Ctrl+C 或关闭命令行窗口停止服务
echo.
pause
