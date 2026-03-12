"""文档存储."""

from __future__ import annotations

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
        
        self._initialize_storage()
        
        self._cache: Dict[str, Document] = {}
        self._index = self._load_index()
    
    def _initialize_storage(self):
        """初始化存储目录结构"""
        for doc_type in DocumentType:
            dir_path = self.base_path / doc_type.value
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.version_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, document: Document) -> bool:
        """保存文档"""
        self._validate_document(document)
        
        document.metadata.checksum = self._calculate_checksum(document.content.content)
        
        file_path = self._get_file_path(document)
        self._write_file(file_path, document)
        
        self._update_index(document)
        self._cache[document.id] = document
        
        return True
    
    async def load(self, doc_id: str) -> Optional[Document]:
        """加载文档"""
        if doc_id in self._cache:
            return self._cache[doc_id]
        
        doc_path = self._find_document_path(doc_id)
        if doc_path and doc_path.exists():
            document = self._read_file(doc_path)
            self._cache[doc_id] = document
            return document
        
        return None
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self._cache:
            del self._cache[doc_id]
        
        if doc_id in self._index:
            del self._index[doc_id]
            await self._save_index()
        
        doc_path = self._find_document_path(doc_id)
        if doc_path and doc_path.exists():
            doc_path.unlink()
        
        return True
    
    async def list_documents(
        self,
        doc_type: Optional[DocumentType] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Document]:
        """列出文档"""
        results = []
        
        for doc_id, metadata in self._index.items():
            if doc_type and metadata.get("doc_type") != doc_type.value:
                continue
            if status and metadata.get("status") != status:
                continue
            
            doc = await self.load(doc_id)
            if doc:
                results.append(doc)
            
            if len(results) >= limit:
                break
        
        return results
    
    def _validate_document(self, document: Document):
        """验证文档"""
        if not document.id:
            raise ValueError("Document ID is required")
        if not document.path:
            raise ValueError("Document path is required")
        if not document.content.content:
            raise ValueError("Document content is required")
    
    def _calculate_checksum(self, content: str) -> str:
        """计算校验和"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_file_path(self, document: Document) -> Path:
        """获取文件路径"""
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
    
    def _write_file(self, path: Path, document: Document):
        """写入文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(document.model_dump(), f, ensure_ascii=False, indent=2)
    
    def _read_file(self, path: Path) -> Document:
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
