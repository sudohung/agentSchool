# 文档中心 (Document Hub) 设计文档

> Agent Team System 核心组件设计
> 
> 版本：0.1.0
> 创建日期：2026-03-11
> 最后更新：2026-03-11

---

## 1. 概述

### 1.1 设计目标

构建一个**共享文档中心**，作为 Agent 团队协作的核心基础设施：

- ✅ 所有 Agent 通过文档进行协作
- ✅ 支持文档版本控制和历史追踪
- ✅ 提供文档更新通知机制
- ✅ 防止并发冲突 (文档锁)
- ✅ 与 OpenCode SDK 无缝集成

### 1.2 核心原则

| 原则 | 描述 |
|------|------|
| 📄 **单一事实源** | 所有文档有且只有一个权威版本 |
| 🔄 **版本控制** | 每次修改都有版本记录和 diff |
| 🔔 **通知驱动** | 文档更新自动通知相关 Agent |
| 🔒 **并发安全** | 文档锁防止并发写入冲突 |
| 📂 **分类管理** | 按文档类型组织存储 |

### 1.3 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Document Hub                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Document Store                      │   │
│  │              (文档存储层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  文件系统存储 │ 内存缓存 │ 索引服务             │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Version Control                     │   │
│  │              (版本控制层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  版本历史 │ Diff 计算 │ 版本回滚 │ 分支管理      │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Notification Service                │   │
│  │              (通知服务层)                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  订阅/发布 │ 事件队列 │ 批量通知 │ 过滤规则     │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              Lock Manager                        │   │
│  │              (锁管理器)                           │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  文档锁 │ 锁超时 │ 锁竞争处理 │ 死锁检测        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 文档模型设计

### 2.1 文档类型枚举

```python
# src/document_hub/models.py

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentType(Enum):
    """文档类型"""
    # 需求文档
    PRD = "prd"                    # 产品需求文档
    USER_STORY = "user_story"      # 用户故事
    REQUIREMENT = "requirement"    # 需求列表
    
    # 设计文档
    ARCHITECTURE = "architecture"  # 系统架构
    TECH_DESIGN = "tech_design"    # 技术方案
    API_DESIGN = "api_design"      # API 设计
    DB_DESIGN = "db_design"        # 数据库设计
    
    # 代码文档
    CODE = "code"                  # 源代码
    COMPONENT = "component"        # 组件文档
    MODULE = "module"              # 模块文档
    
    # 测试文档
    TEST_CASE = "test_case"        # 测试用例
    TEST_REPORT = "test_report"    # 测试报告
    BUG_REPORT = "bug_report"      # Bug 报告
    
    # 交付文档
    USER_MANUAL = "user_manual"    # 用户手册
    API_DOC = "api_doc"            # API 文档
    DEPLOY_DOC = "deploy_doc"      # 部署文档
    RELEASE_NOTE = "release_note"  # 发布说明
    
    # 协作文档
    MEETING_NOTE = "meeting_note"  # 会议纪要
    DECISION_LOG = "decision_log"  # 决策日志
    PROGRESS_REPORT = "progress"   # 进度报告
    
    # 其他
    OTHER = "other"                # 其他文档
```

### 2.2 文档元数据

```python
class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: str                      # 文档标题
    doc_type: DocumentType          # 文档类型
    author: str                     # 作者 (Agent 角色)
    created_at: int                 # 创建时间戳
    updated_at: int                 # 更新时间戳
    version: int                    # 版本号
    status: str = "draft"           # 状态：draft, review, approved, archived
    tags: List[str] = Field(default_factory=list)  # 标签
    related_docs: List[str] = Field(default_factory=list)  # 相关文档
    visibility: str = "team"        # 可见性：private, team, public
    file_size: int = 0              # 文件大小 (字节)
    checksum: Optional[str] = None  # 校验和
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
```

### 2.3 文档内容模型

```python
class DocumentContent(BaseModel):
    """文档内容"""
    content: str                    # 文档内容
    format: str = "markdown"        # 格式：markdown, plain, json, yaml
    encoding: str = "utf-8"         # 编码
    language: str = "zh-CN"         # 语言
    line_count: int = 0             # 行数
    word_count: int = 0             # 字数
    hash: Optional[str] = None      # 内容哈希
```

### 2.4 文档完整模型

```python
class Document(BaseModel):
    """文档完整模型"""
    id: str                         # 文档 ID (唯一标识)
    path: str                       # 文件路径
    metadata: DocumentMetadata      # 元数据
    content: DocumentContent        # 内容
    version_history: List[str] = Field(default_factory=list)  # 版本历史 ID 列表
    
    class Config:
        use_enum_values = True
```

### 2.5 文档版本模型

```python
class DocumentVersion(BaseModel):
    """文档版本"""
    version_id: str                 # 版本 ID
    document_id: str                # 文档 ID
    version: int                    # 版本号
    content: DocumentContent        # 版本内容
    author: str                     # 作者
    timestamp: int                  # 时间戳
    change_summary: str             # 变更摘要
    diff: Optional[str] = None      # 与上一版本的 diff
    parent_version: Optional[str] = None  # 父版本 ID
```

---

## 3. 文档存储设计

### 3.1 存储结构

```
document_hub/
├── store.py              # 文档存储主类
├── storage/              # 物理存储目录
│   ├── prd/              # 需求文档
│   ├── design/           # 设计文档
│   ├── code/             # 代码文档
│   ├── test/             # 测试文档
│   ├── delivery/         # 交付文档
│   └── collaboration/    # 协作文档
├── versions/             # 版本存储
│   └── {doc_id}/
│       └── v{version}.json
├── index/                # 索引文件
│   ├── documents.json    # 文档索引
│   └── tags.json         # 标签索引
└── cache/                # 缓存目录
    └── {doc_id}.cache
```

### 3.2 文档存储类

```python
# src/document_hub/store.py

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Document, DocumentType, DocumentMetadata, DocumentContent


class DocumentStore:
    """
    文档存储类
    
    负责文档的物理存储、读取、索引管理
    """
    
    def __init__(self, base_path: str = "./document_hub/storage"):
        self.base_path = Path(base_path)
        self.index_path = self.base_path.parent / "index"
        self.version_path = self.base_path.parent / "versions"
        
        # 初始化目录结构
        self._initialize_storage()
        
        # 内存缓存
        self._cache: Dict[str, Document] = {}
        
        # 加载索引
        self._index = self._load_index()
    
    def _initialize_storage(self):
        """初始化存储目录结构"""
        # 创建文档类型目录
        for doc_type in DocumentType:
            dir_path = self.base_path / doc_type.value
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建索引和版本目录
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.version_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, document: Document) -> bool:
        """
        保存文档
        
        流程：
        1. 验证文档
        2. 计算校验和
        3. 写入物理文件
        4. 更新索引
        5. 更新缓存
        
        返回：是否成功
        """
        # 1. 验证文档
        self._validate_document(document)
        
        # 2. 计算校验和
        document.metadata.checksum = self._calculate_checksum(document.content.content)
        
        # 3. 写入物理文件
        file_path = self._get_file_path(document)
        await self._write_file(file_path, document)
        
        # 4. 更新索引
        self._update_index(document)
        
        # 5. 更新缓存
        self._cache[document.id] = document
        
        return True
    
    async def load(self, doc_id: str) -> Optional[Document]:
        """
        加载文档
        
        优先从缓存加载，缓存未命中则从磁盘加载
        """
        # 检查缓存
        if doc_id in self._cache:
            return self._cache[doc_id]
        
        # 从磁盘加载
        doc_path = self._find_document_path(doc_id)
        if doc_path and doc_path.exists():
            document = await self._read_file(doc_path)
            self._cache[doc_id] = document
            return document
        
        return None
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        # 从缓存移除
        if doc_id in self._cache:
            del self._cache[doc_id]
        
        # 从索引移除
        if doc_id in self._index:
            del self._index[doc_id]
            await self._save_index()
        
        # 删除物理文件
        doc_path = self._find_document_path(doc_id)
        if doc_path and doc_path.exists():
            doc_path.unlink()
        
        return True
    
    async def list_documents(
        self,
        doc_type: Optional[DocumentType] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """
        列出文档
        
        支持按类型、状态、标签过滤
        """
        results = []
        
        for doc_id, metadata in self._index.items():
            # 过滤条件
            if doc_type and metadata.get("doc_type") != doc_type.value:
                continue
            if status and metadata.get("status") != status:
                continue
            if tags and not any(tag in metadata.get("tags", []) for tag in tags):
                continue
            
            # 加载文档
            doc = await self.load(doc_id)
            if doc:
                results.append(doc)
            
            # 限制数量
            if len(results) >= limit:
                break
        
        return results[offset:offset + limit]
    
    async def search(
        self,
        query: str,
        doc_type: Optional[DocumentType] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        支持全文搜索 (简单实现，可替换为 Elasticsearch)
        """
        results = []
        query_lower = query.lower()
        
        for doc_id, metadata in self._index.items():
            # 类型过滤
            if doc_type and metadata.get("doc_type") != doc_type.value:
                continue
            
            # 加载文档
            doc = await self.load(doc_id)
            if not doc:
                continue
            
            # 搜索标题、标签、内容
            if (
                query_lower in doc.metadata.title.lower() or
                any(query_lower in tag.lower() for tag in doc.metadata.tags) or
                query_lower in doc.content.content.lower()
            ):
                results.append({
                    "id": doc.id,
                    "title": doc.metadata.title,
                    "type": doc.metadata.doc_type,
                    "snippet": self._extract_snippet(doc.content.content, query),
                    "score": self._calculate_relevance(doc, query),
                })
        
        # 按相关性排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _validate_document(self, document: Document):
        """验证文档"""
        if not document.id:
            raise ValueError("Document ID is required")
        if not document.path:
            raise ValueError("Document path is required")
        if not document.content.content:
            raise ValueError("Document content is required")
    
    def _calculate_checksum(self, content: str) -> str:
        """计算内容校验和"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_file_path(self, document: Document) -> Path:
        """获取文件存储路径"""
        doc_type = document.metadata.doc_type
        if isinstance(doc_type, str):
            doc_type = DocumentType(doc_type)
        
        return self.base_path / doc_type.value / f"{document.id}.json"
    
    def _find_document_path(self, doc_id: str) -> Optional[Path]:
        """查找文档路径"""
        for doc_type in DocumentType:
            path = self.base_path / doc_type.value / f"{doc_id}.json"
            if path.exists():
                return path
        return None
    
    async def _write_file(self, path: Path, document: Document):
        """写入文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(document.dict(), f, ensure_ascii=False, indent=2)
    
    async def _read_file(self, path: Path) -> Document:
        """读取文件"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Document(**data)
    
    def _update_index(self, document: Document):
        """更新索引"""
        self._index[document.id] = {
            "title": document.metadata.title,
            "doc_type": document.metadata.doc_type,
            "status": document.metadata.status,
            "author": document.metadata.author,
            "created_at": document.metadata.created_at,
            "updated_at": document.metadata.updated_at,
            "version": document.metadata.version,
            "tags": document.metadata.tags,
            "path": str(self._get_file_path(document)),
        }
    
    def _load_index(self) -> Dict[str, Any]:
        """加载索引"""
        index_file = self.index_path / "documents.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    async def _save_index(self):
        """保存索引"""
        index_file = self.index_path / "documents.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)
    
    def _extract_snippet(self, content: str, query: str, length: int = 200) -> str:
        """提取内容片段"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 找到查询词位置
        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:length] + "..."
        
        # 提取片段
        start = max(0, pos - 50)
        end = min(len(content), pos + length)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _calculate_relevance(self, document: Document, query: str) -> float:
        """计算相关性分数"""
        score = 0.0
        query_lower = query.lower()
        
        # 标题匹配权重最高
        if query_lower in document.metadata.title.lower():
            score += 10.0
        
        # 标签匹配
        for tag in document.metadata.tags:
            if query_lower in tag.lower():
                score += 5.0
        
        # 内容匹配
        content_lower = document.content.content.lower()
        query_words = query_lower.split()
        for word in query_words:
            if word in content_lower:
                score += 1.0
        
        return score
```

---

## 4. 版本控制设计

### 4.1 版本管理类

```python
# src/document_hub/version.py

import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Document, DocumentVersion, DocumentContent


class VersionControl:
    """
    版本控制类
    
    负责文档版本管理、Diff 计算、版本回滚
    """
    
    def __init__(self, store: "DocumentStore"):
        self.store = store
        self.version_path = store.version_path
    
    async def create_version(
        self,
        document: Document,
        change_summary: str,
        author: str,
    ) -> DocumentVersion:
        """
        创建新版本
        
        流程：
        1. 递增版本号
        2. 计算 Diff
        3. 保存版本
        4. 更新文档版本历史
        
        返回：新版本对象
        """
        # 1. 递增版本号
        new_version = document.metadata.version + 1
        
        # 2. 获取上一版本
        previous_version = await self.get_version(document.id, document.metadata.version)
        
        # 3. 计算 Diff
        diff = None
        if previous_version:
            diff = self._calculate_diff(
                previous_version.content.content,
                document.content.content,
            )
        
        # 4. 创建版本对象
        version = DocumentVersion(
            version_id=self._generate_version_id(document.id, new_version),
            document_id=document.id,
            version=new_version,
            content=document.content,
            author=author,
            timestamp=int(datetime.now().timestamp()),
            change_summary=change_summary,
            diff=diff,
            parent_version=previous_version.version_id if previous_version else None,
        )
        
        # 5. 保存版本
        await self._save_version(version)
        
        # 6. 更新文档版本历史
        document.version_history.append(version.version_id)
        document.metadata.version = new_version
        document.metadata.updated_at = version.timestamp
        
        return version
    
    async def get_version(
        self,
        doc_id: str,
        version: int,
    ) -> Optional[DocumentVersion]:
        """获取指定版本"""
        version_file = self._get_version_file_path(doc_id, version)
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                data = __import__('json').load(f)
            return DocumentVersion(**data)
        return None
    
    async def get_version_history(self, doc_id: str) -> List[DocumentVersion]:
        """获取版本历史"""
        doc = await self.store.load(doc_id)
        if not doc:
            return []
        
        versions = []
        for version_id in doc.version_history:
            # 从版本 ID 解析版本号
            version = int(version_id.split("_v")[-1])
            v = await self.get_version(doc_id, version)
            if v:
                versions.append(v)
        
        return versions
    
    async def rollback(
        self,
        doc_id: str,
        target_version: int,
        author: str,
    ) -> Optional[Document]:
        """
        回滚到指定版本
        
        流程：
        1. 获取目标版本
        2. 创建新版本 (内容为回滚版本)
        3. 更新文档
        
        返回：回滚后的文档
        """
        # 1. 获取目标版本
        target = await self.get_version(doc_id, target_version)
        if not target:
            return None
        
        # 2. 加载当前文档
        document = await self.store.load(doc_id)
        if not document:
            return None
        
        # 3. 更新文档内容
        document.content = target.content
        document.metadata.checksum = target.content.hash
        
        # 4. 创建新版本
        await self.create_version(
            document=document,
            change_summary=f"Rollback to version {target_version}",
            author=author,
        )
        
        # 5. 保存文档
        await self.store.save(document)
        
        return document
    
    def _calculate_diff(self, old_content: str, new_content: str) -> str:
        """计算 Diff (简化实现)"""
        # 可以使用 difflib 或集成 git diff
        import difflib
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='old',
            tofile='new',
        )
        
        return ''.join(diff)
    
    def _generate_version_id(self, doc_id: str, version: int) -> str:
        """生成版本 ID"""
        return f"{doc_id}_v{version}"
    
    def _get_version_file_path(self, doc_id: str, version: int) -> __import__('pathlib').Path:
        """获取版本文件路径"""
        doc_version_dir = self.version_path / doc_id
        doc_version_dir.mkdir(parents=True, exist_ok=True)
        return doc_version_dir / f"v{version}.json"
    
    async def _save_version(self, version: DocumentVersion):
        """保存版本"""
        file_path = self._get_version_file_path(version.document_id, version.version)
        with open(file_path, 'w', encoding='utf-8') as f:
            __import__('json').dump(version.dict(), f, ensure_ascii=False, indent=2)
```

---

## 5. 通知系统设计

### 5.1 通知模型

```python
# src/document_hub/notification.py

from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio


class NotificationType(Enum):
    """通知类型"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_REVIEWED = "document_reviewed"
    DOCUMENT_APPROVED = "document_approved"
    VERSION_CREATED = "version_created"
    LOCK_ACQUIRED = "lock_acquired"
    LOCK_RELEASED = "lock_released"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """通知模型"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    document_id: str
    document_title: str
    message: str
    sender: str  # 发送者 (Agent 角色)
    recipients: List[str]  # 接收者列表
    timestamp: int
    read: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 5.2 订阅/发布机制

```python
class NotificationService:
    """
    通知服务类
    
    实现订阅/发布模式，支持事件驱动的通知机制
    """
    
    def __init__(self):
        # 订阅者列表：topic -> [callback, ...]
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # 通知队列
        self._queue: asyncio.Queue = asyncio.Queue()
        
        # 通知历史
        self._history: List[Notification] = []
        
        # 后台任务
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def subscribe(
        self,
        topic: str,
        callback: Callable[[Notification], None],
    ):
        """
        订阅主题
        
        主题格式：
        - "document.*" - 所有文档事件
        - "document.created" - 文档创建事件
        - "document.updated.{doc_type}" - 特定类型文档更新
        - "agent.{agent_role}" - 特定 Agent 的事件
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
    
    def unsubscribe(
        self,
        topic: str,
        callback: Callable[[Notification], None],
    ):
        """取消订阅"""
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)
    
    async def publish(self, notification: Notification):
        """
        发布通知
        
        流程：
        1. 加入通知队列
        2. 匹配订阅者
        3. 异步发送通知
        """
        # 1. 加入队列
        await self._queue.put(notification)
        
        # 2. 保存到历史
        self._history.append(notification)
        
        # 3. 匹配并通知订阅者
        await self._notify_subscribers(notification)
    
    async def _notify_subscribers(self, notification: Notification):
        """通知匹配的订阅者"""
        topics_to_notify = []
        
        # 精确匹配
        exact_topic = f"document.{notification.type.value}"
        if exact_topic in self._subscribers:
            topics_to_notify.append(exact_topic)
        
        # 通配符匹配
        wildcard_topic = "document.*"
        if wildcard_topic in self._subscribers:
            topics_to_notify.append(wildcard_topic)
        
        # 按 Agent 匹配
        for recipient in notification.recipients:
            agent_topic = f"agent.{recipient}"
            if agent_topic in self._subscribers:
                topics_to_notify.append(agent_topic)
        
        # 发送通知
        for topic in topics_to_notify:
            for callback in self._subscribers.get(topic, []):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(notification)
                    else:
                        callback(notification)
                except Exception as e:
                    # 记录错误，不影响其他订阅者
                    print(f"Error notifying subscriber for {topic}: {e}")
    
    async def start_background_processor(self):
        """启动后台处理器"""
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
    
    async def stop_background_processor(self):
        """停止后台处理器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _process_queue(self):
        """处理通知队列"""
        while self._running:
            try:
                notification = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                # 可以在这里添加批处理、延迟发送等逻辑
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing notification queue: {e}")
    
    def get_history(
        self,
        doc_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
    ) -> List[Notification]:
        """获取通知历史"""
        results = self._history
        
        if doc_id:
            results = [n for n in results if n.document_id == doc_id]
        
        if notification_type:
            results = [n for n in results if n.type == notification_type]
        
        return results[-limit:]
```

### 5.3 与 Document Store 集成

```python
# src/document_hub/store.py (增强版)

class DocumentStore:
    def __init__(
        self,
        base_path: str = "./document_hub/storage",
        notification_service: Optional[NotificationService] = None,
    ):
        # ... 其他初始化代码 ...
        
        self.notification_service = notification_service
    
    async def save(
        self,
        document: Document,
        notify: bool = True,
        notify_agents: Optional[List[str]] = None,
    ) -> bool:
        """保存文档并发送通知"""
        # 检查是否是更新
        is_update = document.id in self._index
        
        # 保存文档
        result = await super().save(document)
        
        if result and notify and self.notification_service:
            # 确定通知接收者
            if notify_agents is None:
                notify_agents = [document.metadata.author]
            
            # 创建通知
            notification = Notification(
                id=self._generate_notification_id(),
                type=NotificationType.DOCUMENT_UPDATED if is_update else NotificationType.DOCUMENT_CREATED,
                priority=NotificationPriority.NORMAL,
                document_id=document.id,
                document_title=document.metadata.title,
                message=f"文档已{'更新' if is_update else '创建'}: {document.metadata.title}",
                sender=document.metadata.author,
                recipients=notify_agents,
                timestamp=int(datetime.now().timestamp()),
                metadata={
                    "doc_type": document.metadata.doc_type,
                    "version": document.metadata.version,
                },
            )
            
            # 发布通知
            await self.notification_service.publish(notification)
        
        return result
```

---

## 6. 文档锁设计

### 6.1 锁模型

```python
# src/document_hub/lock.py

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import asyncio


class LockType(Enum):
    """锁类型"""
    READ = "read"       # 读锁 (共享)
    WRITE = "write"     # 写锁 (独占)


class LockStatus(Enum):
    """锁状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"


class DocumentLock(BaseModel):
    """文档锁"""
    lock_id: str
    document_id: str
    lock_type: LockType
    holder: str  # 持有者 (Agent 角色)
    acquired_at: int
    expires_at: int  # 过期时间
    status: LockStatus = LockStatus.ACTIVE
    
    class Config:
        use_enum_values = True
```

### 6.2 锁管理器

```python
class LockManager:
    """
    锁管理器
    
    实现文档级别的读写锁，支持：
    - 多个读锁 (共享)
    - 单个写锁 (独占)
    - 锁超时自动释放
    - 死锁检测
    """
    
    def __init__(self, default_timeout: int = 300):
        # 当前锁：doc_id -> [DocumentLock, ...]
        self._locks: Dict[str, List[DocumentLock]] = {}
        
        # 锁等待队列：doc_id -> [asyncio.Event, ...]
        self._wait_queue: Dict[str, List[asyncio.Event]] = {}
        
        # 默认锁超时时间 (秒)
        self.default_timeout = default_timeout
        
        # 后台任务
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def acquire_read_lock(
        self,
        doc_id: str,
        holder: str,
        timeout: Optional[int] = None,
    ) -> Optional[DocumentLock]:
        """
        获取读锁
        
        读锁是共享的，多个 Agent 可以同时持有读锁
        但不能在有写锁时获取读锁
        """
        # 检查是否有写锁
        if self._has_write_lock(doc_id):
            # 等待写锁释放
            await self._wait_for_lock(doc_id, timeout)
        
        # 创建锁
        lock = self._create_lock(
            doc_id=doc_id,
            lock_type=LockType.READ,
            holder=holder,
            timeout=timeout,
        )
        
        # 记录锁
        if doc_id not in self._locks:
            self._locks[doc_id] = []
        self._locks[doc_id].append(lock)
        
        return lock
    
    async def acquire_write_lock(
        self,
        doc_id: str,
        holder: str,
        timeout: Optional[int] = None,
    ) -> Optional[DocumentLock]:
        """
        获取写锁
        
        写锁是独占的，不能有其他的读锁或写锁
        """
        # 检查是否有其他锁
        if self._has_any_lock(doc_id):
            # 等待所有锁释放
            await self._wait_for_lock(doc_id, timeout)
        
        # 创建锁
        lock = self._create_lock(
            doc_id=doc_id,
            lock_type=LockType.WRITE,
            holder=holder,
            timeout=timeout,
        )
        
        # 记录锁
        self._locks[doc_id] = [lock]
        
        return lock
    
    async def release_lock(self, lock_id: str, doc_id: str) -> bool:
        """释放锁"""
        if doc_id not in self._locks:
            return False
        
        # 找到并移除锁
        for i, lock in enumerate(self._locks[doc_id]):
            if lock.lock_id == lock_id:
                lock.status = LockStatus.RELEASED
                self._locks[doc_id].pop(i)
                
                # 通知等待者
                await self._notify_waiters(doc_id)
                
                return True
        
        return False
    
    async def release_all_locks(self, holder: str) -> int:
        """释放某个持有者的所有锁"""
        released_count = 0
        
        for doc_id, locks in list(self._locks.items()):
            for lock in locks[:]:
                if lock.holder == holder:
                    await self.release_lock(lock.lock_id, doc_id)
                    released_count += 1
        
        return released_count
    
    def _create_lock(
        self,
        doc_id: str,
        lock_type: LockType,
        holder: str,
        timeout: Optional[int] = None,
    ) -> DocumentLock:
        """创建锁"""
        timeout = timeout or self.default_timeout
        now = int(datetime.now().timestamp())
        
        return DocumentLock(
            lock_id=self._generate_lock_id(doc_id, holder),
            document_id=doc_id,
            lock_type=lock_type,
            holder=holder,
            acquired_at=now,
            expires_at=now + timeout,
        )
    
    def _has_write_lock(self, doc_id: str) -> bool:
        """检查是否有写锁"""
        if doc_id not in self._locks:
            return False
        
        return any(
            lock.lock_type == LockType.WRITE and lock.status == LockStatus.ACTIVE
            for lock in self._locks[doc_id]
        )
    
    def _has_any_lock(self, doc_id: str) -> bool:
        """检查是否有任何锁"""
        if doc_id not in self._locks:
            return False
        
        return any(lock.status == LockStatus.ACTIVE for lock in self._locks[doc_id])
    
    async def _wait_for_lock(self, doc_id: str, timeout: Optional[int] = None):
        """等待锁释放"""
        if doc_id not in self._wait_queue:
            self._wait_queue[doc_id] = []
        
        event = asyncio.Event()
        self._wait_queue[doc_id].append(event)
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout or self.default_timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout waiting for lock on document {doc_id}")
        finally:
            if event in self._wait_queue.get(doc_id, []):
                self._wait_queue[doc_id].remove(event)
    
    async def _notify_waiters(self, doc_id: str):
        """通知等待者"""
        if doc_id in self._wait_queue:
            for event in self._wait_queue[doc_id]:
                event.set()
    
    def _generate_lock_id(self, doc_id: str, holder: str) -> str:
        """生成锁 ID"""
        import hashlib
        timestamp = int(datetime.now().timestamp())
        data = f"{doc_id}:{holder}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def start_background_processor(self):
        """启动后台处理器 (清理过期锁)"""
        self._running = True
        self._task = asyncio.create_task(self._cleanup_expired_locks())
    
    async def stop_background_processor(self):
        """停止后台处理器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_expired_locks(self):
        """清理过期锁"""
        while self._running:
            now = int(datetime.now().timestamp())
            
            for doc_id, locks in list(self._locks.items()):
                for lock in locks[:]:
                    if lock.status == LockStatus.ACTIVE and lock.expires_at < now:
                        lock.status = LockStatus.EXPIRED
                        locks.remove(lock)
                        await self._notify_waiters(doc_id)
            
            await asyncio.sleep(10)  # 每 10 秒检查一次
```

---

## 7. 与 OpenCode SDK 集成

### 7.1 文档读写适配器

```python
# src/document_hub/opencode_adapter.py

from typing import Optional
from opencode_4_py import OpenCodeClient, Session

from .store import DocumentStore
from .models import Document, DocumentType, DocumentMetadata, DocumentContent


class OpenCodeDocumentAdapter:
    """
    OpenCode SDK 文档适配器
    
    将 Document Hub 与 OpenCode SDK 集成
    """
    
    def __init__(
        self,
        store: DocumentStore,
        client: OpenCodeClient,
        session: Session,
    ):
        self.store = store
        self.client = client
        self.session = session
    
    async def read_from_opencode(self, path: str) -> Optional[Document]:
        """
        从 OpenCode 读取文档
        
        通过 OpenCode SDK 的 file.read API 读取文件，
        然后转换为 Document 模型
        """
        try:
            # 通过 OpenCode SDK 读取
            file_content = await self.client.file.read(path=path)
            
            # 转换为 Document
            doc_type = self._infer_doc_type(path)
            document = Document(
                id=self._generate_doc_id(path),
                path=path,
                metadata=DocumentMetadata(
                    title=path.split("/")[-1],
                    doc_type=doc_type,
                    author="System",
                    created_at=int(__import__('time').time()),
                    updated_at=int(__import__('time').time()),
                    version=1,
                ),
                content=DocumentContent(
                    content=file_content.content,
                    format=self._infer_format(path),
                ),
            )
            
            return document
        
        except Exception as e:
            print(f"Error reading from OpenCode: {e}")
            return None
    
    async def write_to_opencode(self, document: Document) -> bool:
        """
        写入文档到 OpenCode
        
        将 Document 通过 OpenCode SDK 写入文件系统
        """
        try:
            # 通过 OpenCode SDK 写入
            # 注意：OpenCode SDK 可能没有直接的 write API，
            # 需要通过 message 间接实现
            await self.client.message.send_text(
                session_id=self.session.id,
                text=f"Save this content to {document.path}:\n\n{document.content.content}",
            )
            
            # 保存到本地 Document Hub
            await self.store.save(document)
            
            return True
        
        except Exception as e:
            print(f"Error writing to OpenCode: {e}")
            return False
    
    def _infer_doc_type(self, path: str) -> DocumentType:
        """根据路径推断文档类型"""
        path_lower = path.lower()
        
        if ".md" in path_lower:
            if "prd" in path_lower:
                return DocumentType.PRD
            elif "design" in path_lower or "arch" in path_lower:
                return DocumentType.ARCHITECTURE
            elif "test" in path_lower:
                return DocumentType.TEST_CASE
            elif "manual" in path_lower or "guide" in path_lower:
                return DocumentType.USER_MANUAL
            else:
                return DocumentType.OTHER
        
        elif ".py" in path_lower or ".js" in path_lower or ".ts" in path_lower:
            return DocumentType.CODE
        
        elif ".json" in path_lower or ".yaml" in path_lower or ".yml" in path_lower:
            return DocumentType.API_DESIGN
        
        else:
            return DocumentType.OTHER
    
    def _infer_format(self, path: str) -> str:
        """根据路径推断文件格式"""
        path_lower = path.lower()
        
        if path_lower.endswith(".md"):
            return "markdown"
        elif path_lower.endswith(".json"):
            return "json"
        elif path_lower.endswith(".yaml") or path_lower.endswith(".yml"):
            return "yaml"
        elif path_lower.endswith(".txt"):
            return "plain"
        else:
            return "markdown"  # 默认
    
    def _generate_doc_id(self, path: str) -> str:
        """生成文档 ID"""
        import hashlib
        timestamp = int(__import__('time').time())
        data = f"{path}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
```

---

## 8. 使用示例

### 8.1 基本使用

```python
# examples/document_hub_basic.py

import asyncio
from src.document_hub.store import DocumentStore
from src.document_hub.models import (
    Document,
    DocumentType,
    DocumentMetadata,
    DocumentContent,
)
from src.document_hub.version import VersionControl
from src.document_hub.notification import NotificationService
from src.document_hub.lock import LockManager


async def main():
    # 1. 初始化组件
    store = DocumentStore()
    version_control = VersionControl(store)
    notification_service = NotificationService()
    lock_manager = LockManager()
    
    # 2. 创建文档
    doc = Document(
        id="doc_001",
        path="prd/PRD_v1.md",
        metadata=DocumentMetadata(
            title="在线商城系统 PRD",
            doc_type=DocumentType.PRD,
            author="Product Manager",
            created_at=int(__import__('time').time()),
            updated_at=int(__import__('time').time()),
            version=1,
            tags=["商城", "需求"],
        ),
        content=DocumentContent(
            content="# 在线商城系统 PRD\n\n## 需求描述...",
            format="markdown",
        ),
    )
    
    # 3. 获取写锁
    lock = await lock_manager.acquire_write_lock(
        doc_id=doc.id,
        holder="Product Manager",
    )
    
    # 4. 保存文档
    await store.save(doc)
    
    # 5. 创建版本
    version = await version_control.create_version(
        document=doc,
        change_summary="初始版本",
        author="Product Manager",
    )
    
    # 6. 发布通知
    await notification_service.publish({
        "type": "document_created",
        "document_id": doc.id,
        "recipients": ["System Architect", "Tech Lead"],
    })
    
    # 7. 释放锁
    await lock_manager.release_lock(lock.lock_id, doc.id)
    
    # 8. 读取文档
    loaded_doc = await store.load(doc.id)
    print(f"Loaded document: {loaded_doc.metadata.title}")
    
    # 9. 搜索文档
    results = await store.search("商城", limit=10)
    print(f"Search results: {len(results)} documents")
    
    # 10. 获取版本历史
    history = await version_control.get_version_history(doc.id)
    print(f"Version history: {len(history)} versions")


if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 Agent 集成使用

```python
# examples/agent_document_collaboration.py

import asyncio
from src.agent.base import Agent
from src.document_hub.store import DocumentStore
from src.document_hub.lock import LockManager


class ProductManagerAgent(Agent):
    """产品经理 Agent 示例"""
    
    def __init__(self, session, client, store: DocumentStore, lock_manager: LockManager):
        super().__init__(
            role="Product Manager",
            expertise=["需求分析"],
            session=session,
            client=client,
        )
        self.store = store
        self.lock_manager = lock_manager
    
    async def create_prd(self, requirements: str) -> Document:
        """创建 PRD 文档"""
        # 获取写锁
        doc_id = "prd_001"
        lock = await self.lock_manager.acquire_write_lock(
            doc_id=doc_id,
            holder=self.role,
        )
        
        try:
            # 创建文档
            doc = Document(
                id=doc_id,
                path="prd/PRD_v1.md",
                metadata=DocumentMetadata(
                    title="在线商城系统 PRD",
                    doc_type=DocumentType.PRD,
                    author=self.role,
                    created_at=int(__import__('time').time()),
                    updated_at=int(__import__('time').time()),
                    version=1,
                ),
                content=DocumentContent(
                    content=requirements,
                    format="markdown",
                ),
            )
            
            # 保存文档
            await self.store.save(doc)
            
            # 发布诉求给 Architect
            await self.help_requests(
                to_agent="System Architect",
                subject="请评估技术可行性",
                content=f"基于 PRD: {doc.metadata.title}",
            )
            
            return doc
        
        finally:
            # 释放锁
            await self.lock_manager.release_lock(lock.lock_id, doc_id)
```

---

## 9. 实现计划

| 阶段 | 内容 | 文件 | 预计时间 |
|------|------|------|----------|
| 1 | 文档模型 | `models.py` | 2 小时 |
| 2 | 文档存储 | `store.py` | 4 小时 |
| 3 | 版本控制 | `version.py` | 3 小时 |
| 4 | 通知服务 | `notification.py` | 3 小时 |
| 5 | 锁管理器 | `lock.py` | 3 小时 |
| 6 | OpenCode 适配器 | `opencode_adapter.py` | 2 小时 |
| 7 | 单元测试 | `tests/` | 4 小时 |
| **总计** | | | **21 小时** |

---

## 10. 测试策略

### 10.1 单元测试

```python
# tests/document_hub/test_store.py

import pytest
from src.document_hub.store import DocumentStore
from src.document_hub.models import Document, DocumentType, DocumentMetadata, DocumentContent


class TestDocumentStore:
    """文档存储测试"""
    
    @pytest.fixture
    def store(self, tmp_path):
        """创建测试存储"""
        return DocumentStore(base_path=str(tmp_path / "storage"))
    
    @pytest.fixture
    def sample_document(self):
        """创建示例文档"""
        return Document(
            id="test_001",
            path="test/test.md",
            metadata=DocumentMetadata(
                title="Test Document",
                doc_type=DocumentType.OTHER,
                author="Test Agent",
                created_at=0,
                updated_at=0,
                version=1,
            ),
            content=DocumentContent(
                content="# Test\n\nContent",
                format="markdown",
            ),
        )
    
    async def test_save_document(self, store, sample_document):
        """测试保存文档"""
        result = await store.save(sample_document)
        assert result is True
    
    async def test_load_document(self, store, sample_document):
        """测试加载文档"""
        await store.save(sample_document)
        loaded = await store.load(sample_document.id)
        assert loaded is not None
        assert loaded.id == sample_document.id
    
    async def test_delete_document(self, store, sample_document):
        """测试删除文档"""
        await store.save(sample_document)
        result = await store.delete(sample_document.id)
        assert result is True
        
        loaded = await store.load(sample_document.id)
        assert loaded is None
    
    async def test_search_documents(self, store, sample_document):
        """测试搜索文档"""
        await store.save(sample_document)
        results = await store.search("Test")
        assert len(results) > 0
```

### 10.2 集成测试

```python
# tests/document_hub/test_integration.py

import pytest
from src.document_hub.store import DocumentStore
from src.document_hub.version import VersionControl
from src.document_hub.lock import LockManager


class TestDocumentHubIntegration:
    """文档中心集成测试"""
    
    @pytest.fixture
    def components(self, tmp_path):
        """创建测试组件"""
        store = DocumentStore(base_path=str(tmp_path / "storage"))
        version_control = VersionControl(store)
        lock_manager = LockManager()
        return store, version_control, lock_manager
    
    async def test_version_control_flow(self, components):
        """测试版本控制流程"""
        store, version_control, lock_manager = components
        
        # 创建文档
        doc = create_test_document()
        await store.save(doc)
        
        # 创建版本
        version = await version_control.create_version(
            document=doc,
            change_summary="v1",
            author="Test Agent",
        )
        assert version.version == 1
        
        # 更新文档
        doc.content.content = "# Updated\n\nContent"
        doc.metadata.version = 2
        
        # 创建新版本
        version2 = await version_control.create_version(
            document=doc,
            change_summary="v2",
            author="Test Agent",
        )
        assert version2.version == 2
        
        # 获取版本历史
        history = await version_control.get_version_history(doc.id)
        assert len(history) == 2
    
    async def test_concurrent_locks(self, components):
        """测试并发锁"""
        store, version_control, lock_manager = components
        
        doc_id = "test_concurrent"
        
        # Agent 1 获取读锁
        lock1 = await lock_manager.acquire_read_lock(
            doc_id=doc_id,
            holder="Agent 1",
        )
        
        # Agent 2 获取读锁 (应该成功)
        lock2 = await lock_manager.acquire_read_lock(
            doc_id=doc_id,
            holder="Agent 2",
        )
        assert lock2 is not None
        
        # Agent 3 尝试获取写锁 (应该等待或失败)
        # 这里可以测试超时逻辑
```

---

## 11. 风险和挑战

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 并发冲突 | 高 | 中 | 实现完善的锁机制 |
| 性能问题 | 中 | 中 | 添加缓存层、索引优化 |
| 存储膨胀 | 中 | 中 | 版本清理策略、压缩 |
| 通知延迟 | 低 | 中 | 异步处理、批量化 |
| OpenCode 集成复杂 | 中 | 高 | 适配器模式、降级方案 |

---

## 12. 成功标准

- [ ] 文档存储读写功能正常
- [ ] 版本控制支持创建、查询、回滚
- [ ] 通知服务支持订阅/发布模式
- [ ] 锁管理器支持读写锁、超时释放
- [ ] 与 OpenCode SDK 集成成功
- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试全部通过

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Document Hub | 共享文档中心 |
| Document Store | 文档存储层 |
| Version Control | 版本控制 |
| Notification Service | 通知服务 |
| Lock Manager | 锁管理器 |

### B. 参考资源

- [Git 版本控制原理](https://git-scm.com/book)
- [发布订阅模式](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)
- [读写锁](https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock)

---

> 最后更新：2026-03-11
> 状态：草稿
> 审核：待审核
