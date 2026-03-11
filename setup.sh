#!/bin/bash

# Agent School Setup Script
# 新手友好的一键安装脚本

echo "==================================="
echo "🤖 Welcome to Agent School Setup!"
echo "==================================="

# 检查系统环境
echo "🔍 Checking system requirements..."

# 检查 Git
if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装，请先安装 Git"
    exit 1
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js 已安装: $NODE_VERSION"
    USE_NODE=true
else
    echo "⚠️  Node.js 未找到"
    USE_NODE=false
fi

# 检查 Python
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✅ Python 已安装: $PYTHON_VERSION"
    USE_PYTHON=true
else
    echo "⚠️  Python 未找到"
    USE_PYTHON=false
fi

# 如果都没有安装，给出建议
if [ "$USE_NODE" = false ] && [ "$USE_PYTHON" = false ]; then
    echo ""
    echo "🚨 错误：未检测到 Node.js 或 Python"
    echo "请至少安装其中一个："
    echo "- Node.js 下载：https://nodejs.org/"
    echo "- Python 下载：https://www.python.org/"
    exit 1
fi

echo ""
echo "📦 安装项目依赖..."

# 安装 Node.js 依赖
if [ "$USE_NODE" = true ]; then
    echo "🔧 安装 Node.js 依赖..."
    if npm install; then
        echo "✅ Node.js 依赖安装成功"
    else
        echo "❌ Node.js 依赖安装失败"
    fi
fi

# 安装 Python 依赖
if [ "$USE_PYTHON" = true ]; then
    echo "🐍 安装 Python 依赖..."
    if pip install -r requirements.txt; then
        echo "✅ Python 依赖安装成功"
    else
        echo "❌ Python 依赖安装失败"
    fi
fi

echo ""
echo "📋 创建环境配置文件..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Agent School 环境配置文件
# 请根据需要修改以下配置

# 数据库配置
DATABASE_URL=sqlite:///./agent_school.db

# API 密钥（如需要）
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# 服务器配置
PORT=3000
DEBUG=true

# 日志级别
LOG_LEVEL=info
EOF
    echo "✅ .env 配置文件已创建"
else
    echo "ℹ️  .env 文件已存在，跳过创建"
fi

echo ""
echo "🧪 运行初始测试..."
if [ "$USE_NODE" = true ]; then
    npm test
elif [ "$USE_PYTHON" = true ]; then
    python -m pytest
fi

echo ""
echo "==================================="
echo "🎉 安装完成！"
echo "==================================="
echo ""
echo "下一步建议："
echo "1. 阅读新手指南：cat BEGINNER_GUIDE.md"
echo "2. 查看项目结构：ls -la"
echo "3. 运行示例程序：npm run example （或相应命令）"
echo ""
echo "需要帮助？查看文档或在 GitHub 上提问！"
echo ""