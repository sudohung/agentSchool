# 中优先级功能缺失设计方案

> 版本：1.0
> 创建日期：2026-03-17
> 状态：设计完成

---

## 1. 概述

本文档定义了以下功能的实现方案：
1. **Git 交付** - 推送交付物到 Git 仓库
2. **S3 交付** - 上传交付物到 S3 存储
3. **性能分析器** - Agent 性能分析工具
4. **Agent 调试器** - Agent 调试工具
5. **CLI 工具** - 命令行管理工具

---

## 2. Git 交付设计

### 2.1 功能需求

| 功能 | 描述 |
|------|------|
| 克隆仓库 | 支持克隆远程 Git 仓库 |
| 创建分支 | 支持创建新分支或使用现有分支 |
| 复制文件 | 将交付物复制到仓库目录 |
| 提交推送 | 自动提交并推送到远程 |

### 2.2 接口设计

```python
class GitDeliveryConfig:
    """Git 交付配置"""
    repo_url: str           # 仓库 URL
    branch: str = "main"    # 分支名
    commit_message: str     # 提交信息
    author_name: str        # 作者名
    author_email: str       # 作者邮箱
    target_dir: str         # 目标目录
    create_branch: bool     # 是否创建新分支

class GitDeliveryExecutor:
    """Git 交付执行器"""
    
    async def deliver(
        self,
        artifact: DeliveryArtifact,
        config: GitDeliveryConfig
    ) -> DeliveryResult:
        """执行 Git 交付"""
        
    async def clone(self, repo_url: str, branch: str) -> Path:
        """克隆仓库"""
        
    async def commit_and_push(
        self,
        repo_path: Path,
        message: str,
        branch: str
    ) -> bool:
        """提交并推送"""
```

### 2.3 实现策略

```
1. 使用 subprocess 调用 git 命令（避免依赖 gitpython）
2. 流程：
   - 克隆/拉取仓库
   - 创建/切换分支
   - 复制交付物到目标目录
   - git add -> git commit -> git push
3. 错误处理：
   - 网络错误重试
   - 冲突检测
   - 权限验证
```

---

## 3. S3 交付设计

### 3.1 功能需求

| 功能 | 描述 |
|------|------|
| 上传文件 | 支持单文件和多文件上传 |
| 目录上传 | 支持整个目录上传 |
| 进度显示 | 显示上传进度 |
| 元数据 | 支持设置文件元数据 |

### 3.2 接口设计

```python
class S3DeliveryConfig:
    """S3 交付配置"""
    bucket: str             # S3 bucket 名
    key_prefix: str         # 键前缀
    region: str             # 区域
    acl: str = "private"    # 访问控制
    storage_class: str      # 存储类型
    metadata: Dict          # 元数据

class S3DeliveryExecutor:
    """S3 交付执行器"""
    
    async def deliver(
        self,
        artifact: DeliveryArtifact,
        config: S3DeliveryConfig
    ) -> DeliveryResult:
        """执行 S3 交付"""
        
    async def upload_file(
        self,
        file_path: Path,
        key: str,
        config: S3DeliveryConfig
    ) -> str:
        """上传单个文件"""
        
    async def upload_directory(
        self,
        dir_path: Path,
        key_prefix: str,
        config: S3DeliveryConfig
    ) -> List[str]:
        """上传整个目录"""
```

### 3.3 实现策略

```
1. 使用 boto3 库（AWS SDK for Python）
2. 支持无 boto3 时的降级模式（模拟上传）
3. 流程：
   - 验证凭证和 bucket
   - 打包文件（可选）
   - 并发上传
   - 验证上传成功
4. 进度回调支持
```

---

## 4. 性能分析器设计

### 4.1 功能需求

| 功能 | 描述 |
|------|------|
| Agent 执行时间分析 | 记录每个 Agent 的执行时间 |
| 方法耗时分析 | 分析各方法耗时 |
| 内存使用分析 | 追踪内存使用情况 |
| 报告生成 | 生成性能分析报告 |

### 4.2 接口设计

```python
@dataclass
class ProfileResult:
    """性能分析结果"""
    agent_id: str
    method_name: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_before: int
    memory_after: int
    memory_delta: int
    success: bool
    error: Optional[str]

@dataclass
class ProfileReport:
    """性能分析报告"""
    total_time: float
    agent_stats: Dict[str, AgentStats]
    method_stats: Dict[str, MethodStats]
    memory_peak: int
    bottlenecks: List[Bottleneck]

class Profiler:
    """性能分析器"""
    
    def start_profiling(self, session_id: str):
        """开始分析"""
        
    def stop_profiling(self) -> ProfileReport:
        """停止并生成报告"""
        
    def record_method(
        self,
        agent_id: str,
        method_name: str,
        duration: float,
        memory_delta: int
    ):
        """记录方法执行"""
        
    @contextmanager
    def profile_method(self, agent_id: str, method_name: str):
        """上下文管理器方式记录"""
```

### 4.3 实现策略

```
1. 使用 Python 内置模块：
   - time.perf_counter() 精确计时
   - tracemalloc 追踪内存
   - cProfile 函数级别分析
2. 装饰器模式：@profile_method
3. 上下文管理器：with profiler.profile_method(...)
4. 输出格式：
   - JSON 报告
   - 控制台表格
   - 火焰图数据（可选）
```

---

## 5. Agent 调试器设计

### 5.1 功能需求

| 功能 | 描述 |
|------|------|
| 状态检查 | 检查 Agent 当前状态 |
| 日志查看 | 查看 Agent 执行日志 |
| 断点设置 | 在特定条件暂停执行 |
| 变量检查 | 检查 Agent 内部变量 |
| 单步执行 | 支持单步调试模式 |

### 5.2 接口设计

```python
@dataclass
class Breakpoint:
    """断点"""
    id: str
    agent_id: Optional[str]
    method_name: Optional[str]
    condition: Optional[str]
    enabled: bool = True
    hit_count: int = 0

@dataclass
class DebugSession:
    """调试会话"""
    session_id: str
    agent_id: str
    status: str  # running, paused, stopped
    current_step: Optional[str]
    variables: Dict[str, Any]
    call_stack: List[str]

class AgentDebugger:
    """Agent 调试器"""
    
    def attach(self, agent_id: str) -> DebugSession:
        """附加到 Agent"""
        
    def detach(self, session_id: str):
        """分离调试"""
        
    def add_breakpoint(
        self,
        agent_id: str,
        method_name: str,
        condition: Optional[str] = None
    ) -> Breakpoint:
        """添加断点"""
        
    def remove_breakpoint(self, breakpoint_id: str):
        """移除断点"""
        
    def step_over(self, session_id: str):
        """单步跳过"""
        
    def step_into(self, session_id: str):
        """单步进入"""
        
    def continue_execution(self, session_id: str):
        """继续执行"""
        
    def get_variables(self, session_id: str) -> Dict[str, Any]:
        """获取变量"""
        
    def get_call_stack(self, session_id: str) -> List[str]:
        """获取调用栈"""
```

### 5.3 实现策略

```
1. 调试模式：
   - 同步调试：直接在当前进程
   - 远程调试：通过消息通道
2. 状态追踪：
   - 维护 Agent 状态快照
   - 记录执行路径
3. 断点机制：
   - 方法入口断点
   - 条件断点（表达式求值）
4. 输出：
   - 控制台交互
   - Web UI（可选）
```

---

## 6. CLI 工具设计

### 6.1 功能需求

| 功能 | 描述 |
|------|------|
| 项目管理 | 创建、配置项目 |
| Agent 管理 | 列出、启动、停止 Agent |
| 任务执行 | 执行任务并查看进度 |
| 报告查看 | 查看各种报告 |
| 配置管理 | 查看和修改配置 |

### 6.2 命令设计

```bash
# 项目管理
ats project create <name>              # 创建项目
ats project list                       # 列出项目
ats project info <name>                # 项目详情

# Agent 管理
ats agent list                         # 列出所有 Agent
ats agent create <role> [--name NAME]  # 创建 Agent
ats agent info <id>                    # Agent 详情
ats agent start <id>                   # 启动 Agent
ats agent stop <id>                    # 停止 Agent

# 任务执行
ats task run <description>             # 执行任务
ats task status <id>                   # 查看任务状态
ats task list                          # 列出任务

# 报告
ats report delivery <id>               # 查看交付报告
ats report performance                 # 性能报告
ats report metrics                     # 指标报告

# 配置
ats config show                        # 显示配置
ats config set <key> <value>           # 设置配置
ats config validate                    # 验证配置

# 调试
ats debug attach <agent-id>            # 附加调试
ats debug breakpoints                  # 列出断点
ats debug vars <session-id>            # 查看变量

# 工具
ats profile start                      # 开始性能分析
ats profile stop [--output FILE]       # 停止并生成报告
ats version                            # 显示版本
ats help [COMMAND]                     # 帮助信息
```

### 6.3 接口设计

```python
import click  # 或 typer

@click.group()
def cli():
    """Agent Team System CLI"""
    pass

@cli.group()
def project():
    """项目管理"""
    pass

@cli.group()
def agent():
    """Agent 管理"""
    pass

@cli.group()
def task():
    """任务执行"""
    pass

@cli.group()
def report():
    """报告查看"""
    pass

@cli.group()
def config():
    """配置管理"""
    pass

@cli.group()
def debug():
    """调试工具"""
    pass

@cli.group()
def profile():
    """性能分析"""
    pass
```

### 6.4 实现策略

```
1. 使用 click 或 typer 库（选择 typer，更现代）
2. 输出格式：
   - 表格：rich 库美化
   - JSON：--json 参数
   - 简洁：--quiet 参数
3. 配置文件：~/.ats/config.yaml
4. 交互模式：可选的 REPL
```

---

## 7. 文件结构

```
src/
├── delivery/
│   ├── deliverer.py          # 修改：添加 Git/S3 交付
│   ├── git_delivery.py       # 新增：Git 交付实现
│   └── s3_delivery.py        # 新增：S3 交付实现
│
└── infrastructure/
    └── devtools/
        ├── __init__.py       # 新增
        ├── profiler.py       # 新增：性能分析器
        ├── debugger.py       # 新增：Agent 调试器
        └── cli.py            # 新增：CLI 工具
```

---

## 8. 实现计划

| # | 任务 | 预计时间 | 优先级 |
|---|------|---------|--------|
| 1 | Git 交付实现 | 1.5h | P1 |
| 2 | S3 交付实现 | 1.5h | P1 |
| 3 | 性能分析器 | 1h | P1 |
| 4 | Agent 调试器 | 1h | P1 |
| 5 | CLI 工具 | 1.5h | P1 |
| 6 | 测试编写 | 1h | P1 |

**总计**: 7.5 小时

---

## 9. 依赖要求

```
# 可选依赖
boto3>=1.26.0        # S3 交付（可选）
typer>=0.9.0         # CLI 工具
rich>=13.0.0         # CLI 美化输出
```

---

> 设计完成，准备实现