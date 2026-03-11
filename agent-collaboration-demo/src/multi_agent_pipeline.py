#!/usr/bin/env python3
"""
多Agent协作系统 - 协调者+子Agent架构
基于8角色框架实现完整的软件开发流程
"""
import asyncio
import os
import logging
import argparse
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# OpenCode 集成
try:
    from opencode_integration import OpenCodeClient, get_opencode_client, close_opencode_client
    OPENCODE_AVAILABLE = True
except ImportError:
    OPENCODE_AVAILABLE = False
    print("[Warning] OpenCode SDK 未安装，将使用本地执行")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== 配置 ==============
DASHSCOPE_API_KEY = "sk-sp-de6e887faf1f49acbad120766050fdd9"
DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen3-coder-next"


# ============== 状态管理 ==============

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ApprovalGate:
    """人工审批门 - 支持暂停等待人工审核"""
    
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.approvals = {}
    
    def request_approval(self, stage: Stage, output: str) -> ApprovalStatus:
        """请求审批"""
        stage_name = stage.value
        
        print("\n" + "="*60)
        print(f"🔔 审批门: {stage_name}")
        print("="*60)
        print(f"输出预览 (前500字符):\n{output[:500]}...")
        print("="*60)
        
        if self.auto_approve:
            print(f"✅ 自动批准: {stage_name}")
            status = ApprovalStatus.APPROVED
        else:
            print(f"\n请选择操作:")
            print("  [a] 批准 (approve)")
            print("  [r] 拒绝 (reject) - 需要修改后重新提交")
            print("  [s] 跳过 (skip) - 跳过此阶段")
            print("  [v] 查看完整输出 (view)")
            print("  [q] 退出 (quit)")
            
            status = self._get_approval_input(stage_name)
        
        self.approvals[stage_name] = status
        return status
    
    def _get_approval_input(self, stage_name: str) -> ApprovalStatus:
        """获取审批输入"""
        while True:
            try:
                choice = input(f"\n> 选择 [{stage_name}]: ").strip().lower()
                
                if choice == "a":
                    return ApprovalStatus.APPROVED
                elif choice == "r":
                    reason = input("拒绝原因: ").strip()
                    print(f"❌ 已拒绝: {stage_name}, 原因: {reason}")
                    return ApprovalStatus.REJECTED
                elif choice == "s":
                    return ApprovalStatus.SKIPPED
                elif choice == "v":
                    continue
                elif choice == "q":
                    print("用户退出")
                    raise KeyboardInterrupt()
                else:
                    print("无效选择，请重试")
            except EOFError:
                return ApprovalStatus.APPROVED
    
    def require_approval(self, stage: Stage, output: str, max_retries: int = 3) -> tuple[bool, str]:
        """需要审批，支持重试"""
        for attempt in range(max_retries):
            status = self.request_approval(stage, output)
            
            if status == ApprovalStatus.APPROVED:
                return True, "approved"
            elif status == ApprovalStatus.SKIPPED:
                return True, "skipped"
            else:
                print(f"🔄 重新提交 (尝试 {attempt + 1}/{max_retries})")
        
        return False, "max_retries_exceeded"


class StatePersistence:
    """状态持久化 - 保存/加载项目状态到JSON"""
    
    def __init__(self, state_dir: str = "./state"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    def _get_state_path(self, project_id: str) -> str:
        return os.path.join(self.state_dir, f"{project_id}.json")
    
    def save(self, context: 'TaskContext', approvals: dict = None) -> str:
        """保存项目状态"""
        state = {
            "project_id": context.project_id,
            "requirement": context.requirement,
            "design_doc": context.design_doc,
            "code_output": context.code_output,
            "test_result": context.test_result,
            "deploy_result": context.deploy_result,
            "issues_found": context.issues_found,
            "optimization_plan": context.optimization_plan,
            "current_stage": context.current_stage.value,
            "saved_at": datetime.now().isoformat(),
            "approvals": approvals or {}
        }
        
        path = self._get_state_path(context.project_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print(f"💾 状态已保存: {path}")
        return path
    
    def load(self, project_id: str) -> Optional['TaskContext']:
        """加载项目状态"""
        path = self._get_state_path(project_id)
        
        if not os.path.exists(path):
            print(f"⚠️  未找到项目状态: {project_id}")
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        context = TaskContext(
            project_id=state["project_id"],
            requirement=state.get("requirement", ""),
            design_doc=state.get("design_doc", ""),
            code_output=state.get("code_output", ""),
            test_result=state.get("test_result", ""),
            deploy_result=state.get("deploy_result", ""),
            issues_found=state.get("issues_found", []),
            optimization_plan=state.get("optimization_plan", ""),
            current_stage=Stage(state.get("current_stage", "requirement"))
        )
        
        print(f"📂 状态已加载: {path}")
        print(f"   恢复阶段: {context.current_stage.value}")
        return context
    
    def list_projects(self) -> list:
        """列出所有保存的项目"""
        projects = []
        for f in os.listdir(self.state_dir):
            if f.endswith(".json"):
                projects.append(f[:-5])
        return projects


class Stage(Enum):
    REQUIREMENT = "requirement"
    DESIGN = "design"
    CODE = "test"
    VALIDATION = "validation"
    DEPLOY = "deploy"


@dataclass
class TaskContext:
    """任务上下文 - 在Agent间共享"""
    project_id: str
    requirement: str = ""
    design_doc: str = ""
    code_output: str = ""
    test_result: str = ""
    deploy_result: str = ""
    issues_found: list = field(default_factory=list)
    optimization_plan: str = ""
    current_stage: Stage = Stage.REQUIREMENT
    
    def to_prompt(self) -> str:
        """转换为提示信息"""
        return f"""
当前项目: {self.project_id}
阶段: {self.current_stage.value}
需求: {self.requirement[:200]}...
设计: {self.design_doc[:200]}...
代码: {self.code_output[:200]}...
已发现问题: {len(self.issues_found)}个
"""


# ============== Agent工厂 ==============

def create_model_client():
    """创建模型客户端"""
    return OpenAIChatCompletionClient(
        model=MODEL,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        model_info={
            "name": MODEL,
            "family": "qwen",
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        }
    )


# ============== 8角色Agent定义 ==============

def create_coordinator_agent(model_client) -> AssistantAgent:
    """协调者Agent - 负责整体流程统筹和任务调度"""
    return AssistantAgent(
        name="ProjectCoordinator",
        model_client=model_client,
        system_message="""你是项目协调者，负责管理整个软件开发流程。

你的职责：
1. 任务分解 - 将项目分解为可管理的任务
2. 资源分配 - 协调各个子Agent的工作
3. 进度跟踪 - 监控任务完成状态
4. 问题升级 - 识别并处理阻塞问题
5. 质量控制 - 确保各阶段产出符合标准

工作流程：
1. 分析需求，创建任务列表
2. 调度不同Agent执行任务
3. 收集并整合各Agent的输出
4. 进行质量检查
5. 推进到下一阶段

请用中文回复，输出格式清晰。
"""
    )


def create_scanner_agent(model_client) -> AssistantAgent:
    """项目扫描器 - 快速建立项目全貌认知"""
    return AssistantAgent(
        name="ProjectScanner",
        model_client=model_client,
        system_message="""你是项目扫描器，负责快速了解项目现状。

你的任务：
1. 代码统计 - 文件数量、代码行数、语言分布
2. 依赖分析 - 识别主要依赖和版本
3. 热点识别 - 找出最常修改的文件
4. 风险评估 - 识别潜在风险区域

输出格式：
1. 项目概览（文件数、代码行数）
2. 技术栈（语言、框架、依赖）
3. 风险清单
4. 优化建议

请用简洁的中文输出。
"""
    )


def create_architecture_agent(model_client) -> AssistantAgent:
    """架构分析器 - 深入分析技术架构"""
    return AssistantAgent(
        name="ArchitectureAnalyzer",
        model_client=model_client,
        system_message="""你是架构分析器，负责深入分析系统架构。

你的任务：
1. 依赖树分析 - 理解模块间的依赖关系
2. 入口点识别 - 找到程序的主要入口
3. 分层结构分析 - 识别前端/后端/数据层
4. 技术债务识别 - 找出架构问题

输出格式：
1. 架构概览图（文字描述）
2. 模块依赖图
3. 技术债务清单
4. 改进建议

请用中文输出，包含具体文件路径。
"""
    )


def create_business_agent(model_client) -> AssistantAgent:
    """业务逻辑分析器 - 理解核心业务流程"""
    return AssistantAgent(
        name="BusinessLogicAnalyzer",
        model_client=model_client,
        system_message="""你是业务逻辑分析器，负责理解核心业务流程。

你的任务：
1. 调用链追踪 - 理解主要业务流程
2. 状态机分析 - 识别状态转换逻辑
3. 数据模型构建 - 理解核心数据结构
4. API分析 - 接口关系和契约

输出格式：
1. 业务流程图
2. 核心领域模型
3. API清单
4. 业务规则

请用中文输出。
"""
    )


def create_issue_agent(model_client) -> AssistantAgent:
    """问题识别器 - 系统化识别各类问题"""
    return AssistantAgent(
        name="IssueIdentifier",
        model_client=model_client,
        system_message="""你是问题识别器，负责系统化识别代码问题。

你的任务：
1. 代码异味检测 - 找出不良代码模式
2. 性能问题识别 - 找出性能瓶颈
3. 安全漏洞扫描 - 识别安全隐患
4. 代码规范检查 - 找出不符合规范的地方

输出格式：
1. 问题清单（按严重程度排序）
2. 问题位置（文件:行号）
3. 修复建议
4. 优先级矩阵

请用中文输出，每个问题都要具体。
"""
    )


def create_refactoring_agent(model_client) -> AssistantAgent:
    """重构专家 - 负责代码重构优化"""
    return AssistantAgent(
        name="RefactoringSpecialist",
        model_client=model_client,
        system_message="""你是重构专家，负责代码质量优化。

你的任务：
1. 重构方案设计 - 提出具体的重构计划
2. 代码修改实施 - 执行代码重构
3. 保持功能不变 - 确保重构后功能一致
4. 小步验证 - 每次修改后验证

工作模式：
- 分析 → 设计 → 实现 → 自验证（闭环）

输出格式：
1. 重构方案
2. 变更清单
3. 验证结果

请用中文输出，包含具体的代码变更。
"""
    )


def create_optimizer_agent(model_client) -> AssistantAgent:
    """性能优化专家 - 负责性能优化"""
    return AssistantAgent(
        name="PerformanceOptimizer",
        model_client=model_client,
        system_message="""你是性能优化专家，负责性能提升。

你的任务：
1. 性能分析定位 - 找出性能瓶颈
2. 优化方案设计 - 提出具体的优化计划
3. 优化实施 - 执行性能优化
4. 基准测试 - 验证优化效果

工作模式：
- 分析 → 设计 → 实现 → 测量（闭环）

输出格式：
1. 性能分析报告
2. 优化方案
3. 优化前后对比

请用中文输出，包含具体数据。
"""
    )


def create_tester_agent(model_client) -> AssistantAgent:
    """测试代理 - 负责测试验证"""
    return AssistantAgent(
        name="TestingAgent",
        model_client=model_client,
        system_message="""你是测试工程师，负责验证代码质量。

你的任务：
1. 测试用例生成 - 设计覆盖各场景的测试
2. 自动化测试执行 - 运行测试并收集结果
3. 回归测试 - 确保修改没有破坏现有功能
4. 覆盖率分析 - 评估测试覆盖率

输出格式：
1. 测试计划
2. 测试用例列表
3. 测试结果
4. 覆盖率报告

请用中文输出。
"""
    )


# ============== 协调者逻辑 ==============

class ProjectCoordinator:
    """项目协调者 - 管理整个开发流程"""
    
    def __init__(self, model_client, auto_approve: bool = False, 
                 state_dir: str = "./state", save_state: bool = True,
                 use_opencode: bool = True):
        self.model_client = model_client
        self.context = None
        self.approval_gate = ApprovalGate(auto_approve=auto_approve)
        self.state_persistence = StatePersistence(state_dir) if save_state else None
        self.save_state = save_state
        
        # OpenCode 客户端
        self.use_opencode = use_opencode and OPENCODE_AVAILABLE
        self.opencode_client: Optional[object] = None  # OpenCodeClient 实例
        
        # 创建8角色Agent
        self.coordinator = create_coordinator_agent(model_client)
        self.scanner = create_scanner_agent(model_client)
        self.architect = create_architecture_agent(model_client)
        self.business = create_business_agent(model_client)
        self.issue_id = create_issue_agent(model_client)
        self.refactorer = create_refactoring_agent(model_client)
        self.optimizer = create_optimizer_agent(model_client)
        self.tester = create_tester_agent(model_client)
        
        # 角色映射到阶段
        self.role_stage_map = {
            "requirement": [self.coordinator, self.business],
            "design": [self.architect, self.business],
            "code": [self.scanner, self.architect, self.issue_id, self.refactorer, self.optimizer],
            "validation": [self.tester, self.issue_id],
            "deploy": [self.coordinator],
        }
    
    async def analyze_requirement(self, requirement: str) -> str:
        """需求分析阶段"""
        print("\n" + "="*50)
        print("阶段1: 需求分析")
        print("="*50)
        
        # 协调者分析需求
        coord_result = await self.coordinator.run(
            task=f"分析以下需求，分解为具体任务:\n{requirement}"
        )
        
        # 业务逻辑分析
        business_result = await self.business.run(
            task=f"理解业务逻辑，识别核心功能:\n{requirement}"
        )
        
        result = f"=== 需求分析结果 ===\n{coord_result}\n\n=== 业务分析 ===\n{business_result}"
        self.context = TaskContext(
            project_id="project-001",
            requirement=requirement,
            current_stage=Stage.REQUIREMENT
        )
        return result
    
    async def init_opencode(self):
        """初始化 OpenCode 客户端"""
        if self.use_opencode and OPENCODE_AVAILABLE:
            try:
                from opencode_integration import OpenCodeClient
                self.opencode_client = OpenCodeClient()
                await self.opencode_client.connect()
                print("✅ OpenCode 客户端已初始化")
            except Exception as e:
                print(f"⚠️ OpenCode 初始化失败: {e}")
                self.use_opencode = False
                self.opencode_client = None
    
    async def design_architecture(self, requirement: str) -> str:
        """架构设计阶段"""
        print("\n" + "="*50)
        print("阶段2: 架构设计")
        print("="*50)
        
        # 架构分析
        arch_result = await self.architect.run(
            task=f"基于需求设计系统架构:\n{requirement}"
        )
        
        # 业务模型分析
        biz_result = await self.business.run(
            task=f"设计业务领域模型:\n{requirement}"
        )
        
        result = f"=== 架构设计 ===\n{arch_result}\n\n=== 业务模型 ===\n{biz_result}"
        self.context.design_doc = result
        self.context.current_stage = Stage.DESIGN
        return result
    
    async def implement_code(self, design: str) -> str:
        """代码实现阶段"""
        print("\n" + "="*50)
        print("阶段3: 代码实现")
        print("="*50)
        
        opencode_result = ""
        if self.use_opencode and self.opencode_client:
            print("\n🤖 使用 OpenCode 生成代码...")
            try:
                oc_result = await self.opencode_client.generate_and_execute(
                    requirement=self.context.requirement,
                    language="python"
                )
                opencode_result = f"""
=== OpenCode 生成代码 ===
{oc_result.get('code', '')[:1000]}

=== 执行结果 ===
{oc_result.get('execution', {}).get('stdout', '')[:500]}
"""
                print(f"✅ OpenCode 代码生成完成")
            except Exception as e:
                print(f"⚠️ OpenCode 执行失败: {e}")
                opencode_result = f"\n[OpenCode 失败: {e}]\n"
        
        # 项目扫描
        scan_result = await self.scanner.run(
            task="创建项目结构，生成代码框架"
        )
        
        # 架构师确认
        arch_check = await self.architect.run(
            task=f"基于设计生成代码:\n{design}"
        )
        
        # 问题识别
        issue_result = await self.issue_id.run(
            task=f"分析代码，识别潜在问题:\n{arch_check}"
        )
        
        # 重构优化
        refactor_result = await self.refactorer.run(
            task=f"重构代码，提升质量:\n{arch_check}"
        )
        
        result = f"=== 项目结构 ===\n{scan_result}\n\n=== OpenCode 生成 ===\n{opencode_result}\n\n=== 代码 ===\n{arch_check}\n\n=== 问题识别 ===\n{issue_result}\n\n=== 重构 ===\n{refactor_result}"
        self.context.code_output = result
        self.context.current_stage = Stage.CODE
        return result
    
    async def validate_code(self, code: str) -> str:
        """验证阶段"""
        print("\n" + "="*50)
        print("阶段4: 测试验证")
        print("="*50)
        
        # 测试执行
        test_result = await self.tester.run(
            task=f"设计并执行测试:\n{code}"
        )
        
        # 问题验证
        issue_check = await self.issue_id.run(
            task=f"验证修复效果:\n{test_result}"
        )
        
        result = f"=== 测试结果 ===\n{test_result}\n\n=== 验证 ===\n{issue_check}"
        self.context.test_result = result
        self.context.current_stage = Stage.VALIDATION
        return result
    
    async def deploy(self, validation: str) -> str:
        """部署阶段"""
        print("\n" + "="*50)
        print("阶段5: 部署发布")
        print("="*50)
        
        # 协调者制定部署计划
        deploy_result = await self.coordinator.run(
            task=f"基于验证结果制定部署计划:\n{validation}"
        )
        
        result = f"=== 部署计划 ===\n{deploy_result}"
        self.context.deploy_result = result
        self.context.current_stage = Stage.DEPLOY
        return result
    
    async def run_full_pipeline(self, requirement: str, use_approval_gates: bool = True) -> 'TaskContext':
        """运行完整Pipeline"""
        print("\n" + "="*60)
        print("开始执行8角色Agent协作开发流程")
        print(f"需求: {requirement[:100]}...")
        if use_approval_gates and not self.approval_gate.auto_approve:
            print("⚠️  审批门已启用 - 每个阶段需要人工审核")
        if self.use_opencode:
            print("🤖 OpenCode 已启用 - 将用于代码生成")
        print("="*60)
        
        # 初始化 OpenCode
        await self.init_opencode()
        
        # 阶段1: 需求分析
        await self.analyze_requirement(requirement)
        if self.save_state and self.state_persistence:
            self.state_persistence.save(self.context, self.approval_gate.approvals)
        
        if use_approval_gates:
            approved, _ = self.approval_gate.require_approval(
                Stage.REQUIREMENT, self.context.design_doc or self.context.requirement
            )
            if not approved:
                print("❌ 需求分析未通过审批，流程终止")
                return self.context
        
        # 阶段2: 架构设计
        design = await self.design_architecture(requirement)
        if self.save_state and self.state_persistence:
            self.state_persistence.save(self.context, self.approval_gate.approvals)
        
        if use_approval_gates:
            approved, _ = self.approval_gate.require_approval(Stage.DESIGN, design)
            if not approved:
                print("❌ 架构设计未通过审批，流程终止")
                return self.context
        
        # 阶段3: 代码实现
        code = await self.implement_code(design)
        if self.save_state and self.state_persistence:
            self.state_persistence.save(self.context, self.approval_gate.approvals)
        
        if use_approval_gates:
            approved, _ = self.approval_gate.require_approval(Stage.CODE, code)
            if not approved:
                print("❌ 代码实现未通过审批，流程终止")
                return self.context
        
        # 阶段4: 测试验证
        validation = await self.validate_code(code)
        if self.save_state and self.state_persistence:
            self.state_persistence.save(self.context, self.approval_gate.approvals)
        
        if use_approval_gates:
            approved, _ = self.approval_gate.require_approval(Stage.VALIDATION, validation)
            if not approved:
                print("❌ 测试验证未通过审批，流程终止")
                return self.context
        
        # 阶段5: 部署
        deploy = await self.deploy(validation)
        
        if use_approval_gates:
            self.approval_gate.request_approval(Stage.DEPLOY, deploy)
        
        # 最终保存
        if self.save_state and self.state_persistence:
            self.state_persistence.save(self.context, self.approval_gate.approvals)
        
        print("\n" + "="*60)
        print("✅ 完整Pipeline执行完成!")
        print("="*60)
        
        return self.context


# ============== 主入口 ==============

async def main():
    parser = argparse.ArgumentParser(description="多Agent协作开发系统")
    parser.add_argument("--auto-approve", "-a", action="store_true", 
                        help="自动批准所有阶段，跳过人工审核")
    parser.add_argument("--no-gates", action="store_true", 
                        help="禁用审批门，直接执行")
    parser.add_argument("--requirement", "-r", type=str, default=None,
                        help="自定义需求文本")
    parser.add_argument("--load", "-l", type=str, default=None, metavar="PROJECT_ID",
                        help="加载已有项目状态继续执行")
    parser.add_argument("--no-save", action="store_true", 
                        help="禁用状态保存")
    parser.add_argument("--state-dir", type=str, default="./state",
                        help="状态保存目录 (默认: ./state)")
    parser.add_argument("--list", action="store_true",
                        help="列出所有保存的项目")
    parser.add_argument("--no-opencode", action="store_true",
                        help="禁用 OpenCode，使用本地执行")
    args = parser.parse_args()
    
    # 列出项目
    if args.list:
        persistence = StatePersistence(args.state_dir)
        projects = persistence.list_projects()
        print("已保存的项目:")
        for p in projects:
            print(f"  - {p}")
        return
    
    # 加载项目
    if args.load:
        persistence = StatePersistence(args.state_dir)
        context = persistence.load(args.load)
        if not context:
            return
        print(f"已恢复项目: {context.project_id}, 阶段: {context.current_stage.value}")
    
    model_client = create_model_client()
    
    auto_approve = args.auto_approve or args.no_gates
    use_gates = not args.no_gates
    save_state = not args.no_save
    use_opencode = not args.no_opencode
    
    coordinator = ProjectCoordinator(
        model_client, 
        auto_approve=auto_approve,
        state_dir=args.state_dir,
        save_state=save_state,
        use_opencode=use_opencode
    )
    
    if args.load:
        coordinator.context = context
    
    if args.requirement:
        requirement = args.requirement
    else:
        requirement = """
    开发一个简单的任务管理Web应用
    - 用户可以创建、编辑、删除任务
    - 任务有标题、描述、截止日期、状态
    - 支持任务分类/标签
    - 使用简单的文件存储
    """
    
    context = await coordinator.run_full_pipeline(requirement, use_approval_gates=use_gates)
    
    print("\n========== 项目完成摘要 ==========")
    print(f"项目ID: {context.project_id}")
    print(f"最终阶段: {context.current_stage.value}")
    print(f"已识别问题数: {len(context.issues_found)}")
    print(f"审批记录: {list(coordinator.approval_gate.approvals.keys())}")
    print("="*40)
    
    await model_client.close()


if __name__ == "__main__":
    print(f"使用模型: {MODEL}")
    print(f"API端点: {DASHSCOPE_BASE_URL}")
    print()
    print("用法:")
    print("  python multi_agent_pipeline.py              # 交互模式，每个阶段需要审批")
    print("  python multi_agent_pipeline.py -a           # 自动批准所有阶段")
    print("  python multi_agent_pipeline.py --no-gates  # 完全禁用审批门")
    print("  python multi_agent_pipeline.py -r '需求'    # 自定义需求")
    print("  python multi_agent_pipeline.py --list      # 列出已保存的项目")
    print("  python multi_agent_pipeline.py -l project-001  # 加载项目继续执行")
    print("  python multi_agent_pipeline.py --no-opencode # 禁用 OpenCode")
    print()
    asyncio.run(main())
