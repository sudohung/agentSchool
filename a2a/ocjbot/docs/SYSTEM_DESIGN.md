# OCJBot - Agent OS 系统设计文档 v2.1

## 1. 核心论点

### 1.1 Agent = 模型 + Harness + Runtime

> **LLM 只是一个预测下一个 Token 的概率引擎。**
> **Agent 是一个通过一系列行动追求目标的系统。**
> **Harness 是弥合原始智能与生产力工作的基础设施。**
> **Runtime 是底层 LLM 能力的抽象层，让 Harness 不依赖具体实现。**

```
┌─────────────────────────────────────────────────────────┐
│                        Agent                            │
│                                                         │
│    ┌─────────┐              ┌─────────────────────┐    │
│    │   LLM   │   ← "大脑"    │      Harness        │    │
│    │ (模型)  │              │  (感知/规划/行动/记忆) │    │
│    └─────────┘              └─────────────────────┘    │
│         ↑                            ↑                  │
│         │                            │                  │
│    ┌────┴────────────────────────────┴────┐            │
│    │              Runtime                  │            │
│    │       (LLM 能力抽象层)                 │            │
│    │   OpenCode / Direct LLM / Mock       │            │
│    └──────────────────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 三层架构

| 层级 | 职责 | 实现方式 |
|------|------|----------|
| **Harness** | Agent 神经系统，感知→规划→行动→记忆 | 业务逻辑 |
| **Runtime** | LLM 能力抽象，会话/消息/工具/事件 | 接口 + 多实现 |
| **底层** | 具体 LLM 服务 | OpenCode Server / OpenAI API |

| 组件 | 职责 | 类比 |
|------|------|------|
| **感知层** | 将原始数据转为模型可理解的格式 | 眼睛、耳朵 |
| **规划引擎** | 推理循环、决策、控制流 | 大脑皮层 |
| **行动层** | 执行工具、影响现实世界 | 双手 |
| **内存系统** | 状态管理、记忆存储 | 海马体 |
| **护栏系统** | 安全边界、成本控制 | 免疫系统 |

---

## 2. Harness 四层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         External World                               │
│              用户输入 / 外部系统 / 数据源 / 物理世界                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     1. 感知层 (Perception Layer)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Prompt      │  │ RAG         │  │ Sensory     │                 │
│  │ Engine      │  │ Pipeline    │  │ Normalizer  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  职责：将原始数据转换为模型可以消化的格式                              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     2. 规划引擎 (Planning Engine)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ ReAct       │  │ Plan &      │  │ Self        │                 │
│  │ Loop        │  │ Execute     │  │ Reflection  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  职责：推理循环、决策、控制流（"思考"发生的地方）                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     3. 行动层 (Action Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Tool        │  │ Sandbox     │  │ Error       │                 │
│  │ Executor    │  │ Runner      │  │ Handler     │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  职责：执行工具、影响现实世界、安全沙箱                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     4. 内存系统 (Memory System)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Short-term  │  │ Long-term   │  │ Working     │                 │
│  │ Memory      │  │ Memory      │  │ Memory      │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  职责：状态管理、对话历史、持久化记忆                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     5. 护栏系统 (Guardrails)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Input       │  │ Output      │  │ Cost        │                 │
│  │ Guardrail   │  │ Guardrail   │  │ Limiter     │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                      │
│  职责：安全边界、PII过滤、格式验证、成本控制                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件详解

### 3.1 感知层 (Perception Layer)

**职责**：将原始数据转换为模型可以消化的格式

```java
public interface PerceptionLayer {
    
    /**
     * 构建完整的感知输入
     */
    PerceptionInput perceive(PerceptionContext context);
}

public record PerceptionInput(
    List<ChatMessage> messages,      // 对话历史
    String systemPrompt,             // 系统提示词
    List<Document> ragDocuments,     // RAG 检索文档
    Map<String, Object> variables    // 模板变量
) {}
```

**子组件**：

| 组件 | 职责 |
|------|------|
| **PromptEngine** | 动态组装系统指令、模板渲染 |
| **RAGPipeline** | 向量检索、文档注入 |
| **SensoryNormalizer** | HTML/PDF/Schema → Markdown/JSON |

### 3.2 规划引擎 (Planning Engine)

**职责**：推理循环、决策、控制流 —— "思考"发生的地方

```java
public interface PlanningEngine {
    
    /**
     * 执行推理循环
     */
    PlanResult plan(PlanContext context, Goal goal);
}

public interface AgentLoop {
    
    /**
     * 核心 ReAct 循环
     */
    LoopResult run(Goal goal, AgentContext context);
}
```

**推理模式**：

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **ReAct** | Reason + Act，思考→行动→观察 | 通用任务 |
| **Plan & Execute** | 先规划多步骤，再顺序执行 | 复杂任务 |
| **Self-Reflection** | 执行前自我批判评估 | 高风险任务 |

### 3.3 行动层 (Action Layer)

**职责**：执行工具、影响现实世界

```java
public interface ActionLayer {
    
    /**
     * 执行工具调用
     */
    ActionResult execute(ToolCall call, ActionContext context);
    
    /**
     * 在沙箱中执行代码
     */
    SandboxResult runInSandbox(String code, SandboxConfig config);
}
```

**关键能力**：

| 能力 | 描述 |
|------|------|
| **Tool Definition** | JSON Schema 定义工具参数 |
| **Sandbox Execution** | Docker/E2B 安全沙箱 |
| **Error Handling** | 捕获错误反馈给模型修正 |

### 3.4 内存系统 (Memory System)

**职责**：状态管理、记忆存储

```java
public interface MemorySystem {
    
    /**
     * 短期记忆：当前会话
     */
    ShortTermMemory getShortTermMemory(String sessionId);
    
    /**
     * 长期记忆：持久化存储
     */
    LongTermMemory getLongTermMemory(String userId);
    
    /**
     * 工作记忆：当前任务
     */
    WorkingMemory getWorkingMemory(String taskId);
}
```

**记忆类型**：

| 类型 | 存储 | 生命周期 |
|------|------|----------|
| Short-term | 内存 | 会话结束 |
| Long-term | 向量数据库 | 永久 |
| Working | 内存 | 任务结束 |

### 3.5 护栏系统 (Guardrails)

**职责**：安全边界、成本控制

```java
public interface Guardrails {
    
    /**
     * 输入护栏：过滤敏感信息
     */
    GuardrailResult validateInput(PerceptionInput input);
    
    /**
     * 输出护栏：验证格式
     */
    GuardrailResult validateOutput(AgentOutput output);
    
    /**
     * 成本护栏：限制迭代次数
     */
    boolean checkCostLimit(AgentContext context);
}
```

---

## 4. Agent Loop 核心流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Loop (ReAct)                           │
│                                                                      │
│    ┌─────────┐                                                       │
│    │  START  │                                                       │
│    └────┬────┘                                                       │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────────────────────────────────────────────────────────┐  │
│    │  1. 感知 (Perception)                                        │  │
│    │     - 构建 Prompt                                            │  │
│    │     - RAG 检索                                               │  │
│    │     - 归一化输入                                              │  │
│    └─────────────────────────────────────────────────────────────┘  │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────────────────────────────────────────────────────────┐  │
│    │  2. 规划 (Planning)                                          │  │
│    │     - 调用 LLM                                                │  │
│    │     - 生成 Thought + Action                                   │  │
│    └─────────────────────────────────────────────────────────────┘  │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────┐     ┌─────────┐                                      │
│    │finish?  │─NO─→│ 3. 行动 │                                      │
│    └────┬────┘     │(Action) │                                      │
│         │YES       └────┬────┘                                      │
│         │               │                                           │
│         │               ▼                                           │
│         │       ┌─────────────────────────────────────────────────┐│
│         │       │  4. 观察 (Observation)                          ││
│         │       │     - 获取工具执行结果                            ││
│         │       │     - 更新内存                                    ││
│         │       └─────────────────────────────────────────────────┘│
│         │               │                                           │
│         │               │                                            │
│         │               └──────────────────────┐                    │
│         │                                      │                    │
│         ▼                                      ▼                    │
│    ┌─────────────────────────────────────────────────────────────┐  │
│    │  5. 护栏检查 (Guardrails)                                    │  │
│    │     - 成本限制                                                │  │
│    │     - 安全检查                                                │  │
│    └─────────────────────────────────────────────────────────────┘  │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────┐                                                       │
│    │   END   │                                                       │
│    └─────────┘                                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 代码架构

```
src/main/java/ai/openclaw/ocjbot/
├── OcjbotApplication.java          # 主入口
│
├── harness/                         # Harness 核心
│   ├── Harness.java                 # Harness 接口
│   ├── HarnessImpl.java             # Harness 实现
│   └── AgentLoop.java               # Agent 循环接口
│
├── perception/                      # 感知层
│   ├── PerceptionLayer.java
│   ├── PerceptionInput.java
│   ├── prompt/
│   │   └── PromptEngine.java
│   ├── rag/
│   │   └── RAGPipeline.java
│   └── normalizer/
│       └── SensoryNormalizer.java
│
├── planning/                        # 规划引擎
│   ├── PlanningEngine.java
│   ├── PlanContext.java
│   ├── react/
│   │   └── ReActLoop.java
│   ├── planexec/
│   │   └── PlanAndExecute.java
│   └── reflection/
│       └── SelfReflection.java
│
├── action/                          # 行动层
│   ├── ActionLayer.java
│   ├── ToolExecutor.java
│   ├── SandboxRunner.java
│   └── ErrorHandler.java
│
├── memory/                          # 内存系统
│   ├── MemorySystem.java
│   ├── ShortTermMemory.java
│   ├── LongTermMemory.java
│   └── WorkingMemory.java
│
├── guardrails/                      # 护栏系统
│   ├── Guardrails.java
│   ├── InputGuardrail.java
│   ├── OutputGuardrail.java
│   └── CostLimiter.java
│
├── tool/                            # 工具定义
│   ├── Tool.java
│   ├── ToolRegistry.java
│   └── tools/
│       ├── BashTool.java
│       ├── ReadTool.java
│       └── WriteTool.java
│
├── llm/                             # LLM 集成
│   ├── LLMProvider.java
│   ├── OpenAIProvider.java
│   └── AnthropicProvider.java
│
├── gateway/                         # 网关层
│   └── GatewayServer.java
│
└── config/                          # 配置
    └── OcjbotConfig.java
```

---

## 6. 关键接口设计

### 6.1 Harness 接口

```java
public interface Harness {
    
    // 核心组件
    PerceptionLayer getPerceptionLayer();
    PlanningEngine getPlanningEngine();
    ActionLayer getActionLayer();
    MemorySystem getMemorySystem();
    Guardrails getGuardrails();
    
    // Agent 循环
    AgentLoop getAgentLoop();
    
    // 生命周期
    void initialize();
    void shutdown();
}
```

### 6.2 AgentLoop 接口

```java
public interface AgentLoop {
    
    /**
     * 执行 Agent 循环
     * 
     * @param goal 目标
     * @param context Agent 上下文
     * @return 循环结果
     */
    LoopResult run(Goal goal, AgentContext context);
    
    /**
     * 最大迭代次数
     */
    int getMaxIterations();
    
    /**
     * 是否启用自我反思
     */
    boolean isSelfReflectionEnabled();
}
```

### 6.3 ReActLoop 实现

```java
public class ReActLoop implements AgentLoop {
    
    private final Harness harness;
    
    @Override
    public LoopResult run(Goal goal, AgentContext context) {
        int iteration = 0;
        
        while (iteration < getMaxIterations()) {
            // 1. 护栏检查
            if (!harness.getGuardrails().checkCostLimit(context)) {
                return LoopResult.costExceeded();
            }
            
            // 2. 感知
            PerceptionInput input = harness.getPerceptionLayer()
                .perceive(PerceptionContext.from(goal, context));
            
            // 3. 规划
            PlanResult plan = harness.getPlanningEngine()
                .plan(PlanContext.from(input), goal);
            
            // 4. 判断是否完成
            if (plan.isFinished()) {
                return LoopResult.success(plan.getFinalAnswer());
            }
            
            // 5. 行动
            if (plan.hasToolCall()) {
                ActionResult action = harness.getActionLayer()
                    .execute(plan.getToolCall(), ActionContext.from(context));
                
                // 6. 观察 & 更新内存
                context.addObservation(action.getResult());
                harness.getMemorySystem()
                    .getShortTermMemory(context.getSessionId())
                    .addMessage(Message.assistant(plan.getThought()))
                    .addMessage(Message.tool(action.getResult()));
            }
            
            iteration++;
        }
        
        return LoopResult.maxIterationsExceeded();
    }
}
```

---

## 7. 与 OpenClaw 对标

| 维度 | OpenClaw | OCJBot | 说明 |
|------|----------|--------|------|
| 架构理念 | Plugin-based | Harness-based | Harness 是神经系统 |
| 感知层 | Prompt Templates | PerceptionLayer + RAG | 更系统化 |
| 规划引擎 | 简单循环 | ReAct/Plan-Exec/Reflection | 多种推理模式 |
| 行动层 | Tool Calling | ActionLayer + Sandbox | 安全沙箱 |
| 内存系统 | Mem0 插件 | 内置 MemorySystem | 深度集成 |
| 护栏 | 无 | Guardrails | 生产必备 |

---

## 8. Runtime 抽象层

### 8.1 设计理念

**Runtime 是 LLM 能力的抽象层**，让 Harness 不依赖具体的 LLM 实现：

```
┌─────────────────────────────────────────────────────────────┐
│                        Harness                               │
│              (感知/规划/行动/记忆/护栏)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ AgentRuntime 接口
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Runtime 实现                              │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ OpenCode    │  │ Direct LLM  │  │ Mock        │          │
│  │ Runtime     │  │ Runtime     │  │ Runtime     │          │
│  │ (oc4j)      │  │ (OpenAI)    │  │ (Testing)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    底层服务                                   │
│  OpenCode Server  │  OpenAI API  │  Anthropic API           │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 AgentRuntime 接口

```java
public interface AgentRuntime extends AutoCloseable {
    
    // 生命周期
    void initialize();
    RuntimeHealth checkHealth();
    String getName();
    RuntimeType getType();
    
    // 会话管理
    RuntimeSession createSession(SessionCreateRequest request);
    RuntimeSession getSession(String sessionId);
    List<RuntimeSession> listSessions();
    boolean deleteSession(String sessionId);
    
    // 消息交互
    RuntimeMessage sendMessage(String sessionId, MessageRequest request);
    RuntimeMessage sendText(String sessionId, String text);
    void sendMessageStream(String sessionId, MessageRequest request, 
                           Consumer<RuntimeEvent> eventHandler);
    
    // 工具执行
    ToolResult executeTool(String sessionId, ToolCallRequest request);
    RuntimeMessage executeShell(String sessionId, String command);
    
    // 事件订阅
    EventSubscription subscribeEvents(Consumer<RuntimeEvent> eventHandler);
    
    // 权限管理
    List<PermissionRequest> listPendingPermissions();
    boolean replyPermission(String permissionId, PermissionReply reply);
    
    // Provider/Agent
    List<RuntimeProvider> listProviders();
    List<RuntimeAgent> listAgents();
}
```

### 8.3 Runtime 实现

| 实现 | 描述 | 依赖 |
|------|------|------|
| **OpenCodeRuntime** | 基于 oc4j SDK，连接 OpenCode Server | oc4j-0.1.0.jar |
| **DirectLLMRuntime** | 直接调用 OpenAI/Anthropic API | langchain4j |
| **MockRuntime** | 测试用 Mock 实现 | 无 |

### 8.4 OpenCodeRuntime 示例

```java
// 创建 Runtime
OpenCodeRuntimeConfig config = OpenCodeRuntimeConfig.builder()
    .baseUrl("http://127.0.0.1:4096")
    .username("opencode")
    .password("password")
    .directory("/path/to/project")
    .build();

AgentRuntime runtime = new OpenCodeRuntime(config);
runtime.initialize();

// 创建会话
RuntimeSession session = runtime.createSession(
    SessionCreateRequest.of("My Session")
);

// 发送消息
RuntimeMessage response = runtime.sendText(
    session.getId(), 
    "Hello, Agent!"
);

// 订阅事件
runtime.subscribeEvents(event -> {
    System.out.println("Event: " + event.getType());
});

// 关闭
runtime.close();
```

### 8.5 Runtime 与 Harness 集成

```java
public class HarnessImpl implements Harness {
    
    private final AgentRuntime runtime;
    
    public HarnessImpl(AgentRuntime runtime) {
        this.runtime = runtime;
    }
    
    @Override
    public AgentLoop getAgentLoop() {
        return new ReActLoop(this, runtime);
    }
}
```

---

## 9. 开发路线

### Phase 0: Runtime 层 ✅
- [x] AgentRuntime 接口定义
- [x] Runtime 模型类
- [x] OpenCodeRuntime 实现 (基于 oc4j)
- [x] MockRuntime 实现

### Phase 1: 核心框架
- [x] Harness 接口设计
- [ ] AgentLoop 实现
- [ ] 基础配置

### Phase 2: 感知层
- [ ] PromptEngine
- [ ] RAGPipeline
- [ ] SensoryNormalizer

### Phase 3: 规划引擎
- [ ] ReActLoop
- [ ] PlanAndExecute
- [ ] SelfReflection

### Phase 4: 行动层
- [ ] ToolExecutor
- [ ] SandboxRunner
- [ ] ErrorHandler

### Phase 5: 内存系统
- [ ] ShortTermMemory
- [ ] LongTermMemory
- [ ] 向量存储集成

### Phase 6: 护栏系统
- [ ] InputGuardrail
- [ ] OutputGuardrail
- [ ] CostLimiter

### Phase 7: 生产就绪
- [ ] Gateway 层
- [ ] 监控告警
- [ ] 文档完善

---

## 10. 核心洞见

> **模型是标准化资源，Harness 才是核心竞争力。**
> **Runtime 是适配层，让 Harness 不依赖具体实现。**

1. **Harness 不是框架**，是 Agent 的神经系统
2. **核心是推理循环**，不是能力管理
3. **护栏是生产必备**，不是可选项
4. **感知→规划→行动→记忆** 是完整闭环
5. **Runtime 是抽象层**，支持多种 LLM 后端

---

*文档版本: 2.1.0*
*新增 Runtime 抽象层设计*
*最后更新: 2026-03-20*