#!/usr/bin/env bash
# agentBot Docker 一键部署脚本
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo "❌ 缺少 .env 文件，请先: cp .env.example .env 并填写飞书凭证"
    exit 1
fi

echo ">>> 构建镜像..."
docker compose build

echo ">>> 停止旧容器（如有）..."
docker compose down

echo ">>> 启动服务（restart: always 自动重启）..."
docker compose up -d

echo ">>> 部署完成"
echo "    配置管理页: http://<host>:8081"
echo "    查看日志:   docker logs -f agent-bot"
