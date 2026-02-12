@echo off
REM FAISS MCP Server 安装脚本 (Windows)
REM 自动检测环境并安装所需依赖

echo ========================================
echo FAISS MCP Server 安装脚本
echo ========================================

REM 检查Python版本
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo 检测到Python版本:
python --version

REM 检查虚拟环境
if not exist ".faiVenv" (
    echo 创建虚拟环境...
    python -m venv .faiVenv
    if %errorlevel% neq 0 (
        echo 错误: 虚拟环境创建失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 激活虚拟环境...
call .faiVenv\Scripts\activate.bat

REM 安装核心依赖
echo 安装核心依赖...
pip install -r requirements-minimal.txt

if %errorlevel% neq 0 (
    echo 尝试使用conda安装faiss-cpu...
    conda install -c conda-forge faiss-cpu numpy -y
    if %errorlevel% neq 0 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo ========================================
echo 安装完成！
echo ========================================
echo 使用方法:
echo 1. 激活虚拟环境: .faiVenv\Scripts\activate.bat
echo 2. 运行服务器: python faiss_mcp_server.py --transport streamable_http --port 8001
echo 3. 运行测试: python faiss_mcp_server.py --test
echo 4. 查看帮助: python faiss_mcp_server.py --help
echo ========================================

pause