"""Agent 基类."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from .config import AgentConfig, AgentStatus, Document, Request
from .state import AgentStateMachine, AgentState
from .permissions import (
    PermissionType,
    PermissionAction,
    PermissionRequest,
    QuestionOption,
    QuestionResponse,
)
from .handler import PermissionQuestionHandler
from .memory import AgentMemory


class Agent(ABC):
    """
    Agent 基类
    
    所有 Agent 角色都继承自这个基类
    实现 Ralph Loop 的核心能力
    """
    
    def __init__(
        self,
        role: str,
        expertise: List[str],
        session: Any = None,
        client: Any = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        初始化 Agent
        
        Args:
            role: 角色名称
            expertise: 专业技能列表
            session: OpenCode 会话
            client: OpenCode 客户端
            config: Agent 配置
        """
        self.role = role
        self.expertise = expertise
        self.session = session
        self.client = client
        self.config = config or AgentConfig(role=role, expertise=expertise)
        
        # 状态管理
        self.status = AgentStatus.IDLE
        self.state_machine = AgentStateMachine()
        
        # 记忆系统
        self.memory = AgentMemory()
        
        # 权限/问题处理器
        self.handler = PermissionQuestionHandler()
        
        # 文档中心和诉求看板 (由外部注入)
        self.document_hub = None
        self.request_board = None
    
    # ========== Ralph Loop 核心能力 ==========
    
    @abstractmethod
    async def read_documents(self) -> List[Document]:
        """
        R - Read: 阅读共享文档中心的最新文档
        
        返回：相关文档列表
        """
        pass
    
    @abstractmethod
    async def act_on_requests(self) -> List[Request]:
        """
        A - Act: 响应其他 Agent 的诉求
        
        返回：已处理的诉求列表
        """
        pass
    
    @abstractmethod
    async def leverage_expertise(self) -> Any:
        """
        L - Leverage: 发挥专业能力执行工作
        
        返回：工作结果
        """
        pass
    
    @abstractmethod
    async def produce_document(self, work_result: Any) -> Document:
        """
        P - Produce: 产出文档作为工作成果
        
        返回：新文档
        """
        pass
    
    @abstractmethod
    async def help_requests(self) -> List[Request]:
        """
        H - Help: 发布诉求寻求其他 Agent 协作
        
        返回：新诉求列表
        """
        pass
    
    # ========== 权限/问题处理能力 ==========
    
    async def request_permission(
        self,
        type: PermissionType,
        resource: str,
        description: str,
        remember: bool = False,
    ) -> PermissionAction:
        """
        请求权限
        
        Args:
            type: 权限类型
            resource: 资源 (文件路径/命令等)
            description: 描述
            remember: 是否记住选择
            
        Returns:
            PermissionAction: ALLOW/DENY/ASK
        """
        request = PermissionRequest(
            id=self._generate_id("perm"),
            type=type,
            resource=resource,
            description=description,
            requested_by=self.role,
            action=PermissionAction.ASK,
            remember=remember,
        )
        
        response = await self.handler.handle_permission(request)
        
        if response.remember:
            cache_key = f"{type.value}:{resource}"
            self.handler.permission_cache[cache_key] = response.action
        
        return response.action
    
    async def ask_question(
        self,
        question: str,
        header: str,
        options: List[QuestionOption],
        multiple: bool = False,
        custom: bool = True,
    ) -> Optional[QuestionResponse]:
        """
        提出问题
        
        Args:
            question: 完整问题
            header: 简短标题
            options: 选项列表
            multiple: 是否多选
            custom: 是否允许自定义答案
            
        Returns:
            QuestionResponse 或 None (需要用户回答)
        """
        from .permissions import QuestionRequest
        
        request = QuestionRequest(
            id=self._generate_id("ques"),
            question=question,
            header=header,
            options=options,
            multiple=multiple,
            custom=custom,
            requested_by=self.role,
        )
        
        return await self.handler.handle_question(request)
    
    # ========== 便捷权限方法 ==========
    
    async def can_read_file(self, path: str) -> bool:
        """检查是否可以读取文件"""
        action = await self.request_permission(
            type=PermissionType.FILE_READ,
            resource=path,
            description=f"读取文件：{path}",
        )
        return action == PermissionAction.ALLOW
    
    async def can_write_file(self, path: str) -> bool:
        """检查是否可以写入文件"""
        action = await self.request_permission(
            type=PermissionType.FILE_WRITE,
            resource=path,
            description=f"写入文件：{path}",
        )
        return action == PermissionAction.ALLOW
    
    async def can_execute_command(self, command: str) -> bool:
        """检查是否可以执行命令"""
        action = await self.request_permission(
            type=PermissionType.COMMAND_EXECUTE,
            resource=command,
            description=f"执行命令：{command}",
        )
        return action == PermissionAction.ALLOW
    
    # ========== 工具方法 ==========
    
    async def send_message(self, text: str) -> Any:
        """通过 OpenCode SDK 发送消息获取 AI 响应"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        result = await self.client.message.send_text(
            session_id=self.session.id,
            text=text,
            agent=self.role,
        )
        return result
    
    def update_status(self, status: AgentStatus):
        """更新 Agent 状态"""
        self.status = status
        
        # 更新状态机
        state_map = {
            AgentStatus.IDLE: AgentState.IDLE,
            AgentStatus.WORKING: AgentState.WORKING,
            AgentStatus.WAITING: AgentState.WAITING,
            AgentStatus.BLOCKED: AgentState.BLOCKED,
            AgentStatus.DONE: AgentState.DONE,
        }
        
        target_state = state_map.get(status)
        if target_state:
            self.state_machine.transition_to(target_state, str(status))
    
    def add_to_memory(self, key: str, value: Any, scope: str = "short"):
        """添加到记忆"""
        self.memory.add(key, value, scope)
    
    def get_from_memory(self, key: str, scope: str = "short") -> Optional[Any]:
        """从记忆获取"""
        return self.memory.get(key, scope)
    
    def _generate_id(self, prefix: str) -> str:
        """生成 ID"""
        import hashlib
        timestamp = int(time.time() * 1000)
        data = f"{prefix}:{timestamp}"
        return f"{prefix}_{hashlib.md5(data.encode()).hexdigest()[:12]}"
    
    async def execute_ralph_loop(self) -> Dict[str, Any]:
        """
        执行完整的 Ralph Loop
        
        Returns:
            执行结果
        """
        result = {
            "documents_read": [],
            "requests_processed": [],
            "work_result": None,
            "document_produced": None,
            "requests_posted": [],
            "setbacks": [],
        }
        
        try:
            # 更新状态为工作中
            self.update_status(AgentStatus.WORKING)
            
            # R - Read
            result["documents_read"] = await self.read_documents()
            
            # A - Act
            result["requests_processed"] = await self.act_on_requests()
            
            # L - Leverage
            result["work_result"] = await self.leverage_expertise()
            
            # P - Produce
            if result["work_result"]:
                result["document_produced"] = await self.produce_document(
                    result["work_result"]
                )
            
            # H - Help
            result["requests_posted"] = await self.help_requests()
            
            # 更新状态为完成
            self.update_status(AgentStatus.DONE)
        
        except Exception as e:
            result["setbacks"].append({
                "type": "execution_error",
                "error": str(e),
                "timestamp": int(time.time()),
            })
            self.update_status(AgentStatus.BLOCKED)
        
        return result
