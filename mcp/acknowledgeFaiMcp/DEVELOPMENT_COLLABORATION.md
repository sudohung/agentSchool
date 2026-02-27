# FAISS MCP 开发协作流程总结

## 项目概述

**目标**: 创建一个轻量级的本地 FAISS 向量知识库 MCP 服务，支持语义搜索，默认使用 sentence-transformers 在 CPU 上计算嵌入，暴露 MCP 工具用于添加、搜索和保存索引。同时提供独立的 HTTP API 服务用于查询和管理记忆内容。

**技术栈**:
- FAISS: 向量索引
- sentence-transformers: CPU 嵌入计算
- ONNX Runtime + DirectML: AMD GPU 加速
- PyTorch + CUDA: NVIDIA GPU 加速
- SQLite + FTS5: 元数据存储与全文搜索
- FastMCP: MCP 协议服务端
- FastAPI: HTTP API 服务


---

## 协作模式总结

### Agent 与用户交互模式

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Agent
    
    loop 需求迭代
        U->>A: 提出需求/问题
        A->>A: 分析诊断
        
        alt 需要更多信息
            A->>U: 提问澄清
            U->>A: 提供信息
        end
        
        A->>U: 提供解决方案
        
        alt 方案可行
            U->>A: 确认实施
            A->>U: 执行代码修改
        else 需要调整
            U->>A: 反馈问题
        end
        
        U->>U: 验证结果
        U->>A: 报告结果
        
        alt 有新需求
            U->>A: 继续迭代
        else 满意
            U->>A: 结束
        end
    end
```

### Agent 角色定位

```mermaid
mindmap
  root((Agent 角色))
    架构师
      设计服务架构
      选择技术栈
      规划模块划分
    开发者
      实现代码
      修复 bug
      添加功能
    调试员
      分析错误日志
      定位问题根源
      提供解决方案
    文档编写者
      创建 README
      编写代码注释
      解释技术概念
    顾问
      提供技术选型建议
      权衡方案利弊
```

### 用户角色定位

```mermaid
mindmap
  root((用户 角色))
    需求方
      提出功能需求
      澄清业务场景
    测试者
      运行代码
      反馈错误信息
      验证解决方案
    决策者
      选择技术方案
      确认实现优先级
    提问者
      询问技术细节
      要求解释代码逻辑
```

---

## 关键协作模式

### 1. 问题驱动迭代

```mermaid
stateDiagram-v2
    [*] --> 用户报告问题
    用户报告问题 --> Agent分析诊断
    Agent分析诊断 --> 提出解决方案
    提出解决方案 --> 用户验证
    用户验证 --> 反馈调整: 验证失败
    反馈调整 --> Agent分析诊断
    用户验证 --> [*]: 验证成功
```

**实例**: HTTP 404 问题
- 用户: "127.0.0.1:59167 - POST /call_tool HTTP/1.1 404 Not Found"
- Agent: 创建探测工具、分析 FastMCP 路由机制、修复传输参数映射
- 结果: 成功连接

### 2. 需求渐进细化

```mermaid
graph LR
    A[硬编码模型] --> B[环境变量配置]
    B --> C[配置文件]
    C --> D[多后端支持]
    
    style A fill:#ffebee
    style D fill:#e8f5e9
```

### 3. 技术方案对比

```mermaid
flowchart TD
    A[用户需求] --> B{Agent 分析}
    B --> C[方案A]
    B --> D[方案B]
    B --> E[方案C]
    
    C --> F[优点分析]
    C --> G[缺点分析]
    D --> H[优点分析]
    D --> I[缺点分析]
    E --> J[优点分析]
    E --> K[缺点分析]
    
    F --> L{对比总结}
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[推荐方案]
    M --> N[用户选择]
    N --> O[实施]
    
    style M fill:#fff9c4
    style O fill:#e8f5e9
```

---

## 技术决策记录


| 决策点 | 选项 | 最终选择 | 理由 |
|--------|------|----------|------|
| 向量数据库 | FAISS vs Milvus vs Qdrant | FAISS | 轻量级、本地部署、CPU 友好 |
| 索引类型 | IndexFlatL2 vs IVF vs HNSW | IndexFlatL2 + IndexIDMap | 简单、适合小规模、支持 ID 映射 |
| 嵌入模型 | 默认 MiniLM vs 用户指定 | 配置文件 + 环境变量 | 灵活性、易切换 |
| 传输协议 | stdio vs SSE vs streamable-http | 全支持 | 不同场景需求 |
| GPU 加速 | torch-directml vs ONNX DirectML | ONNX DirectML (推荐) | 生产稳定、部署简单 |

---

## 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph "客户端层"
        C1[HTTP Client<br/>StreamableHTTP]
        C2[Stdio Client<br/>本地进程]
        C3[SSE Client<br/>Server-Sent Events]
        C4[Browser/API Client<br/>REST HTTP]
    end
    
    subgraph "MCP 服务层 (faiss_mcp_server.py)"
        MCP[FastMCP Server]
        
        subgraph "MCP 工具"
            T1[faiss_add_items]
            T2[faiss_search]
            T3[faiss_save]
        end
        
        subgraph "HTTP 路由"
            R1['/health']
            R2['/call_tool']
            R3['/mcp']
            R4['/sse']
        end
    end
    
    subgraph "HTTP API 服务层 (memory_api.py)"
        API[FastAPI Server]
        
        subgraph "API 路由"
            AR1[GET /memories]
            AR2[GET /memories/search]
            AR3[POST /memories]
            AR4[DELETE /memories/id]
            AR5[GET /faiss/stats]
            AR6[POST /faiss/search]
        end
    end
    
    subgraph "核心层"
        KB[FaissKB<br/>知识库管理]
        CFG[FaissConfig<br/>配置管理]
    end
    
    subgraph "嵌入层"
        subgraph "CPU 后端"
            ST[SentenceTransformer<br/>CPU 推理]
        end
        
        subgraph "AMD GPU 后端"
            ONNX[ONNX Runtime<br/>DirectML]
        end
        
        subgraph "NVIDIA GPU 后端"
            CUDA[PyTorch + CUDA<br/>sentence-transformers]
        end
        
        EMB[Embedder<br/>嵌入模型管理]
    end
    
    subgraph "存储层"
        IDX[faiss.index<br/>向量索引]
        DB[knowledge.db<br/>SQLite + FTS5]
        CONFIG[embedder_config.json<br/>模型配置]
    end
    
    C1 --> R3
    C2 --> MCP
    C3 --> R4
    C4 --> API
    
    R1 --> MCP
    R2 --> MCP
    R3 --> MCP
    R4 --> MCP
    
    MCP --> T1
    MCP --> T2
    MCP --> T3
    
    T1 --> KB
    T2 --> KB
    T3 --> KB
    
    KB --> CFG
    KB --> EMB
    
    EMB --> ST
    EMB --> ONNX
    EMB --> CUDA
    
    CFG --> CONFIG
    
    KB --> IDX
    KB --> DB
    
    API --> KB
    
    style MCP fill:#e1f5fe
    style API fill:#e1f5fe
    style KB fill:#f3e5f5
    style EMB fill:#fff3e0
    style ST fill:#e8f5e9
    style ONNX fill:#e8f5e9
    style CUDA fill:#e8f5e9
```

### 模块依赖关系

```mermaid
graph LR
    subgraph "配置模块"
        A[embedder_config.json]
        B[环境变量<br/>FAISS_EMBEDDER_MODEL<br/>FAISS_DIM<br/>FAISS_DEVICE<br/>FAISS_GPU_ID]
    end
    
    subgraph "MCP 服务模块"
        M[faiss_mcp_server.py<br/>FastMCP]
    end
    
    subgraph "HTTP API 模块"
        API[memory_api.py<br/>FastAPI]
    end
    
    subgraph "核心模块"
        C[FaissConfig]
        D[FaissKB]
        E[Embedder Manager]
    end
    
    subgraph "数据库模块"
        DB[MemoryAPIClient<br/>SQLite + FTS5]
    end
    
    subgraph "嵌入引擎"
        F[SentenceTransformer<br/>CPU]
        G[ONNX Runtime<br/>DirectML AMD GPU]
        H[PyTorch + CUDA<br/>NVIDIA GPU]
    end
    
    subgraph "存储"
        I[faiss.index<br/>向量索引]
        J[knowledge.db<br/>SQLite 数据库]
    end
    
    A --> C
    B --> C
    A --> E
    B --> E
    
    C --> D
    E --> D
    
    D --> DB
    DB --> J
    
    E --> F
    E --> G
    E --> H
    
    D --> I
    
    M --> D
    API --> DB
    API --> D
    
    style A fill:#fff9c4
    style B fill:#fff9c4
    style M fill:#e1f5fe
    style API fill:#e1f5fe
    style C fill:#e3f2fd
    style D fill:#f3e5f5
    style DB fill:#fce4ec
    style E fill:#fff3e0
```

---

## 核心数据流程

### 添加文档流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant MCP as FastMCP Server
    participant KB as FaissKB
    participant EMB as Embedder
    participant FAISS as FAISS Index
    participant DB as SQLite/knowledge.db
    
    Client->>MCP: faiss_add_items<br/>{params: [documents, metadatas]}
    
    alt 提供了 embeddings
        MCP->>KB: add_items(embeddings, ...)
        KB->>FAISS: index.add_with_ids(embeddings, ids)
    else 未提供 embeddings
        MCP->>KB: add_items(documents=docs, ...)
        KB->>EMB: encode(documents)
        EMB-->>KB: embeddings
        KB->>FAISS: index.add_with_ids(embeddings, ids)
    end
    
    KB->>FAISS: 保存向量索引
    
    loop 每个文档
        KB->>DB: store_memory(title, content, type, ...)
    end
    
    KB-->>MCP: 返回添加的 IDs
    MCP-->>Client: {"success": true, "added_ids": [...]}
```

### 语义搜索流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant MCP as FastMCP Server
    participant KB as FaissKB
    participant EMB as Embedder
    participant FAISS as FAISS Index
    participant DB as SQLite/knowledge.db
    
    Client->>MCP: faiss_search<br/>{query_text, k} 或 {query_embedding, k}
    
    alt 提供了 query_embedding
        MCP->>KB: search(embedding=vec, k=k)
    else 提供了 query_text
        MCP->>KB: search(query_text=text, k=k)
        KB->>EMB: encode([query_text])
        EMB-->>KB: embedding vector
    end
    
    KB->>FAISS: index.search(query_vec, k)
    FAISS-->>KB: distances, indices
    
    loop 每个结果
        KB->>DB: get_memory_by_id(id)
    end
    
    KB-->>MCP: 返回结果列表
    MCP-->>Client: {"success": true, "results": [...]}
```

### 配置加载流程

```mermaid
flowchart TD
    START([服务启动]) --> READ_CONFIG[读取 embedder_config.json]
    READ_CONFIG --> PARSE_ENV{检查环境变量}
    
    PARSE_ENV -->|FAISS_EMBEDDER_DEVICE| OVERRIDE_DEVICE[覆盖 device]
    PARSE_ENV -->|FAISS_EMBEDDER_MODEL| OVERRIDE_MODEL[覆盖 model_name]
    PARSE_ENV -->|FAISS_DIM| OVERRIDE_DIM[覆盖 dim]
    
    OVERRIDE_DEVICE --> MERGE[合并配置]
    OVERRIDE_MODEL --> MERGE
    OVERRIDE_DIM --> MERGE
    
    MERGE --> CHECK_DEVICE{device == ?}
    
    CHECK_DEVICE -->|cpu| LOAD_ST[加载 SentenceTransformer]
    CHECK_DEVICE -->|gpu| CHECK_ONNX{ONNX 文件存在?}
    
    CHECK_ONNX -->|是| LOAD_ONNX[加载 ONNX Runtime<br/>DirectML Provider]
    CHECK_ONNX -->|否| ERROR[抛出错误]
    
    LOAD_ST --> VALIDATE_DIM[验证维度匹配]
    LOAD_ONNX --> VALIDATE_DIM
    
    VALIDATE_DIM -->|匹配| INIT_KB[初始化 FaissKB]
    VALIDATE_DIM -->|不匹配| ERROR_DIM[抛出维度错误]
    
    INIT_KB --> START_SERVER[启动 MCP 服务]
    START_SERVER --> END([就绪])
    
    ERROR --> END
    ERROR_DIM --> END
    
    style START fill:#e8f5e9
    style END fill:#e8f5e9
    style ERROR fill:#ffebee
    style ERROR_DIM fill:#ffebee
```

---

## 传输协议

### 三种传输模式对比

```mermaid
graph TB
    subgraph "Stdio 传输"
        S1[父进程] -->|stdin/stdout| S2[MCP Server]
        S2 -->|stdin/stdout| S1
    end
    
    subgraph "SSE 传输"
        SSE1[HTTP Client] -->|GET /sse| SSE2[MCP Server]
        SSE2 -->|EventStream| SSE1
        SSE1 -->|POST /messages/| SSE2
    end
    
    subgraph "StreamableHTTP 传输"
        H1[HTTP Client] -->|POST /mcp| H2[MCP Server]
        H2 -->|JSON/SSE| H1
    end
    
    style S2 fill:#e3f2fd
    style SSE2 fill:#e3f2fd
    style H2 fill:#e3f2fd
```

### HTTP 路由结构

```mermaid
graph LR
    subgraph "FastMCP 路由"
        A[health<br/>GET] --> A1[健康检查]
        B[call_tool<br/>POST] --> B1[兼容路由<br/>调用工具]
        C[mcp<br/>POST] --> C1[StreamableHTTP<br/>MCP 协议]
        D[sse<br/>GET] --> D1[SSE 连接]
        E[messages/<br/>POST] --> E1[SSE 消息]
    end
    
    style A fill:#c8e6c9
    style B fill:#fff9c4
    style C fill:#bbdefb
    style D fill:#bbdefb
    style E fill:#bbdefb
```

---

## 协作流程时间线

### 阶段 1: 需求澄清与架构设计

```mermaid
graph LR
    subgraph "用户"
        U1[提出需求:<br/>FAISS MCP 服务]
        U2[确认技术选型]
    end
    
    subgraph "Agent"
        A1[分析现有 MCP 模式]
        A2[设计架构]
        A3[提出实现方案]
    end
    
    U1 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> U2
    
    style U1 fill:#e8f5e9
    style A2 fill:#e3f2fd
```

**协作成果**:
- 确定了技术栈：FAISS + sentence-transformers + FastMCP
- 确定了数据持久化方案：faiss.index + faiss_meta.json

---

### 阶段 2: 核心功能实现

```mermaid
stateDiagram-v2
    [*] --> 开发核心服务
    开发核心服务 --> 实现MCP工具
    实现MCP工具 --> 创建演示客户端
    创建演示客户端 --> 用户测试
    用户测试 --> 发现依赖问题: 安装FAISS失败
    发现依赖问题 --> Agent诊断
    Agent诊断 --> 提供安装方案
    提供安装方案 --> 问题解决
    问题解决 --> [*]
    
    note right of 发现依赖问题
        ModuleNotFoundError: 
        No module named 'faiss'
    end note
    
    note right of 提供安装方案
        conda install -c conda-forge 
        faiss-cpu numpy
    end note
```

---

### 阶段 3: HTTP 传输调试

```mermaid
flowchart TD
    START([用户报告 404]) --> CREATE_PROBE[Agent 创建探测工具]
    CREATE_PROBE --> RUN_PROBE[运行 http_probe.py]
    RUN_PROBE --> ANALYZE{分析结果}
    
    ANALYZE -->|/call_tool 404| FIND_ROUTE[分析 FastMCP 源码]
    ANALYZE -->|/sse 405| FIND_ROUTE
    
    FIND_ROUTE --> DISCOVER[发现挂载路径为 /mcp]
    DISCOVER --> FIX_MAPPING[修复传输参数映射]
    
    FIX_MAPPING --> ADD_ROUTES[添加兼容路由<br/>/health, /call_tool]
    ADD_ROUTES --> CREATE_CLIENT[创建 StreamableHTTP 客户端]
    CREATE_CLIENT --> VERIFY{用户验证}
    
    VERIFY -->|成功| SUCCESS([问题解决])
    VERIFY -->|失败| DEBUG[继续调试]
    DEBUG --> RUN_PROBE
    
    style START fill:#ffebee
    style SUCCESS fill:#e8f5e9
    style DISCOVER fill:#fff9c4
```

**关键发现**:
- FastMCP streamable-http 模式默认挂载路径为 `/mcp`
- 需要使用 MCP 客户端协议，而非直接 POST JSON

---

### 阶段 4: HuggingFace 缓存警告处理

```mermaid
flowchart LR
    A[用户报告警告] --> B{分析原因}
    B --> C[Windows 不支持<br/>普通用户创建 symlink]
    C --> D[HuggingFace 缓存<br/>回退到文件复制]
    D --> E{影响分析}
    
    E -->|功能| F[不影响]
    E -->|磁盘| G[占用更多空间]
    
    F --> H{解决方案}
    G --> H
    
    H -->|方案A| I[禁用 symlink<br/>HF_HUB_DISABLE_SYMLINKS=1]
    H -->|方案B| J[启用 Windows<br/>Developer Mode]
    
    I --> K[问题解决]
    J --> K
    
    style A fill:#fff9c4
    style K fill:#e8f5e9
```

---

### 阶段 5: 模型配置外部化

```mermaid
graph TB
    subgraph "迭代 1: 硬编码"
        A1[代码中写死<br/>all-MiniLM-L6-v2]
    end
    
    subgraph "迭代 2: 环境变量"
        A2[支持 FAISS_EMBEDDER_MODEL<br/>环境变量覆盖]
    end
    
    subgraph "迭代 3: 配置文件"
        A3[embedder_config.json<br/>持久化配置]
    end
    
    subgraph "迭代 4: 多后端"
        A4[支持 CPU/GPU<br/>不同后端配置]
    end
    
    A1 --> A2 --> A3 --> A4
    
    style A1 fill:#ffebee
    style A4 fill:#e8f5e9
```

**配置优先级**:

```mermaid
flowchart LR
    A[默认值<br/>all-MiniLM-L6-v2] --> B[配置文件<br/>embedder_config.json]
    B --> C[环境变量<br/>FAISS_EMBEDDER_MODEL]
    C --> D[最终生效值]
    
    style D fill:#e8f5e9
```

---

### 阶段 6: 多后端 Embedding 支持

```mermaid
flowchart TD
    subgraph "需求分析"
        REQ[支持 GPU 加速<br/>ONNX DirectML]
    end
    
    subgraph "方案对比"
        OPT_A[方案A: ONNX Runtime<br/>+ DirectML]
        OPT_B[方案B: torch-directml]
    end
    
    subgraph "方案A 优点"
        A1[生产稳定]
        A2[部署简单]
        A3[无需 PyTorch GPU]
    end
    
    subgraph "方案B 优点"
        B1[实现简单]
        B2[无需导出 ONNX]
    end
    
    subgraph "方案A 缺点"
        A4[需要导出 ONNX]
    end
    
    subgraph "方案B 缺点"
        B3[算子支持有限]
        B4[版本兼容问题]
    end
    
    REQ --> OPT_A
    REQ --> OPT_B
    
    OPT_A --> A1
    OPT_A --> A2
    OPT_A --> A3
    OPT_A --> A4
    
    OPT_B --> B1
    OPT_B --> B2
    OPT_B --> B3
    OPT_B --> B4
    
    A1 --> DECISION{选择方案}
    A2 --> DECISION
    A3 --> DECISION
    DECISION -->|推荐| IMPLEMENT[实现 ONNX 后端]
    
    style OPT_A fill:#e8f5e9
    style IMPLEMENT fill:#e8f5e9
```

**实现架构**:

```mermaid
classDiagram
    class EmbedderConfig {
        +device: str
        +cpu: CPUEmbedder
        +gpu: GPUEmbedder
        +dim: int
    }
    
    class CPUEmbedder {
        +backend: str
        +model_name: str
    }
    
    class GPUEmbedder {
        +backend: str
        +onnx_path: str
        +tokenizer: str
    }
    
    class Embedder {
        <<interface>>
        +encode(texts: List~str~) ndarray
    }
    
    class SentenceTransformerEmbedder {
        -model: SentenceTransformer
        +encode(texts) ndarray
    }
    
    class ONNXEmbedder {
        -session: InferenceSession
        -tokenizer: Tokenizer
        +encode(texts) ndarray
    }
    
    EmbedderConfig --> CPUEmbedder
    EmbedderConfig --> GPUEmbedder
    Embedder <|.. SentenceTransformerEmbedder
    Embedder <|.. ONNXEmbedder
    
    note for EmbedderConfig "embedder_config.json"
    note for SentenceTransformerEmbedder "CPU 后端"
    note for ONNXEmbedder "GPU 后端 (DirectML)"
```

---

## 文件清单

### 核心文件职责

| 文件 | 用途 | 依赖 |
|------|------|------|
| `faiss_mcp_server.py` | MCP 服务主程序 | faiss, sentence-transformers, mcp |
---

## 经验教训

### 成功经验

```mermaid
mindmap
  root((成功经验))
    增量开发
      最小可用版本
      逐步添加功能
      快速验证反馈
    配置外置
      配置文件
      环境变量
      灵活切换
    多传输支持
      stdio 本地
      SSE 实时
      HTTP 通用
    详细日志
      启动配置
      错误追踪
      调试友好
    探测工具
      快速定位
      独立验证
      问题隔离
```

*文档生成时间: 2026-02-26*  
*协作工具: OpenCode Agent*  
*文档版本: 2.0 (含 Mermaid 图表)*