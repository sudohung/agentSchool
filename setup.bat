@echo off
setlocal enabledelayedexpansion

echo ===================================
echo 🤖 Welcome to Agent School Setup!
echo ===================================

REM 检查系统环境
echo 🔍 Checking system requirements...

REM 检查 Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git 未安装，请先安装 Git
    pause
    exit /b 1
) e lse (
    for /f "tokens=*" %%i in ('git --version') do set GIT_VERSION=%%i
    echo ✅ Git 已安装: %GIT_VERSION%
)

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Node.js 未找到
    set USE_NODE=false
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo ✅ Node.js 已安装: %NODE_VERSION%
    set USE_NODE=true
)

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Python 未找到
    set USE_PYTHON=false
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✅ Python 已安装: %PYTHON_VERSION%
    set USE_PYTHON=true
)

REM 如果都没有安装，给出建议
if "!USE_NODE!"=="false" if "!USE_PYTHON!"=="false" (
    echo.
    echo 🚨 错误：未检测到 Node.js 或 Python
    echo 请至少安装其中一个：
    echo - Node.js 下载：https://nodejs.org/
    echo - Python 下载：https://www.python.org/
    pause
    exit /b 1
)

echo.
echo 📦 安装项目依赖...

REM 安装 Node.js 依赖
if "!USE_NODE!"=="true" (
    echo 🔧 安装 Node.js 依赖...
    call npm install
    if !errorlevel! equ 0 (
        echo ✅ Node.js 依赖安装成功
    ) else (
        echo ❌ Node.js 依赖安装失败
    )
)

REM 安装 Python 依赖
if "!USE_PYTHON!"=="true" (
    echo 🐍 安装 Python 依赖...
    pip install -r requirements.txt
    if !errorlevel! equ 0 (
        echo ✅ Python 依赖安装成功
    ) else (
        echo ❌ Python 依赖安装失败
    )
)

echo.
echo 📋 创建环境配置文件...
if not exist ".env" (
    echo # Agent School 环境配置文件 > .env
    echo # 请根据需要修改以下配置 >> .env
    echo. >> .env
    echo # 数据库配置 >> .env
    echo DATABASE_URL=sqlite:///./agent_school.db >> .env
    echo. >> .env
    echo # API 密钥（如需要） >> .env
    echo OPENAI_API_KEY= >> .env
    echo ANTHROPIC_API_KEY= >> .env
    echo. >> .env
    echo # 服务器配置 >> .env
    echo PORT=3000 >> .env
    echo DEBUG=true >> .env
    echo. >> .env
    echo # 日志级别 >> .env
    echo LOG_LEVEL=info >> .env
    echo ✅ .env 配置文件已创建
) else (
    echo ℹ️  .env 文件已存在，跳过创建
)

echo.
echo 🧪 运行初始测试...
if "!USE_NODE!"=="true" (
    call npm test
) else if "!USE_PYTHON!"=="true" (
    python -m pytest
)

echo.
echo ===================================
echo 🎉 安装完成！
echo ===================================
echo.
echo 下一步建议：
echo 1. 阅读新手指南：type BEGINNER_GUIDE.md
echo 2. 查看项目结构：dir
echo 3. 运行示例程序：npm run example （或相应命令）
echo.
echo 需要帮助？查看文档或在 GitHub 上提问！
echo.
pause