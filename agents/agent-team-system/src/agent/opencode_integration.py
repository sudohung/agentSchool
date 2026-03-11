"""OpenCode 集成层."""

from __future__ import annotations

import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

# 导入 OpenCode SDK
import sys
opencode_path = Path(__file__).parent.parent.parent / "opencode-4-py" / "src"
sys.path.insert(0, str(opencode_path))

from opencode_4_py import OpenCodeClient
from opencode_4_py.models.session import Session


class OpenCodeIntegration:
    """
    OpenCode SDK 集成类
    
    为 Agent Team System 提供 OpenCode 服务集成
    """
    
    def __init__(self, base_url: str = "http://localhost:4096"):
        """
        初始化 OpenCode 集成
        
        Args:
            base_url: OpenCode Server 地址
        """
        self.base_url = base_url
        self.client: Optional[OpenCodeClient] = None
        self.session: Optional[Session] = None
    
    async def connect(self) -> bool:
        """
        连接到 OpenCode Server
        
        Returns:
            是否成功连接
        """
        try:
            self.client = OpenCodeClient(
                base_url=self.base_url,
            )
            
            # 健康检查
            health = self.client.health_check()
            print(f"✅ 已连接到 OpenCode Server v{health.version}")
            
            return True
        except Exception as e:
            print(f"❌ 连接失败：{e}")
            return False
    
    async def create_session(self, title: str) -> Optional[Session]:
        """
        创建团队会话
        
        Args:
            title: 会话标题
            
        Returns:
            创建的会话
        """
        if not self.client:
            await self.connect()
        
        if not self.client:
            return None
        
        self.session = self.client.session.create(title=title)
        print(f"✅ 已创建会话：{self.session.id}")
        return self.session
    
    async def send_message(
        self,
        agent_role: str,
        text: str,
        session_id: Optional[str] = None,
    ) -> Optional[Any]:
        """
        发送消息获取 AI 响应
        
        Args:
            agent_role: Agent 角色
            text: 消息内容
            session_id: 会话 ID (可选)
            
        Returns:
            AI 响应
        """
        if not self.client:
            return None
        
        sid = session_id or (self.session.id if self.session else None)
        if not sid:
            print("❌ 没有可用会话")
            return None
        
        try:
            result = self.client.message.send_text(
                session_id=sid,
                text=text,
                agent=agent_role,
            )
            return result
        except Exception as e:
            print(f"❌ 发送消息失败：{e}")
            return None
    
    async def read_file(self, path: str) -> Optional[str]:
        """
        读取文件
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容
        """
        if not self.client:
            return None
        
        try:
            content = self.client.file.read(path=path)
            return content.content
        except Exception as e:
            print(f"❌ 读取文件失败：{e}")
            return None
    
    async def write_file(self, path: str, content: str) -> bool:
        """
        写入文件
        
        Args:
            path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        if not self.client:
            return False
        
        try:
            # 通过消息间接写入
            await self.send_message(
                agent_role="System",
                text=f"Save this content to {path}:\n\n{content}",
            )
            return True
        except Exception as e:
            print(f"❌ 写入文件失败：{e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            print("✅ 已断开连接")


class TeamRunner:
    """
    团队运行器
    
    协调多个 Agent 执行 Ralph Loop
    """
    
    def __init__(
        self,
        agents: List[Any],
        opencode: Optional[OpenCodeIntegration] = None,
    ):
        """
        初始化团队运行器
        
        Args:
            agents: Agent 列表
            opencode: OpenCode 集成实例
        """
        self.agents = agents
        self.opencode = opencode or OpenCodeIntegration()
        self.document_hub = None
        self.request_board = None
        self.loop_controller = None
    
    async def initialize(self):
        """初始化团队"""
        # 1. 连接 OpenCode
        await self.opencode.connect()
        
        # 2. 创建会话
        await self.opencode.create_session("Agent Team Session")
        
        # 3. 初始化文档中心和诉求看板
        from document_hub.store import DocumentStore
        from request_board.board import RequestBoard
        from ralph_loop.controller import IterationController
        
        self.document_hub = DocumentStore()
        self.request_board = RequestBoard()
        self.loop_controller = IterationController()
        
        # 4. 注入依赖到所有 Agent
        for agent in self.agents:
            agent.document_hub = self.document_hub
            agent.request_board = self.request_board
            agent.client = self.opencode.client
            agent.session = self.opencode.session
        
        print(f"✅ 团队初始化完成，{len(self.agents)} 个 Agent 就绪")
    
    async def run(self, max_iterations: int = 50):
        """
        运行团队
        
        Args:
            max_iterations: 最大迭代次数
        """
        if not self.opencode.session:
            await self.initialize()
        
        print(f"🚀 开始执行，最大迭代次数：{max_iterations}")
        
        # 启动 Ralph Loop
        await self.loop_controller.start(self.agents, self.opencode.session)
        
        for i in range(max_iterations):
            print(f"\n=== Iteration {i+1}/{max_iterations} ===")
            
            # 并行执行所有 Agent
            tasks = [agent.execute_ralph_loop() for agent in self.agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for agent, result in zip(self.agents, results):
                if isinstance(result, Exception):
                    print(f"  ❌ {agent.role}: {str(result)[:50]}")
                else:
                    docs = result.get("documents_produced")
                    if docs:
                        print(f"  ✅ {agent.role}: 产出 {len([docs])} 个文档")
            
            # 检查完成度
            if await self._check_completion():
                print("✅ 完成度达标，结束迭代")
                break
        
        # 停止
        await self.loop_controller.stop()
        print("✅ 团队执行完成")
        
        # 生成最终报告
        await self._generate_final_report()
    
    async def _check_completion(self) -> bool:
        """检查完成度"""
        # 简化实现：检查是否有足够的文档产出
        if self.document_hub:
            docs = await self.document_hub.list_documents(limit=100)
            return len(docs) >= 10  # 至少 10 个文档
        return False
    
    async def _generate_final_report(self):
        """生成最终报告"""
        if not self.opencode.session:
            return
        
        # 收集所有产出
        docs = await self.document_hub.list_documents(limit=100) if self.document_hub else []
        
        report = f"""# 团队执行报告

## 参与 Agent
{chr(10).join(f'- {agent.role}' for agent in self.agents)}

## 产出文档
{chr(10).join(f'- {doc.metadata.title}' for doc in docs)}

## 会话 ID
{self.opencode.session.id}
"""
        
        # 保存报告
        from agent.config import Document, DocumentMetadata, DocumentContent, DocumentType
        import time
        
        final_doc = Document(
            id="final_report",
            path="reports/final_report.md",
            metadata=DocumentMetadata(
                title="团队执行报告",
                doc_type=DocumentType.OTHER,
                author="Team Runner",
                created_at=int(time.time()),
                updated_at=int(time.time()),
                version=1,
                tags=["报告", "总结"],
            ),
            content=DocumentContent(content=report),
        )
        
        await self.document_hub.save(final_doc)
        print(f"✅ 已生成最终报告：{final_doc.path}")
    
    async def close(self):
        """关闭团队"""
        await self.opencode.disconnect()
        print("✅ 团队已关闭")
