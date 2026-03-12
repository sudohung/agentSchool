"""Agent 角色实现 - 使用 MD 定义文件加载."""

from __future__ import annotations

import time
from typing import List, Any
from agent.base import Agent
from agent.config import Document, DocumentType, DocumentMetadata, DocumentContent, Request, RequestType, RequestPriority, RequestStatus
from agent.roles.loader import get_agent_definition, AgentDefinition


def _create_agent_from_definition(role_name: str, session=None, client=None) -> Agent:
    """从定义创建 Agent"""
    definition = get_agent_definition(role_name)
    
    class DynamicAgent(Agent):
        def __init__(self, session=None, client=None):
            super().__init__(
                role=definition.role,
                expertise=definition.expertise,
                session=session,
                client=client,
            )
            self._definition = definition
        
        async def read_documents(self) -> List[Document]:
            return []
        
        async def act_on_requests(self) -> List[Request]:
            return []
        
        async def leverage_expertise(self) -> Any:
            prompt = self._definition.ralph_loop.leverage_prompt
            if prompt and self.client and self.session:
                return await self.send_message(prompt)
            return f"{self.role} 执行任务"
        
        async def produce_document(self, work_result: Any) -> Document:
            template = self._definition.ralph_loop.produce_template
            content = template.replace("{work_result}", str(work_result))
            
            doc_type_map = {
                "CODE": DocumentType.CODE,
                "DESIGN": DocumentType.DESIGN,
                "API_DOC": DocumentType.API_DOC,
                "TEST_CASE": DocumentType.TEST_CASE,
                "USER_MANUAL": DocumentType.USER_MANUAL,
                "OTHER": DocumentType.OTHER,
                "PRD": DocumentType.PRD,
                "ARCHITECTURE": DocumentType.ARCHITECTURE,
            }
            doc_type = doc_type_map.get(
                self._definition.ralph_loop.produce_doc_type.upper(),
                DocumentType.OTHER
            )
            
            return Document(
                id=self._generate_id(self.role.lower().replace(" ", "_")[:2]),
                path=self._definition.ralph_loop.produce_path,
                metadata=DocumentMetadata(
                    title=self._definition.role,
                    doc_type=doc_type,
                    author=self.role,
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                    version=1,
                    tags=self._definition.ralph_loop.produce_tags,
                ),
                content=DocumentContent(
                    content=content,
                    format="markdown",
                ),
            )
        
        async def help_requests(self) -> List[Request]:
            requests_list = []
            for req in self._definition.ralph_loop.help_requests:
                priority_map = {
                    "HIGH": RequestPriority.HIGH,
                    "NORMAL": RequestPriority.NORMAL,
                    "LOW": RequestPriority.LOW,
                }
                requests_list.append(Request(
                    id=self._generate_id("req"),
                    type=RequestType.COLLABORATION,
                    priority=priority_map.get(req.get("priority", "NORMAL"), RequestPriority.NORMAL),
                    from_agent=self.role,
                    to_agent=req.get("to", ""),
                    subject=req.get("subject", ""),
                    content=req.get("content", ""),
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                ))
            return requests_list
    
    return DynamicAgent(session, client)


def FrontendDeveloperAgent(session=None, client=None):
    """前端开发 Agent"""
    return _create_agent_from_definition("Frontend Developer", session, client)


def BackendDeveloperAgent(session=None, client=None):
    """后端开发 Agent"""
    return _create_agent_from_definition("Backend Developer", session, client)


def FullStackDeveloperAgent(session=None, client=None):
    """全栈开发 Agent"""
    return _create_agent_from_definition("Full Stack Developer", session, client)


def QAAgent(session=None, client=None):
    """测试工程师 Agent"""
    return _create_agent_from_definition("QA Engineer", session, client)


def CodeReviewerAgent(session=None, client=None):
    """代码审查员 Agent"""
    return _create_agent_from_definition("Code Reviewer", session, client)


def DocWriterAgent(session=None, client=None):
    """文档工程师 Agent"""
    return _create_agent_from_definition("Doc Writer", session, client)


def DevOpsAgent(session=None, client=None):
    """运维工程师 Agent"""
    return _create_agent_from_definition("DevOps Engineer", session, client)


def SecurityAgent(session=None, client=None):
    """安全工程师 Agent"""
    return _create_agent_from_definition("Security Engineer", session, client)