"""产品整合器 - 整合所有 Agent 产出."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from document_hub.store import DocumentStore
from document_hub.models import Document, DocumentType
from request_board.board import RequestBoard


@dataclass
class DeliveryPackage:
    """交付包"""
    
    project_name: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    
    # 文档
    documents: List[Document] = field(default_factory=list)
    
    # 代码
    source_code: Dict[str, str] = field(default_factory=dict)  # path -> content
    
    # 测试
    test_cases: List[Document] = field(default_factory=list)
    test_reports: List[Document] = field(default_factory=list)
    
    # 部署配置
    deployment_configs: Dict[str, str] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 交付清单
    manifest: Optional[str] = None
    
    @property
    def total_documents(self) -> int:
        """文档总数"""
        return len(self.documents)
    
    @property
    def total_code_files(self) -> int:
        """代码文件数"""
        return len(self.source_code)
    
    @property
    def total_tests(self) -> int:
        """测试文件数"""
        return len(self.test_cases) + len(self.test_reports)


class ProductIntegrator:
    """
    产品整合器
    
    负责收集所有 Agent 的产出，整合为完整的交付包
    """
    
    def __init__(self, document_store: DocumentStore, request_board: RequestBoard):
        """
        初始化产品整合器
        
        Args:
            document_store: 文档存储
            request_board: 诉求看板
        """
        self.document_store = document_store
        self.request_board = request_board
    
    async def integrate(
        self,
        project_name: str,
        workflow_context: Any,
    ) -> DeliveryPackage:
        """
        整合产品
        
        Args:
            project_name: 项目名称
            workflow_context: 工作流上下文
            
        Returns:
            交付包
        """
        package = DeliveryPackage(project_name=project_name)
        
        # 1. 收集所有文档
        package.documents = await self._collect_documents()
        
        # 2. 收集代码
        package.source_code = await self._collect_source_code()
        
        # 3. 收集测试
        package.test_cases, package.test_reports = await self._collect_tests()
        
        # 4. 收集部署配置
        package.deployment_configs = await self._collect_deployment_configs()
        
        # 5. 生成元数据
        package.metadata = await self._generate_metadata(workflow_context)
        
        # 6. 生成交付清单
        if workflow_context and hasattr(workflow_context, 'team'):
            package.manifest = await self._generate_manifest(package, workflow_context.team)
        
        return package
    
    async def _collect_documents(self) -> List[Document]:
        """收集所有文档"""
        all_docs = await self.document_store.list_documents(limit=1000)
        
        # 排除代码和测试文档（单独收集）
        excluded_types = [
            DocumentType.CODE.value if hasattr(DocumentType, 'value') else 'code',
            DocumentType.TEST_CASE.value if hasattr(DocumentType, 'value') else 'test_case',
        ]
        
        return [
            doc for doc in all_docs
            if getattr(doc.metadata, 'doc_type', None) not in excluded_types
        ]
    
    async def _collect_source_code(self) -> Dict[str, str]:
        """收集源代码"""
        code_docs = await self.document_store.list_documents(
            doc_type="code" if hasattr(DocumentType, 'CODE') else None,
            limit=1000,
        )
        
        source_code = {}
        for doc in code_docs:
            path = getattr(doc, 'path', f'code/{doc.id}')
            content = getattr(doc.content, 'content', '') if hasattr(doc, 'content') else ''
            source_code[path] = content
        
        return source_code
    
    async def _collect_tests(self) -> tuple[List[Document], List[Document]]:
        """收集测试用例和报告"""
        all_docs = await self.document_store.list_documents(limit=1000)
        
        test_cases = []
        test_reports = []
        
        for doc in all_docs:
            doc_type = getattr(doc.metadata, 'doc_type', '')
            title = getattr(doc.metadata, 'title', '').lower()
            
            if 'test' in doc_type.lower() or 'test' in title:
                if 'report' in title:
                    test_reports.append(doc)
                else:
                    test_cases.append(doc)
        
        return test_cases, test_reports
    
    async def _collect_deployment_configs(self) -> Dict[str, str]:
        """收集部署配置"""
        # 查找部署相关文档
        all_docs = await self.document_store.list_documents(limit=1000)
        
        configs = {}
        for doc in all_docs:
            path = getattr(doc, 'path', '')
            if any(keyword in path.lower() for keyword in ['docker', 'deploy', 'config', 'yaml', 'yml']):
                content = getattr(doc.content, 'content', '') if hasattr(doc, 'content') else ''
                configs[path] = content
        
        return configs
    
    async def _generate_metadata(self, workflow_context: Any) -> Dict[str, Any]:
        """生成元数据"""
        metadata = {
            "created_at": int(time.time()),
            "document_count": 0,
            "code_file_count": 0,
            "test_count": 0,
        }
        
        if workflow_context:
            metadata["workflow_id"] = getattr(workflow_context, 'workflow_id', 'unknown')
            metadata["iteration_count"] = getattr(workflow_context, 'iteration_count', 0)
            metadata["quality_score"] = getattr(workflow_context, 'quality_score', 0.0)
        
        return metadata
    
    async def _generate_manifest(self, package: DeliveryPackage, team: List) -> str:
        """生成交付清单"""
        team_list = "\n".join([f"- {getattr(agent, 'role', 'Unknown')}" for agent in team])
        
        doc_list = "\n".join([
            f"- [x] {getattr(doc.metadata, 'title', doc.id)}"
            for doc in package.documents
        ])
        
        code_list = "\n".join([f"- [x] {path}" for path in package.source_code.keys()])
        
        manifest = f"""# 交付清单

## 项目信息
- 项目名称：{package.project_name}
- 交付日期：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(package.created_at))}
- 团队组成:
{team_list}

## 交付内容

### 文档
{doc_list if doc_list else '- 无文档'}

### 代码
{code_list if code_list else '- 无代码'}

### 测试
- 测试用例：{len(package.test_cases)} 个
- 测试报告：{len(package.test_reports)} 个

### 部署配置
{chr(10).join(f'- [x] {path}' for path in package.deployment_configs.keys()) if package.deployment_configs else '- 无部署配置'}

## 统计信息
- 文档总数：{package.total_documents}
- 代码文件：{package.total_code_files}
- 测试文件：{package.total_tests}

## 质量指标
- 工作流 ID: {package.metadata.get('workflow_id', 'N/A')}
- 迭代次数：{package.metadata.get('iteration_count', 0)}
- 质量分数：{package.metadata.get('quality_score', 0.0):.2f}

---
*此清单由 Agent Team System 自动生成*
"""
        return manifest
