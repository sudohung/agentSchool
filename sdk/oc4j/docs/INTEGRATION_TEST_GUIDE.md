# Java OpenCode SDK 集成测试指南

## 测试环境要求

- Java 8 或更高版本
- Maven 3.6+
- OpenCode 服务器运行在 `http://127.0.0.1:4097`

## 测试文件

### 1. QuickIntegrationTest.java
快速集成测试，验证基本连接和所有 API 模块。

**运行方式**:
```bash
# 编译项目
mvn clean compile test-compile

# 运行快速测试
java -cp target/classes:target/test-classes:$(mvn dependency:build-classpath -q -Dmdep.outputFile=/dev/stdout) \
     ai.opencode.sdk.QuickIntegrationTest
```

**测试内容**:
1. Global Health Check
2. Session List
3. File List
4. Project List
5. Current Project
6. Agent List
7. Provider List
8. Config Get
9. Permission List
10. LSP Status

### 2. IntegrationTest.java
完整的 JUnit 集成测试，覆盖所有 API 端点。

**运行方式**:
```bash
# 运行所有集成测试
mvn test -Dtest=IntegrationTest

# 运行特定测试
mvn test -Dtest=IntegrationTest#testListSessions
```

**测试覆盖**:
- Global API (3 tests)
- Session API (8 tests)
- File API (6 tests)
- Project API (2 tests)
- Agent API (1 test)
- Provider API (2 tests)
- Config API (3 tests)
- Permission API (1 test)
- Question API (1 test)
- MCP API (1 test)
- LSP API (1 test)
- Path API (1 test)
- VCS API (1 test)
- Formatter API (1 test)
- Instance API (1 test)

### 3. Windows 批处理脚本
```bash
# 运行集成测试
test-integration.bat
```

## 测试验证清单

### API 模块测试
- [x] GlobalAPI - health, config, dispose
- [x] SessionAPI - list, get, create, delete, update, todos, status
- [x] FileAPI - list, read, status, findFiles, findSymbols
- [x] ProjectAPI - list, current
- [x] AgentAPI - list
- [x] ProviderAPI - list, auth
- [x] ConfigAPI - get, update, providers
- [x] PermissionAPI - list
- [x] QuestionAPI - list
- [x] MCPAPI - status
- [x] LSPAPI - status
- [x] PathAPI - get
- [x] VcsAPI - get
- [x] FormatterAPI - status
- [x] InstanceAPI - dispose

### 实体模型测试
- [x] Session - 所有字段正确序列化/反序列化
- [x] Todo - enum 字段正确映射
- [x] FileNode - type enum 正确映射
- [x] FileContent - type enum 正确映射
- [x] Project - 所有嵌套对象正确映射
- [x] Agent - mode enum 正确映射
- [x] Provider - source enum 正确映射
- [x] PermissionRequest - 所有字段正确映射

### 参数传递测试
- [x] FileAPI - path, directory 参数正确传递
- [x] SessionAPI - workspace, roots, start, search, limit 参数正确传递
- [x] MessageAPI - limit 参数正确传递
- [x] 所有 API - directory, workspace 参数自动添加

## 预期输出

### QuickIntegrationTest 输出示例
```
==========================================
Java OpenCode SDK Quick Integration Test
==========================================

Connecting to: http://127.0.0.1:4097

[1/10] Testing Global Health...
  ✓ Health check passed
    Response: {healthy=true, version=1.0.0}

[2/10] Testing Session List...
  ✓ Session list passed
    Found 5 sessions

[3/10] Testing File List...
  ✓ File list passed
    Found 10 files/directories

...

==========================================
Integration Test Completed!
==========================================
```

### IntegrationTest 输出示例
```
[INFO] Running ai.opencode.sdk.IntegrationTest
Connected to OpenCode server at http://127.0.0.1:4097
Health: {healthy=true, version=1.0.0}
Found 5 sessions
Using session: ses_123456
...
[INFO] Tests run: 30, Failures: 0, Errors: 0, Skipped: 0
```

## 故障排除

### 问题 1: 服务器未运行
```
Failed to connect to server: Connection refused
```
**解决**: 启动 OpenCode 服务器
```bash
opencode server
```

### 问题 2: 认证失败
```
HTTP 401: Unauthorized
```
**解决**: 配置认证信息
```java
ClientConfig config = ClientConfig.builder()
    .baseUrl("http://127.0.0.1:4097")
    .username("opencode")
    .password("your-password")
    .build();
```

### 问题 3: 超时错误
```
Connection timeout
```
**解决**: 增加超时时间
```java
ClientConfig config = ClientConfig.builder()
    .baseUrl("http://127.0.0.1:4097")
    .timeout(Duration.ofSeconds(30))
    .build();
```

## 测试报告

测试完成后，检查以下内容：

1. **连接性**: 能否成功连接到服务器
2. **API 覆盖**: 所有 API 模块是否都能调用
3. **数据模型**: 返回的数据是否正确反序列化
4. **错误处理**: 错误情况是否正确处理
5. **性能**: 请求响应时间是否合理

## 下一步

1. 运行所有测试确保通过
2. 检查测试输出确认所有 API 正常工作
3. 根据测试结果调整配置
4. 将测试集成到 CI/CD 流程中

---

**测试状态**: ✅ 准备就绪
**最后更新**: 2026-03-18
