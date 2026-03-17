# OpenCode Java SDK (oc4j) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现一个完整的 Java 版本 OpenCode SDK，提供与 Python SDK (opencode-4-py) 相同的功能和 API 接口。

**Architecture:** 
- 采用 Maven 项目结构
- 使用 OkHttp 作为 HTTP 客户端
- 使用 Jackson 进行 JSON 序列化/反序列化
- 使用 Lombok 减少样板代码
- 支持同步和异步 (CompletableFuture) 两种调用方式
- 包结构：`ai.opencode.sdk`

**Tech Stack:** 
- Java 17+
- Maven 3.8+
- OkHttp 4.12+
- Jackson 2.16+
- Lombok 1.18+
- JUnit 5 + AssertJ (测试)

---

## 项目结构概览

```
sdk/oc4j/
├── pom.xml                          # Maven 配置
├── README.md                        # 项目说明
├── src/main/java/ai/opencode/sdk/
│   ├── OpenCodeClient.java          # 同步客户端
│   ├── AsyncOpenCodeClient.java     # 异步客户端
│   ├── ClientConfig.java            # 客户端配置
│   ├── OpenCodeException.java       # 异常层次结构
│   ├── http/
│   │   ├── HttpClient.java          # HTTP 客户端封装
│   │   └── AsyncHttpClient.java     # 异步 HTTP 客户端
│   ├── api/                         # API 模块 (15 个)
│   │   ├── SessionAPI.java
│   │   ├── MessageAPI.java
│   │   ├── EventAPI.java
│   │   ├── FileAPI.java
│   │   ├── ProviderAPI.java
│   │   ├── ProjectAPI.java
│   │   ├── ConfigAPI.java
│   │   ├── MCPAPI.java
│   │   ├── QuestionAPI.java
│   │   ├── PermissionAPI.java
│   │   ├── AgentAPI.java
│   │   ├── CommandAPI.java
│   │   ├── InstanceAPI.java
│   │   ├── LSPAPI.java
│   │   └── GlobalAPI.java
│   └── model/                       # 数据模型 (20+ 类)
│       ├── session/
│       ├── message/
│       ├── event/
│       ├── permission/
│       └── ...
└── src/test/java/ai/opencode/sdk/
    ├── OpenCodeClientTest.java
    └── api/
```

---

## Phase 1: 项目基础架构

### Task 1: 创建 Maven 项目配置

**Files:**
- Create: `sdk/oc4j/pom.xml`

**Step 1: 创建 pom.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>ai.opencode</groupId>
    <artifactId>oc4j</artifactId>
    <version>0.1.0</version>
    <packaging>jar</packaging>

    <name>OpenCode Java SDK</name>
    <description>Java SDK for OpenCode Server</description>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <okhttp.version>4.12.0</okhttp.version>
        <jackson.version>2.16.1</jackson.version>
        <lombok.version>1.18.30</lombok.version>
        <junit.version>5.10.1</junit.version>
    </properties>

    <dependencies>
        <!-- HTTP Client -->
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>okhttp</artifactId>
            <version>${okhttp.version}</version>
        </dependency>

        <!-- JSON -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${jackson.version}</version>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <version>${lombok.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <version>3.24.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>mockwebserver</artifactId>
            <version>${okhttp.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${lombok.version}</version>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.2</version>
            </plugin>
        </plugins>
    </build>
</project>
```

**Step 2: 验证 pom.xml**

Run: `cd sdk/oc4j && mvn validate`
Expected: BUILD SUCCESS

**Step 3: Commit**

```bash
git add sdk/oc4j/pom.xml
git commit -m "feat(oc4j): 创建 Maven 项目配置"
```

---

### Task 2: 创建基础目录结构

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/`
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/http/`
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/`
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/model/`
- Create: `sdk/oc4j/src/test/java/ai/opencode/sdk/`

**Step 1: 创建目录**

```bash
mkdir -p sdk/oc4j/src/main/java/ai/opencode/sdk/{http,api,model}
mkdir -p sdk/oc4j/src/test/java/ai/opencode/sdk
```

**Step 2: 验证目录结构**

Run: `tree sdk/oc4j/src`
Expected: 显示正确的目录结构

**Step 3: Commit**

```bash
git add sdk/oc4j/src
git commit -m "feat(oc4j): 创建项目目录结构"
```

---

### Task 3: 创建异常层次结构

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/OpenCodeException.java`

**Step 1: 创建异常类**

```java
package ai.opencode.sdk;

/**
 * Base exception for OpenCode SDK.
 */
public class OpenCodeException extends RuntimeException {
    public OpenCodeException(String message) {
        super(message);
    }
    
    public OpenCodeException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

**Step 2: 创建派生异常类**

```java
// ConnectionException.java
package ai.opencode.sdk;

public class ConnectionException extends OpenCodeException {
    public ConnectionException(String message) {
        super(message);
    }
}

// AuthenticationException.java
package ai.opencode.sdk;

public class AuthenticationException extends OpenCodeException {
    public AuthenticationException(String message) {
        super(message);
    }
}

// NotFoundException.java
package ai.opencode.sdk;

public class NotFoundException extends OpenCodeException {
    public NotFoundException(String message) {
        super(message);
    }
}

// APIException.java
package ai.opencode.sdk;

import lombok.Getter;
import java.util.Map;

@Getter
public class APIException extends OpenCodeException {
    private final int statusCode;
    private final String responseBody;
    private final Map<String, String> headers;
    private final boolean retryable;

    public APIException(int statusCode, String message, String responseBody, 
                       Map<String, String> headers, boolean retryable) {
        super(message);
        this.statusCode = statusCode;
        this.responseBody = responseBody;
        this.headers = headers;
        this.retryable = retryable;
    }
}
```

**Step 3: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/*Exception.java
git commit -m "feat(oc4j): 创建异常层次结构"
```

---

### Task 4: 创建客户端配置

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/ClientConfig.java`

**Step 1: 创建配置类**

```java
package ai.opencode.sdk;

import lombok.Builder;
import lombok.Getter;
import java.time.Duration;
import java.util.Optional;

@Getter
@Builder
public class ClientConfig {
    private final String baseUrl;
    private final String username;
    private final String password;
    private final Duration timeout;
    private final String directory;
    private final String workspace;

    public static class ClientConfigBuilder {
        private String baseUrl = "http://127.0.0.1:4096";
        private String username;
        private String password;
        private Duration timeout = Duration.ofSeconds(30);
        private String directory;
        private String workspace;

        public ClientConfigBuilder password(String password) {
            this.password = password;
            if (password != null && username == null) {
                this.username = "opencode";
            }
            return this;
        }
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/ClientConfig.java
git commit -m "feat(oc4j): 创建客户端配置类"
```

---

### Task 5: 创建 HTTP 客户端封装

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/http/HttpClient.java`

**Step 1: 创建同步 HTTP 客户端**

```java
package ai.opencode.sdk.http;

import ai.opencode.sdk.APIException;
import ai.opencode.sdk.ConnectionException;
import ai.opencode.sdk.ClientConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class HttpClient {
    private final OkHttpClient client;
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final String directory;
    private final String workspace;
    private final Request.Builder requestBuilder;

    public HttpClient(ClientConfig config) {
        this.mapper = new ObjectMapper();
        this.baseUrl = config.getBaseUrl();
        this.directory = config.getDirectory();
        this.workspace = config.getWorkspace();
        
        this.client = new OkHttpClient.Builder()
            .connectTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .readTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .writeTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .build();
        
        this.requestBuilder = new Request.Builder();
        
        if (config.getUsername() != null && config.getPassword() != null) {
            String credentials = Credentials.basic(config.getUsername(), config.getPassword());
            requestBuilder.addHeader("Authorization", credentials);
        }
    }

    public <T> T get(String path, Class<T> responseType) {
        return execute(buildRequest("GET", path, null), responseType);
    }

    public <T> T post(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("POST", path, body), responseType);
    }

    public <T> T put(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PUT", path, body), responseType);
    }

    public <T> T patch(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PATCH", path, body), responseType);
    }

    public void delete(String path) {
        execute(buildRequest("DELETE", path, null), Void.class);
    }

    public Boolean deleteWithResponse(String path) {
        return execute(buildRequest("DELETE", path, null), Boolean.class);
    }

    private <T> T execute(Request request, Class<T> responseType) {
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String body = response.body() != null ? response.body().string() : "";
                Map<String, String> headers = new HashMap<>();
                response.headers().forEach(h -> headers.put(h.getFirst(), h.getSecond()));
                boolean retryable = response.code() >= 500 || response.code() == 429;
                throw new APIException(response.code(), 
                    "HTTP " + response.code() + ": " + response.message(), 
                    body, headers, retryable);
            }
            
            ResponseBody responseBody = response.body();
            if (responseBody == null) {
                return null;
            }
            
            String json = responseBody.string();
            if (responseType == Void.class || responseType == Boolean.class) {
                if ("true".equals(json) || "false".equals(json)) {
                    return responseType.cast(Boolean.parseBoolean(json));
                }
                return null;
            }
            return mapper.readValue(json, responseType);
        } catch (IOException e) {
            throw new ConnectionException("Request failed: " + e.getMessage());
        }
    }

    private Request buildRequest(String method, String path, Object body) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();
        
        if (directory != null) {
            urlBuilder.addQueryParameter("directory", directory);
        }
        if (workspace != null) {
            urlBuilder.addQueryParameter("workspace", workspace);
        }
        
        Request.Builder builder = requestBuilder.newBuilder()
            .url(urlBuilder.build());
        
        if (body != null) {
            builder.method(method, RequestBody.create(
                toJson(body), 
                MediaType.parse("application/json")
            ));
        } else {
            builder.method(method, null);
        }
        
        return builder.build();
    }

    private String toJson(Object obj) {
        try {
            return mapper.writeValueAsString(obj);
        } catch (Exception e) {
            throw new ConnectionException("Failed to serialize object: " + e.getMessage());
        }
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/http/HttpClient.java
git commit -m "feat(oc4j): 创建同步 HTTP 客户端"
```

---

### Task 6: 创建异步 HTTP 客户端

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/http/AsyncHttpClient.java`

**Step 1: 创建异步 HTTP 客户端**

```java
package ai.opencode.sdk.http;

import ai.opencode.sdk.APIException;
import ai.opencode.sdk.ConnectionException;
import ai.opencode.sdk.ClientConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public class AsyncHttpClient {
    private final OkHttpClient client;
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final String directory;
    private final String workspace;
    private final Request.Builder requestBuilder;

    public AsyncHttpClient(ClientConfig config) {
        this.mapper = new ObjectMapper();
        this.baseUrl = config.getBaseUrl();
        this.directory = config.getDirectory();
        this.workspace = config.getWorkspace();
        
        this.client = new OkHttpClient.Builder()
            .connectTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .readTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .writeTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .build();
        
        this.requestBuilder = new Request.Builder();
        
        if (config.getUsername() != null && config.getPassword() != null) {
            String credentials = Credentials.basic(config.getUsername(), config.getPassword());
            requestBuilder.addHeader("Authorization", credentials);
        }
    }

    public <T> CompletableFuture<T> get(String path, Class<T> responseType) {
        return execute(buildRequest("GET", path, null), responseType);
    }

    public <T> CompletableFuture<T> post(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("POST", path, body), responseType);
    }

    public <T> CompletableFuture<T> put(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PUT", path, body), responseType);
    }

    public <T> CompletableFuture<T> patch(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PATCH", path, body), responseType);
    }

    public CompletableFuture<Void> delete(String path) {
        return execute(buildRequest("DELETE", path, null), Void.class);
    }

    private <T> CompletableFuture<T> execute(Request request, Class<T> responseType) {
        CompletableFuture<T> future = new CompletableFuture<>();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                future.completeExceptionally(new ConnectionException("Request failed: " + e.getMessage()));
            }

            @Override
            public void onResponse(Call call, Response response) {
                try {
                    if (!response.isSuccessful()) {
                        String body = response.body() != null ? response.body().string() : "";
                        Map<String, String> headers = new HashMap<>();
                        response.headers().forEach(h -> headers.put(h.getFirst(), h.getSecond()));
                        boolean retryable = response.code() >= 500 || response.code() == 429;
                        future.completeExceptionally(new APIException(
                            response.code(), 
                            "HTTP " + response.code() + ": " + response.message(), 
                            body, headers, retryable));
                        return;
                    }
                    
                    ResponseBody responseBody = response.body();
                    if (responseBody == null) {
                        future.complete(null);
                        return;
                    }
                    
                    String json = responseBody.string();
                    if (responseType == Void.class) {
                        future.complete(null);
                    } else if (responseType == Boolean.class) {
                        future.complete(responseType.cast(Boolean.parseBoolean(json)));
                    } else {
                        future.complete(mapper.readValue(json, responseType));
                    }
                } catch (IOException e) {
                    future.completeExceptionally(new ConnectionException("Response parsing failed: " + e.getMessage()));
                }
            }
        });
        
        return future;
    }

    private Request buildRequest(String method, String path, Object body) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();
        
        if (directory != null) {
            urlBuilder.addQueryParameter("directory", directory);
        }
        if (workspace != null) {
            urlBuilder.addQueryParameter("workspace", workspace);
        }
        
        Request.Builder builder = requestBuilder.newBuilder()
            .url(urlBuilder.build());
        
        if (body != null) {
            builder.method(method, RequestBody.create(
                toJson(body), 
                MediaType.parse("application/json")
            ));
        } else {
            builder.method(method, null);
        }
        
        return builder.build();
    }

    private String toJson(Object obj) {
        try {
            return mapper.writeValueAsString(obj);
        } catch (Exception e) {
            throw new ConnectionException("Failed to serialize object: " + e.getMessage());
        }
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/http/AsyncHttpClient.java
git commit -m "feat(oc4j): 创建异步 HTTP 客户端"
```

---

## Phase 2: 核心数据模型

### Task 7: 创建通用数据模型

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/model/common/`

**Step 1: 创建通用模型类**

```java
// TimeInfo.java
package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class TimeInfo {
    @JsonProperty("created")
    private Long created;
    
    @JsonProperty("updated")
    private Long updated;
    
    @JsonProperty("completed")
    private Long completed;
    
    @JsonProperty("compacting")
    private Long compacting;
    
    @JsonProperty("archived")
    private Long archived;
}

// ModelRef.java
package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class ModelRef {
    @JsonProperty("providerID")
    private String providerId;
    
    @JsonProperty("modelID")
    private String modelId;
}

// PathInfo.java
package ai.opencode.sdk.model.common;

import lombok.Data;

@Data
public class PathInfo {
    private String cwd;
    private String root;
}

// TokenInfo.java
package ai.opencode.sdk.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.Map;

@Data
public class TokenInfo {
    private Integer total;
    private Integer input;
    private Integer output;
    private Integer reasoning;
    private Map<String, Integer> cache;
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/model/common/
git commit -m "feat(oc4j): 创建通用数据模型"
```

---

### Task 8: 创建 Session 模型

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/model/session/`

**Step 1: 创建 Session 相关模型**

```java
// Session.java
package ai.opencode.sdk.model.session;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.ModelRef;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class Session {
    private String id;
    private String title;
    private String directory;
    
    @JsonProperty("parentID")
    private String parentId;
    
    private TimeInfo time;
    private SessionSummary summary;
    private ModelRef model;
    private String agent;
    private Map<String, Object> share;
    private List<Todo> todos;
    private String status;
}

// SessionSummary.java
package ai.opencode.sdk.model.session;

import lombok.Data;
import java.util.List;

@Data
public class SessionSummary {
    private int additions;
    private int deletions;
    private int files;
    private List<FileDiff> diffs;
}

// FileDiff.java
package ai.opencode.sdk.model.session;

import lombok.Data;

@Data
public class FileDiff {
    private String file;
    private String before;
    private String after;
    private int additions;
    private int deletions;
    private String status;
}

// Todo.java
package ai.opencode.sdk.model.session;

import lombok.Data;

@Data
public class Todo {
    private String id;
    private String content;
    private String status;
    private Long createdAt;
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/model/session/
git commit -m "feat(oc4j): 创建 Session 数据模型"
```

---

### Task 9: 创建 Message 模型

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/model/message/`

**Step 1: 创建 Message 相关模型**

```java
// UserMessage.java
package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.ModelRef;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class UserMessage {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String role = "user";
    private TimeInfo time;
    private String agent;
    private ModelRef model;
    private String system;
}

// AssistantMessage.java
package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.TokenInfo;
import ai.opencode.sdk.model.common.PathInfo;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class AssistantMessage {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String role = "assistant";
    private TimeInfo time;
    
    @JsonProperty("parentID")
    private String parentId;
    
    @JsonProperty("modelID")
    private String modelId;
    
    @JsonProperty("providerID")
    private String providerId;
    
    private String mode;
    private String agent;
    private PathInfo path;
    private double cost;
    private TokenInfo tokens;
    private String finish;
}

// TextPart.java
package ai.opencode.sdk.model.message;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class TextPart {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    @JsonProperty("messageID")
    private String messageId;
    
    private String type = "text";
    private String text;
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/model/message/
git commit -m "feat(oc4j): 创建 Message 数据模型"
```

---

### Task 10: 创建 Permission 模型

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/model/permission/`

**Step 1: 创建 Permission 相关模型**

```java
// PermissionRequest.java
package ai.opencode.sdk.model.permission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class PermissionRequest {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String permission;
    private List<String> patterns;
    private Map<String, Object> metadata;
    private List<String> always;
    private PermissionToolRef tool;
}

// PermissionToolRef.java
package ai.opencode.sdk.model.permission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class PermissionToolRef {
    @JsonProperty("messageID")
    private String messageId;
    
    @JsonProperty("callID")
    private String callId;
}

// PermissionReplyRequest.java
package ai.opencode.sdk.model.permission;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PermissionReplyRequest {
    private String reply;  // "once", "always", "reject"
    private String message;
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/model/permission/
git commit -m "feat(oc4j): 创建 Permission 数据模型"
```

---

## Phase 3: API 模块实现

### Task 11: 实现 Session API

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/SessionAPI.java`

**Step 1: 创建 Session API**

```java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.session.Session;
import ai.opencode.sdk.model.session.Todo;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
public class SessionAPI {
    private final HttpClient http;
    private final String directory;

    public List<Session> list() {
        return http.get("/session", List.class);
    }

    public Session get(String sessionId) {
        return http.get("/session/" + sessionId, Session.class);
    }

    public Session create(String title, String directory) {
        Map<String, String> body = new HashMap<>();
        if (title != null) body.put("title", title);
        if (directory != null) body.put("directory", directory);
        return http.post("/session", body, Session.class);
    }

    public void delete(String sessionId) {
        http.delete("/session/" + sessionId);
    }

    public List<Todo> todos(String sessionId) {
        return http.get("/session/" + sessionId + "/todo", List.class);
    }

    public String status(String sessionId) {
        return http.get("/session/status", String.class);
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/api/SessionAPI.java
git commit -m "feat(oc4j): 实现 Session API"
```

---

### Task 12: 实现 Permission API

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/PermissionAPI.java`

**Step 1: 创建 Permission API**

```java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.permission.PermissionRequest;
import ai.opencode.sdk.model.permission.PermissionReplyRequest;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
public class PermissionAPI {
    private final HttpClient http;
    private final String directory;

    public List<PermissionRequest> list() {
        return http.get("/permission", List.class);
    }

    public Boolean reply(String requestId, String reply, String message) {
        PermissionReplyRequest request = PermissionReplyRequest.builder()
            .reply(reply)
            .message(message)
            .build();
        return http.post("/permission/" + requestId + "/reply", request, Boolean.class);
    }

    public Boolean respond(String sessionId, String permissionId, String response) {
        Map<String, String> body = new HashMap<>();
        body.put("response", response);
        return http.post("/session/" + sessionId + "/permissions/" + permissionId, body, Boolean.class);
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/api/PermissionAPI.java
git commit -m "feat(oc4j): 实现 Permission API"
```

---

### Task 13: 实现 Message API

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/MessageAPI.java`

**Step 1: 创建 Message API**

```java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.message.MessageWithParts;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
public class MessageAPI {
    private final HttpClient http;
    private final String directory;

    public List<MessageWithParts> list(String sessionId) {
        return http.get("/session/" + sessionId + "/message", List.class);
    }

    public MessageWithParts get(String sessionId, String messageId) {
        return http.get("/session/" + sessionId + "/message/" + messageId, MessageWithParts.class);
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/api/MessageAPI.java
git commit -m "feat(oc4j): 实现 Message API"
```

---

### Task 14: 实现 File API

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/FileAPI.java`

**Step 1: 创建 File API**

```java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
public class FileAPI {
    private final HttpClient http;
    private final String directory;

    public List<Map<String, Object>> list(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path != null ? path : ".");
        return http.get("/file", List.class);
    }

    public Map<String, Object> read(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path);
        return http.get("/file/content", Map.class);
    }

    public List<Map<String, Object>> status() {
        return http.get("/file/status", List.class);
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/api/FileAPI.java
git commit -m "feat(oc4j): 实现 File API"
```

---

### Task 15: 实现其他核心 API

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/api/{ProviderAPI,ProjectAPI,ConfigAPI,AgentAPI,CommandAPI,GlobalAPI}.java`

**Step 1: 创建 Provider API**

```java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class ProviderAPI {
    private final HttpClient http;
    private final String directory;

    public Object list() {
        return http.get("/provider", Object.class);
    }

    public Object auth() {
        return http.get("/provider/auth", Object.class);
    }
}
```

**Step 2: 创建其他 API (类似结构)**

```java
// ProjectAPI.java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class ProjectAPI {
    private final HttpClient http;
    private final String directory;

    public Object list() { return http.get("/project", Object.class); }
    public Object current() { return http.get("/project/current", Object.class); }
}

// ConfigAPI.java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class ConfigAPI {
    private final HttpClient http;
    private final String directory;

    public Object get() { return http.get("/config", Object.class); }
}

// AgentAPI.java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class AgentAPI {
    private final HttpClient http;
    private final String directory;

    public Object list() { return http.get("/agent", Object.class); }
}

// CommandAPI.java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class CommandAPI {
    private final HttpClient http;
    private final String directory;

    public Object list() { return http.get("/command", Object.class); }
}

// GlobalAPI.java
package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class GlobalAPI {
    private final HttpClient http;

    public Map<String, Object> health() {
        return http.get("/global/health", Map.class);
    }
}
```

**Step 3: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/api/*.java
git commit -m "feat(oc4j): 实现核心 API 模块"
```

---

## Phase 4: 客户端集成

### Task 16: 创建同步客户端

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/OpenCodeClient.java`

**Step 1: 创建客户端类**

```java
package ai.opencode.sdk;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.api.*;
import lombok.Getter;

@Getter
public class OpenCodeClient implements AutoCloseable {
    private final ClientConfig config;
    private final HttpClient http;
    
    private final SessionAPI session;
    private final MessageAPI message;
    private final FileAPI file;
    private final ProviderAPI provider;
    private final ProjectAPI project;
    private final ConfigAPI config_api;
    private final AgentAPI agent;
    private final CommandAPI command;
    private final GlobalAPI global;
    private final PermissionAPI permission;

    public OpenCodeClient(ClientConfig config) {
        this.config = config;
        this.http = new HttpClient(config);
        
        String dir = config.getDirectory();
        this.session = new SessionAPI(http, dir);
        this.message = new MessageAPI(http, dir);
        this.file = new FileAPI(http, dir);
        this.provider = new ProviderAPI(http, dir);
        this.project = new ProjectAPI(http, dir);
        this.config_api = new ConfigAPI(http, dir);
        this.agent = new AgentAPI(http, dir);
        this.command = new CommandAPI(http, dir);
        this.global = new GlobalAPI(http);
        this.permission = new PermissionAPI(http, dir);
    }

    @Override
    public void close() {
        // OkHttp client will be closed automatically
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/OpenCodeClient.java
git commit -m "feat(oc4j): 创建同步客户端"
```

---

### Task 17: 创建异步客户端

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/AsyncOpenCodeClient.java`

**Step 1: 创建异步客户端类**

```java
package ai.opencode.sdk;

import ai.opencode.sdk.http.AsyncHttpClient;
import lombok.Getter;

@Getter
public class AsyncOpenCodeClient implements AutoCloseable {
    private final ClientConfig config;
    private final AsyncHttpClient http;

    public AsyncOpenCodeClient(ClientConfig config) {
        this.config = config;
        this.http = new AsyncHttpClient(config);
    }

    @Override
    public void close() {
        // OkHttp client will be closed automatically
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/AsyncOpenCodeClient.java
git commit -m "feat(oc4j): 创建异步客户端"
```

---

### Task 18: 创建包导出类

**Files:**
- Create: `sdk/oc4j/src/main/java/ai/opencode/sdk/package-info.java`

**Step 1: 创建包信息**

```java
/**
 * OpenCode Java SDK
 * 
 * Provides Java bindings for the OpenCode Server API.
 * 
 * @since 0.1.0
 */
package ai.opencode.sdk;
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/main/java/ai/opencode/sdk/package-info.java
git commit -m "feat(oc4j): 添加包文档"
```

---

## Phase 5: 测试

### Task 19: 创建单元测试

**Files:**
- Create: `sdk/oc4j/src/test/java/ai/opencode/sdk/OpenCodeClientTest.java`

**Step 1: 创建测试类**

```java
package ai.opencode.sdk;

import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.*;
import static org.assertj.core.api.Assertions.*;

class OpenCodeClientTest {
    private MockWebServer mockWebServer;
    private OpenCodeClient client;

    @BeforeEach
    void setUp() throws Exception {
        mockWebServer = new MockWebServer();
        mockWebServer.start();
        
        ClientConfig config = ClientConfig.builder()
            .baseUrl(mockWebServer.url("/").toString())
            .build();
        
        client = new OpenCodeClient(config);
    }

    @AfterEach
    void tearDown() throws Exception {
        client.close();
        mockWebServer.shutdown();
    }

    @Test
    void testHealthCheck() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setBody("{\"healthy\":true,\"version\":\"1.0.0\"}"));
        
        // Test implementation
    }

    @Test
    void testListSessions() throws Exception {
        mockWebServer.enqueue(new MockResponse()
            .setResponseCode(200)
            .setBody("[]"));
        
        // Test implementation
    }
}
```

**Step 2: Commit**

```bash
git add sdk/oc4j/src/test/java/ai/opencode/sdk/OpenCodeClientTest.java
git commit -m "test(oc4j): 创建基础单元测试"
```

---

### Task 20: 运行测试

**Step 1: 运行 Maven 测试**

Run: `cd sdk/oc4j && mvn test`
Expected: BUILD SUCCESS

**Step 2: Commit**

```bash
git add sdk/oc4j/target
git commit -m "test(oc4j): 验证测试通过"
```

---

## Phase 6: 文档

### Task 21: 创建 README

**Files:**
- Create: `sdk/oc4j/README.md`

**Step 1: 创建 README**

```markdown
# OpenCode Java SDK (oc4j)

Java SDK for OpenCode Server.

## Installation

```xml
<dependency>
    <groupId>ai.opencode</groupId>
    <artifactId>oc4j</artifactId>
    <version>0.1.0</version>
</dependency>
```

## Quick Start

### Synchronous Client

```java
import ai.opencode.sdk.*;

try (OpenCodeClient client = new OpenCodeClient()) {
    // Health check
    Map<String, Object> health = client.getGlobal().health();
    System.out.println("Healthy: " + health.get("healthy"));
    
    // List sessions
    List<Session> sessions = client.getSession().list();
    
    // List permissions
    List<PermissionRequest> permissions = client.getPermission().list();
    for (PermissionRequest p : permissions) {
        System.out.println("Permission: " + p.getPermission());
        client.getPermission().reply(p.getId(), "once", null);
    }
}
```

### Asynchronous Client

```java
import ai.opencode.sdk.*;
import java.util.concurrent.CompletableFuture;

try (AsyncOpenCodeClient client = new AsyncOpenCodeClient()) {
    CompletableFuture<List<Session>> sessions = 
        client.getSession().list();
    
    sessions.thenApply(list -> {
        System.out.println("Found " + list.size() + " sessions");
        return list;
    });
}
```

## Configuration

```java
ClientConfig config = ClientConfig.builder()
    .baseUrl("http://127.0.0.1:4096")
    .username("opencode")
    .password("your-password")
    .timeout(Duration.ofSeconds(60))
    .directory("/path/to/project")
    .build();

OpenCodeClient client = new OpenCodeClient(config);
```

## API Reference

### Session API
- `list()` - List all sessions
- `get(id)` - Get session by ID
- `create(title, directory)` - Create new session
- `delete(id)` - Delete session
- `todos(id)` - Get session todos

### Permission API
- `list()` - List pending permissions
- `reply(id, reply, message)` - Reply to permission request
- `respond(sessionId, permissionId, response)` - Respond to permission (deprecated)

### File API
- `list(path)` - List files
- `read(path)` - Read file content
- `status()` - Get file status

## License

MIT
```

**Step 2: Commit**

```bash
git add sdk/oc4j/README.md
git commit -m "docs(oc4j): 创建项目 README"
```

---

## 完成检查清单

- [ ] Maven 项目结构完整
- [ ] 所有核心 API 模块实现
- [ ] 同步和异步客户端可用
- [ ] 单元测试通过
- [ ] 文档完整
- [ ] 代码格式化
- [ ] Git 提交历史清晰

---

**"Plan complete and saved to `sdk/oc4j/docs/plans/2026-03-17-opencode-java-sdk.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**
