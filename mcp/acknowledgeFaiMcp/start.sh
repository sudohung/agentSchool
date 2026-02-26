#!/bin/bash
# ============================================
# FAISS MCP + Memory API 快速启动脚本 (Linux/Mac)
# ============================================

echo ""
echo "========================================"
echo "  FAISS MCP + Memory API 启动脚本"
echo "========================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/4] 检查依赖..."
python3 -c "import fastmcp, faiss, numpy, sentence_transformers, fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[警告] 缺少依赖，正在安装..."
    pip3 install -q fastmcp faiss-cpu numpy sentence-transformers fastapi uvicorn python-dotenv
fi

# 获取配置
FAISS_PORT=${FAISS_PORT:-8401}
MEMORY_PORT=${MEMORY_PORT:-8425}
HOST=${FAISS_HOST:-127.0.0.1}

echo "[2/4] 启动 Memory API 服务 (端口：$MEMORY_PORT)"
python3 memory_api.py --port "$MEMORY_PORT" &
MEMORY_PID=$!
sleep 2

echo "[3/4] 启动 FAISS MCP 服务 (端口：$FAISS_PORT)"
python3 faiss_mcp_server.py --transport streamable_http --port "$FAISS_PORT" &
FAISS_PID=$!
sleep 2

echo ""
echo "[4/4] 服务启动完成！"
echo ""
echo "========================================"
echo "  服务地址"
echo "========================================"
echo "  FAISS MCP:  http://$HOST:$FAISS_PORT"
echo "  Memory API: http://$HOST:$MEMORY_PORT"
echo ""
echo "  健康检查:"
echo "  - FAISS:    http://$HOST:$FAISS_PORT/health"
echo "  - Memory:   http://$HOST:$MEMORY_PORT/health"
echo ""
echo "  进程 ID:"
echo "  - Memory API: $MEMORY_PID"
echo "  - FAISS MCP:  $FAISS_PID"
echo ""
echo "========================================"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待进程
trap "kill $MEMORY_PID $FAISS_PID 2>/dev/null; echo '服务已停止'; exit" INT TERM

wait
