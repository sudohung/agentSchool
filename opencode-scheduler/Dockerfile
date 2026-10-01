# opencode-scheduler
# 常驻调度 daemon：cron/一次性任务 + bash/AI 执行器 + MCP 工具 + Web 管理页
FROM node:24-slim

WORKDIR /app

# 依赖层缓存
COPY package.json ./
RUN npm install --omit=dev && npm cache clean --force

COPY src ./src
COPY public ./public

RUN mkdir -p /data /workspace

ENV NODE_ENV=production \
    TZ=Asia/Shanghai \
    PORT=8080 \
    DB_PATH=/data/scheduler.db \
    OUTPUT_DIR=/data/outputs \
    DEFAULT_WORKDIR=/workspace \
    OPENCODE_BASE_URL=http://host.docker.internal:4096

VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD node -e "fetch('http://127.0.0.1:8080/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "src/index.js"]
