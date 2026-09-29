# ============ 基础镜像：官方 Python slim（体积小，PyMySQL 为纯 Python 无需编译工具链） ============
FROM python:3.12-slim

LABEL org.opencontainers.image.title="mysql-mcp-server" \
      org.opencontainers.image.description="MySQL MCP Server for business data analysis" \
      org.opencontainers.image.source="agentSchool/mcp/mysqlMcp"

# ============ 环境变量 ============
# PYTHONUNBUFFERED: 日志实时输出，便于 docker logs 查看
# MCP_HOST/MCP_PORT: 服务监听地址与端口，运行时可被 -e 覆盖
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# ============ 依赖安装（先拷贝依赖清单，利用层缓存加速重复构建） ============
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ============ 应用代码 ============
COPY mysql_mcp_server.py ./

# ============ 安全加固：使用非 root 用户运行 ============
RUN useradd --create-home --shell /usr/sbin/nologin mcpuser
USER mcpuser

EXPOSE 8000

# ============ 健康检查：TCP 探活（SSE 是长连接流，不适合 HTTP 短探活） ============
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,socket; socket.create_connection(('127.0.0.1', int(os.getenv('MCP_PORT','8000'))), timeout=4)" || exit 1

# ============ 启动命令：默认 HTTP(SSE) 传输，可通过环境变量覆盖 ============
# 注意：容器内监听必须为 0.0.0.0，否则宿主机无法访问
CMD ["sh", "-c", "python mysql_mcp_server.py --transport ${MCP_TRANSPORT:-streamable_http} --host ${MCP_HOST:-0.0.0.0} --port ${MCP_PORT:-8000}"]
