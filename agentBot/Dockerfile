FROM node:20-alpine

WORKDIR /app

# 先装依赖（利用镜像层缓存）
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

# 拷贝源码与默认配置
COPY src ./src
COPY config ./config

ENV NODE_ENV=production
EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8081/api/config > /dev/null 2>&1 || exit 1

CMD ["node", "src/index.js"]
