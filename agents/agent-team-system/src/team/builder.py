"""团队构建器."""

from __future__ import annotations

import asyncio
import time
import hashlib
from typing import Optional, Any, List
from dataclasses import dataclass

from .config import TaskAnalysis, TeamConfig, TeamContext
from .analyzer import TaskAnalyzer
from .mapper import RoleMapper
from .factory import AgentFactory

# 使用正确的类名
from document_hub import DocumentStore
from request_board import RequestBoard


@dataclass
class BuildResult:
    """构建结果"""
    success: bool
    team: List[Any]
    analysis: Optional[TaskAnalysis]
    context: Optional[TeamContext] = None
    error: Optional[str] = None


class TeamBuilder:
    """
    团队构建器
    
    主入口：根据任务描述构建 Agent 团队
    
    使用示例:
        builder = TeamBuilder(client)
        result = await builder.build("开发电商网站")
        if result.success:
            print(f"团队：{[a.role for a in result.team]}")
    """
    
    def __init__(
        self, 
        client=None,
        config: Optional[TeamConfig] = None,
        storage_path: Optional[str] = None,
    ):
        """
        初始化构建器
        
        Args:
            client: OpenCode 客户端
            config: 团队配置
            storage_path: 文档存储路径
        """
        self.client = client
        self.config = config or TeamConfig()
        self.storage_path = storage_path or self.config.storage_base_path
        
        # 初始化组件
        self.analyzer = TaskAnalyzer(client, self.config)
        self.mapper = RoleMapper(self.config)
        
        # 共享组件 (延迟初始化)
        self._document_store = None
        self._request_board = None
        self._factory = None
        self._context = None
    
    @property
    def document_store(self) -> DocumentStore:
        """获取文档存储 (延迟初始化)"""
        if not self._document_store:
            self._document_store = DocumentStore(self.storage_path)
        return self._document_store
    
    @property
    def request_board(self) -> RequestBoard:
        """获取诉求看板 (延迟初始化)"""
        if not self._request_board:
            self._request_board = RequestBoard()
        return self._request_board
    
    @property
    def factory(self) -> AgentFactory:
        """获取工厂 (延迟初始化)"""
        if not self._factory:
            self._factory = AgentFactory(
                document_store=self.document_store,
                request_board=self.request_board,
                client=self.client,
            )
        return self._factory
    
    async def build(self, task_description: str) -> BuildResult:
        """
        构建团队
        
        Args:
            task_description: 用户任务描述
            
        Returns:
            BuildResult: 构建结果
            
        Example:
            >>> builder = TeamBuilder()
            >>> result = await builder.build("开发简单网站")
            >>> print(result.success)
            True
        """
        try:
            # 1. 需求分析
            analysis = await self.analyzer.analyze(task_description)
            
            # 2. 角色映射
            role_names = self.mapper.map(analysis)
            
            # 3. 创建 Agent
            agents = self.factory.create_agents(role_names)
            
            # 4. 创建团队上下文
            context = TeamContext(
                team_id=self._generate_id("team"),
                task_description=task_description,
                analysis=analysis,
                config=self.config,
                document_store=self.document_store,
                request_board=self.request_board,
                client=self.client,
                agents=agents,
            )
            
            # 5. 返回结果
            return BuildResult(
                success=True,
                team=agents,
                analysis=analysis,
                context=context,
            )
            
        except ValueError as e:
            # 详细的错误处理
            return BuildResult(
                success=False,
                team=[],
                analysis=None,
                error=f"角色映射错误：{e}",
            )
        except ImportError as e:
            return BuildResult(
                success=False,
                team=[],
                analysis=None,
                error=f"模块导入错误：{e}",
            )
        except Exception as e:
            return BuildResult(
                success=False,
                team=[],
                analysis=None,
                error=f"未知错误：{e}",
            )
    
    def _generate_id(self, prefix: str) -> str:
        """生成 ID"""
        timestamp = int(time.time() * 1000)
        data = f"{prefix}:{timestamp}"
        return f"{prefix}_{hashlib.md5(data.encode()).hexdigest()[:12]}"
