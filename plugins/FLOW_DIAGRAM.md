# 飞书 OpenCode 机器人 - 系统交互流程

## 📊 完整架构流程图

```mermaid
graph TB
    subgraph "飞书客户端"
        A[用户在飞书发送消息]
        A --> B[消息内容: opencode 任务描述]
    end

    subgraph "飞书服务器"
        C[飞书消息服务器]
        B --> C
        C --> D{判断消息类型}
        D -->|文本消息| E[推送到 WebSocket]
        D -->|其他类型| F[忽略]
    end

    subgraph "OpenCode 插件 (个人电脑)"
        G[WSClient 长连接]
        E --> G
        G --> H[EventDispatcher]
        H --> I[im.message.receive_v1 事件]
        
        I --> J{检测触发关键词}
        J -->|opencode/@opencode| K[提取任务内容]
        J -->|其他| L[忽略消息]
        
        K --> M[创建 OpenCode Session]
        M --> N[存储会话映射<br/>chatId, userId, task]
        N --> O[发送临时回复: 处理中...]
    end

    subgraph "OpenCode 核心服务"
        P[OpenCode HTTP API<br/>localhost:4096]
        O --> P
        M --> P
        
        P --> Q[创建新会话]
        Q --> R[Session ID: xxx]
        
        R --> S[发送任务给 Agent]
        S --> T[增强提示词:<br/>任务 + 飞书群ID]
    end

    subgraph "OpenCode Agent"
        U[Agent 接收任务]
        T --> U
        U --> V[分析任务]
        V --> W[执行操作]
        
        W --> W1[读取文件]
        W --> W2[编辑代码]
        W --> W3[运行命令]
        W --> W4[调用工具]
        
        W1 --> X[任务完成]
        W2 --> X
        W3 --> X
        W4 --> X
    end

    subgraph "会话完成处理"
        Y[session.idle 事件]
        X --> Y
        Y --> Z[插件监听事件]
        Z --> AA[查找会话映射]
        AA --> AB{找到映射?}
        
        AB -->|是| AC[获取处理结果]
        AB -->|否| AD[忽略]
        
        AC --> AE[构建结果消息]
    end

    subgraph "结果返回"
        AF[调用飞书 API]
        AE --> AF
        AF --> AG[发送卡片消息]
        AG --> AH[消息内容:<br/>✅ 任务完成<br/>结果详情]
    end

    subgraph "飞书客户端"
        AI[用户收到回复]
        AH --> AI
        AI --> AJ[显示 OpenCode 处理结果]
    end

    style A fill:#e1f5ff
    style AJ fill:#e1f5ff
    style G fill:#fff4e6
    style P fill:#f3e5f5
    style U fill:#e8f5e9
    style Y fill:#fff9c4
    style AF fill:#fce4ec
```

---

## 🔄 时序图

```mermaid
sequenceDiagram
    participant User as 飞书用户
    participant Feishu as 飞书服务器
    participant WS as WSClient<br/>(长连接)
    participant Plugin as OpenCode 插件
    participant API as OpenCode API
    participant Agent as OpenCode Agent
    participant FeishuAPI as 飞书 API

    User->>Feishu: 发送消息<br/>"opencode 分析代码"
    Feishu->>WS: 推送 im.message.receive_v1 事件
    WS->>Plugin: EventDispatcher 触发
    
    Plugin->>Plugin: 检测关键词 "opencode"
    Plugin->>Plugin: 提取任务: "分析代码"
    
    Plugin->>API: POST /session<br/>{title: "飞书任务: 分析代码"}
    API-->>Plugin: {id: "session_xxx"}
    
    Plugin->>Plugin: 存储映射<br/>session_xxx → {chatId, task}
    
    Plugin->>FeishuAPI: 发送临时回复<br/>"✅ 处理中..."
    FeishuAPI-->>User: 显示消息
    
    Plugin->>API: POST /session/session_xxx/message<br/>{role: "user", content: "分析代码..."}
    API->>Agent: 触发 Agent 处理
    
    Agent->>Agent: 分析任务
    Agent->>Agent: 读取文件
    Agent->>Agent: 生成分析报告
    Agent-->>API: 任务完成
    
    API->>Plugin: session.idle 事件<br/>{sessionID: "session_xxx"}
    
    Plugin->>Plugin: 查找映射获取 chatId
    Plugin->>API: GET /session/session_xxx
    API-->>Plugin: {summary: "分析结果..."}
    
    Plugin->>FeishuAPI: 发送卡片消息<br/>"✅ 任务完成"
    FeishuAPI-->>User: 显示处理结果
    
    Note over User,FeishuAPI: 总耗时: ~5-30秒
```

---

## 🎯 核心组件交互

```mermaid
graph LR
    subgraph "飞书侧"
        A1[飞书 App]
        A2[飞书服务器]
        A3[WebSocket Server]
    end

    subgraph "OpenCode 插件"
        B1[WSClient<br/>长连接管理]
        B2[EventDispatcher<br/>事件分发]
        B3[MessageHandler<br/>消息处理]
        B4[SessionManager<br/>会话管理]
        B5[FeishuTools<br/>飞书工具]
    end

    subgraph "OpenCode 核心"
        C1[HTTP Server<br/>:4096]
        C2[Session API]
        C3[Agent Runtime]
    end

    A1 -->|发送消息| A2
    A2 -->|推送事件| A3
    A3 -->|WebSocket| B1
    
    B1 -->|事件通知| B2
    B2 -->|im.message.receive_v1| B3
    
    B3 -->|创建会话| B4
    B4 -->|HTTP API| C1
    C1 --> C2
    C2 --> C3
    
    C3 -->|处理完成| B4
    B4 -->|发送结果| B5
    B5 -->|API 调用| A2
    A2 -->|推送消息| A1

    style A1 fill:#e3f2fd
    style B1 fill:#fff3e0
    style C1 fill:#f3e5f5
    style B5 fill:#e8f5e9
```

---

## 📝 数据流转

```mermaid
graph TD
    A[飞书消息] --> B{消息类型判断}
    B -->|文本| C[解析内容]
    B -->|其他| Z[忽略]
    
    C --> D{包含关键词?}
    D -->|是| E[提取任务]
    D -->|否| Z
    
    E --> F[创建 Session]
    F --> G[Session ID + 映射关系]
    G --> H[发送给 Agent]
    
    H --> I[Agent 处理]
    I --> J{处理结果}
    J -->|成功| K[生成摘要]
    J -->|失败| L[错误信息]
    
    K --> M[构建卡片消息]
    L --> M
    
    M --> N[发送到飞书]
    N --> O[清理映射关系]

    style A fill:#e1f5ff
    style O fill:#e1f5ff
    style F fill:#fff4e6
    style I fill:#e8f5e9
    style M fill:#fce4ec
```

---

## 🔧 关键状态转换

```mermaid
stateDiagram-v2
    [*] --> Idle: 插件启动
    
    Idle --> MessageReceived: 收到飞书消息
    
    MessageReceived --> CheckKeyword: 解析消息
    CheckKeyword --> Idle: 无关键词
    CheckKeyword --> TaskExtracted: 包含 opencode
    
    TaskExtracted --> SessionCreating: 提取任务
    SessionCreating --> SessionCreated: 创建 OpenCode Session
    SessionCreated --> Processing: 发送任务给 Agent
    
    Processing --> Completed: Agent 完成
    Processing --> Failed: Agent 失败
    
    Completed --> ResultSending: 获取结果
    Failed --> ResultSending: 获取错误
    
    ResultSending --> Idle: 发送到飞书
    
    note right of Idle
        等待飞书消息
        长连接已建立
    end note
    
    note right of Processing
        Agent 正在处理
        可能需要较长时间
    end note
    
    note right of ResultSending
        调用飞书 API
        返回处理结果
    end note
```

---

## 🚨 错误处理流程

```mermaid
graph TD
    A[处理过程中] --> B{发生错误}
    
    B -->|WebSocket 断开| C[自动重连]
    C --> D{重连成功?}
    D -->|是| A
    D -->|否| E[记录日志]
    
    B -->|创建会话失败| F[发送错误消息]
    F --> G[通知用户]
    
    B -->|Agent 处理失败| H[获取错误信息]
    H --> I[发送错误卡片]
    I --> J[清理会话映射]
    
    B -->|飞书 API 失败| K[重试机制]
    K --> L{重试次数 < 3?}
    L -->|是| M[延迟重试]
    M --> A
    L -->|否| N[记录错误日志]

    style A fill:#e8f5e9
    style B fill:#fff9c4
    style E fill:#ffcdd2
    style G fill:#ffcdd2
```

---

## 💡 关键技术点

### 1. 长连接机制
```typescript
WSClient → WebSocket → 飞书服务器
├─ 自动建立连接
├─ 心跳保活
├─ 断线重连
└─ 事件推送
```

### 2. 事件处理链
```typescript
消息接收 → 关键词检测 → 任务提取 → 会话创建 → Agent处理 → 结果返回
```

### 3. 会话映射管理
```typescript
Map<SessionID, {
  chatId: string      // 飞书群ID
  userId: string      // 发送者ID
  task: string        // 任务内容
  startTime: number   // 开始时间
}>
```

### 4. 触发关键词
```
支持格式:
- "opencode <任务>"
- "@opencode <任务>"
- "/opencode <任务>"
```

---

## 📊 性能指标

| 环节 | 预期耗时 | 备注 |
|------|---------|------|
| 消息接收 | < 1s | WebSocket 实时推送 |
| 会话创建 | < 2s | HTTP API 调用 |
| Agent 处理 | 5-30s | 取决于任务复杂度 |
| 结果返回 | < 2s | 飞书 API 调用 |
| **总计** | **7-35s** | 端到端处理时间 |

---

## 🔐 安全机制

```mermaid
graph LR
    A[飞书消息] --> B[签名验证]
    B --> C{验证通过?}
    C -->|是| D[处理消息]
    C -->|否| E[拒绝请求]
    
    D --> F[权限检查]
    F --> G{有权限?}
    G -->|是| H[执行操作]
    G -->|否| I[返回错误]

    style B fill:#fff9c4
    style E fill:#ffcdd2
    style H fill:#e8f5e9
```

---

这个流程图展示了从用户发送消息到收到结果的完整交互过程！🎉