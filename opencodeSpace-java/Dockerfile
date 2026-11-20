# 基于 opencodeSpace 基础镜像，预装 Java 8（OpenJDK 8）+ Maven 环境
# 构建产物：opencodespace-opencode-for-java（基于 opencodespace-opencode:2.3.2）
FROM opencodespace-opencode:2.3.2

ENV JAVA_HOME=/usr/lib/jvm/default-jvm \
    MAVEN_HOME=/opt/maven \
    PATH=/opt/maven/bin:$PATH

# 体积优化：
# 1. apk add --no-cache 不留包缓存
# 2. Maven 用官方 tar 包手装到 /opt/maven（避免 apk maven 强拉 openjdk25 第二套 JDK）
# 注意：不要 apk del openjdk8 元包，会连带 purge openjdk8-jdk
RUN apk add --no-cache openjdk8 \
    && curl -fsSL -o /tmp/mvn.tgz \
        https://mirrors.aliyun.com/apache/maven/maven-3/3.9.16/binaries/apache-maven-3.9.16-bin.tar.gz \
    && mkdir -p /opt \
    && tar -xzf /tmp/mvn.tgz -C /opt \
    && mv /opt/apache-maven-3.9.16 /opt/maven \
    && rm /tmp/mvn.tgz

# Maven 走阿里云镜像仓库（国内加速）
RUN mkdir -p /root/.m2 \
    && printf '%s\n' \
      '<?xml version="1.0" encoding="UTF-8"?>' \
      '<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0">' \
      '  <mirrors>' \
      '    <mirror>' \
      '      <id>aliyun</id>' \
      '      <mirrorOf>central</mirrorOf>' \
      '      <url>https://maven.aliyun.com/repository/public</url>' \
      '    </mirror>' \
      '  </mirrors>' \
      '</settings>' \
      > /root/.m2/settings.xml
