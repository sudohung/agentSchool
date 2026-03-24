# OCJBot 架构图与流程图

## 设计目标

> **设计一个高效的 Harness 工程，通过多 Agent 协作完成复杂任务**

**核心理念**：
- **Agent = 模型 + Harness + Runtime**
- **Harness 是 Agent 的神经系统**，负责感知→规划→行动→记忆的完整闭环
- **多 Agent 协作**：通过 Harness 编排多个专业 Agent，实现复杂任务的分解与协作
- **对标 OpenClaw**：提供更系统化的 Harness 架构和更强的多 Agent 协作能力

## 1. OCJBot 完整架构图

```mermaid
graph TB
    subgraph External["外部世界"]
        User[用户输入]
        ExternalSystem[外部系统]
        DataSource[数据源]
    end

    subgraph Agent["Agent 系统"]
        subgraph Harness["Harness - Agent 神经系统"]
            subgraph Perception["感知层 Perception"]
                PromptEngine[Prompt Engine]
                RAGPipeline[RAG Pipeline]
                SensoryNormalizer[Sensory Normalizer]
            end
            
            subgraph Planning["规划引擎 Planning"]
                ReActLoop[ReAct Loop]
                PlanExecute[Plan and Execute]
                SelfReflection[Self Reflection]
            end
            
            subgraph Action["行动层 Action"]
                ToolExecutor[Tool Executor]
                SandboxRunner[Sandbox Runner]
                ErrorHandler[Error Handler]
            end
            
            subgraph Memory["内存系统 Memory"]
                ShortTerm[Short-term Memory]
                LongTerm[Long-term Memory]
                Working[Working Memory]
            end
            
            subgraph Guardrails["护栏系统 Guardrails"]
                InputGuard[Input Guardrail]
                OutputGuard[Output Guardrail]
                CostLimiter[Cost Limiter]
            end
        end
        
        subgraph Runtime["Runtime - LLM能力抽象层"]
            AgentRuntime[AgentRuntime 接口]
            OpenCodeRuntime[OpenCodeRuntime]
            DirectLLMRuntime[DirectLLMRuntime]
            MockRuntime[MockRuntime]
        end
        
        subgraph Extension["扩展层"]
            ToolRegistry[Tool Registry]
            SkillRegistry[Skill Registry]
            PluginManager[Plugin Manager]
            EventBus[Event Bus]
        end
    end

    subgraph LLM["底层 LLM 服务"]
        OpenCode[OpenCode Server]
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
    end

    User --> Perception
    ExternalSystem --> Perception
    DataSource --> Perception
    
    Perception --> Planning
    Planning --> Action
    Action --> Memory
    Memory --> Perception
    
    Guardrails --> Perception
    Guardrails --> Action
    
    Planning --> AgentRuntime
    AgentRuntime --> OpenCodeRuntime
    AgentRuntime --> DirectLLMRuntime
    AgentRuntime --> MockRuntime
    
    OpenCodeRuntime --> OpenCode
    DirectLLMRuntime --> OpenAI
    DirectLLMRuntime --> Anthropic
    
    Extension --> Harness
```

## 2. 用户任务处理流程图（ReAct Loop）

```mermaid
flowchart TB
    Start([开始]) --> Init[初始化 AgentContext]
    Init --> SetGoal[设置 Goal 目标]
    
    SetGoal --> CheckGuardrails{护栏检查}
    CheckGuardrails -->|超出限制| CostExceeded([成本超限退出])
    CheckGuardrails -->|通过| Perception
    
    subgraph PerceptionPhase["1. 感知阶段"]
        Perception[感知输入]
        BuildPrompt[构建 Prompt]
        RAGSearch[RAG 检索]
        NormalizeInput[输入归一化]
        
        Perception --> BuildPrompt
        BuildPrompt --> RAGSearch
        RAGSearch --> NormalizeInput
    end
    
    NormalizeInput --> PlanningPhase
    
    subgraph PlanningPhase["2. 规划阶段"]
        CallLLM[调用 LLM Runtime]
        GenerateThought[生成 Thought]
        GenerateAction[生成 Action]
        
        CallLLM --> GenerateThought
        GenerateThought --> GenerateAction
    end
    
    GenerateAction --> CheckFinished{是否完成?}
    CheckFinished -->|是| Success([成功返回结果])
    CheckFinished -->|否| CheckAction{有工具调用?}
    
    CheckAction -->|否| CheckIterations
    CheckAction -->|是| ActionPhase
    
    subgraph ActionPhase["3. 行动阶段"]
        ExecuteTool[执行工具]
        SandboxExec[沙箱运行]
        HandleError[错误处理]
        
        ExecuteTool --> SandboxExec
        SandboxExec --> HandleError
    end
    
    HandleError --> ObservePhase
    
    subgraph ObservePhase["4. 观察阶段"]
        GetResult[获取执行结果]
        UpdateMemory[更新内存]
        RecordHistory[记录对话历史]
        
        GetResult --> UpdateMemory
        UpdateMemory --> RecordHistory
    end
    
    RecordHistory --> CheckIterations
    
    CheckIterations{达到最大迭代?}
    CheckIterations -->|否| CheckGuardrails
    CheckIterations -->|是| MaxIterExceeded([最大迭代超限])
    
    CostExceeded --> End([结束])
    Success --> End
    MaxIterExceeded --> End
```

## 3. Runtime 抽象层架构

```mermaid
graph TB
    subgraph HarnessLayer["Harness 层"]
        ReActLoop[ReAct Loop]
        PlanningEngine[Planning Engine]
    end
    
    subgraph RuntimeInterface["Runtime 接口层"]
        AgentRuntime[AgentRuntime 接口]
        
        subgraph RuntimeMethods["核心方法"]
            Session[会话管理]
            Message[消息交互]
            Tool[工具执行]
            Event[事件订阅]
            Permission[权限管理]
        end
    end
    
    subgraph RuntimeImpl["Runtime 实现"]
        OpenCode[OpenCodeRuntime<br/>基于 oc4j SDK]
        DirectLLM[DirectLLMRuntime<br/>LangChain4j]
        Mock[MockRuntime<br/>测试用]
    end
    
    subgraph Backend["底层服务"]
        OpenCodeServer[OpenCode Server]
        OpenAIAPI[OpenAI API]
        AnthropicAPI[Anthropic API]
    end
    
    HarnessLayer --> AgentRuntime
    AgentRuntime --> RuntimeMethods
    AgentRuntime --> OpenCode
    AgentRuntime --> DirectLLM
    AgentRuntime --> Mock
    
    OpenCode --> OpenCodeServer
    DirectLLM --> OpenAIAPI
    DirectLLM --> AnthropicAPI
```

## 4. 三层架构说明

| 层级 | 职责 | 实现方式 |
|------|------|----------|
| **Harness** | Agent 神经系统，感知→规划→行动→记忆 | 业务逻辑 |
| **Runtime** | LLM 能力抽象，会话/消息/工具/事件 | 接口 + 多实现 |
| **底层** | 具体 LLM 服务 | OpenCode Server / OpenAI API |

## 5. Harness 四层架构说明

| 组件 | 职责 | 类比 |
|------|------|------|
| **感知层** | 将原始数据转为模型可理解的格式 | 眼睛、耳朵 |
| **规划引擎** | 推理循环、决策、控制流 | 大脑皮层 |
| **行动层** | 执行工具、影响现实世界 | 双手 |
| **内存系统** | 状态管理、记忆存储 | 海马体 |
| **护栏系统** | 安全边界、成本控制 | 免疫系统 |

## 6. 多 Agent 协作架构

```mermaid
graph TB
    subgraph UserLayer[用户层]
        User[用户任务]
    end
    
    subgraph Orchestrator[编排层 - Orchestrator Agent]
        TaskParser[任务解析]
        TaskSplitter[任务拆分]
        AgentSelector[Agent 选择]
        ResultAggregator[结果聚合]
    end
    
    subgraph AgentPool[Agent 池]
        subgraph CoderAgent[Coder Agent]            
            CoderHarness[Harness]
            CoderRuntime[Runtime]
            CoderTools[代码工具]
        end
        
        subgraph ResearcherAgent[Researcher Agent]
            ResearcherHarness[Harness]
            ResearcherRuntime[Runtime]
            ResearcherTools[搜索工具]
        end
        
        subgraph AnalystAgent[Analyst Agent]
            AnalystHarness[Harness]
            AnalystRuntime[Runtime]
            AnalystTools[分析工具]
        end
        
        subgraph ExecutorAgent[Executor Agent]
            ExecutorHarness[Harness]
            ExecutorRuntime[Runtime]
            ExecutorTools[执行工具]
        end
    end
    
    subgraph SharedLayer[共享层]
        SharedMemory[共享内存]
        EventBus[事件总线]
        MessageQueue[消息队列]
    end
    
    User --> TaskParser
    TaskParser --> TaskSplitter
    TaskSplitter --> AgentSelector
    
    AgentSelector --> CoderAgent
    AgentSelector --> ResearcherAgent
    AgentSelector --> AnalystAgent
    AgentSelector --> ExecutorAgent
    
    CoderAgent --> SharedMemory
    ResearcherAgent --> SharedMemory
    AnalystAgent --> SharedMemory
    ExecutorAgent --> SharedMemory
    
    CoderAgent --> EventBus
    ResearcherAgent --> EventBus
    AnalystAgent --> EventBus
    ExecutorAgent --> EventBus
    
    SharedMemory --> ResultAggregator
    EventBus --> ResultAggregator
    ResultAggregator --> User
```

## 7. 多 Agent 协作流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Orchestrator as 编排 Agent
    participant Agent1 as 专业 Agent 1
    participant Agent2 as 专业 Agent 2
    participant Shared as 共享层
    
    User->>Orchestrator: 提交复杂任务
    Orchestrator->>Orchestrator: 解析并拆分任务
    
    par 并行执行
        Orchestrator->>Agent1: 分配子任务 A
        Agent1->>Shared: 写入中间结果
        Agent1->>Orchestrator: 返回结果 A
    and
        Orchestrator->>Agent2: 分配子任务 B
        Agent2->>Shared: 读取 Agent1 结果
        Agent2->>Shared: 写入中间结果
        Agent2->>Orchestrator: 返回结果 B
    end
    
    Orchestrator->>Shared: 读取所有结果
    Orchestrator->>Orchestrator: 聚合结果
    Orchestrator->>User: 返回最终结果
```

## 8. 与 OpenClaw 对标分析

| 维度 | OpenClaw | OCJBot | 说明 |
|------|----------|--------|------|
| **架构理念** | Plugin-based | Harness-based | Harness 是神经系统，统一编排 |
| **感知层** | Prompt Templates | PerceptionLayer + RAG | 更系统化的输入处理 |
| **规划引擎** | 简单循环 | ReAct/Plan-Exec/Reflection | 多种推理模式支持 |
| **行动层** | Tool Calling | ActionLayer + Sandbox | 安全沙箱执行 |
| **内存系统** | Mem0 插件 | 内置 MemorySystem | 深度集成，支持多 Agent 共享 |
| **护栏** | 无 | Guardrails | 生产必备的安全边界 |
| **多 Agent** | 单 Agent 为主 | 原生多 Agent 协作 | 编排层 + Agent 池 |
| **扩展性** | Plugin 机制 | Plugin + Skill + Tool | 三层扩展体系 |

## 9. OCJBot 核心优势

```mermaid
mindmap
  root((OCJBot))
    Harness 架构
      感知-规划-行动-记忆
      完整闭环
      可插拔组件
    多 Agent 协作
      编排 Agent
      专业 Agent 池
      共享内存
      事件驱动通信
    Runtime 抽象
      多 LLM 后端
      统一接口
      无缝切换
    生产就绪
      护栏系统
      成本控制
      安全沙箱
      错误处理
```

---

*文档版本: 1.1.0*
*最后更新: 2026-03-24*
