#!/usr/bin/env python3
"""
Knowledge Base Write MCP Server - 新知识写入专用

这是一个专门用于存储新业务知识和代码片段的写入 MCP 服务器。
提供安全的知识存储功能，不包含任何检索或查询操作。
"""

import os
import json
import sqlite3
import logging
import re
from typing import Optional, List, Dict, Any, Literal
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("kb_write_mcp")


# ==================== Configuration ====================

class KnowledgeWriteConfig(BaseModel):
    """Knowledge base write configuration."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database_path: str = Field(default="knowledge.db", description="Path to SQLite knowledge base file")
    max_knowledge_size: int = Field(default=50000, description="Maximum number of knowledge entries to store")
    enable_fts: bool = Field(default=True, description="Enable full-text search using FTS5")
    code_highlight_enabled: bool = Field(default=True, description="Enable syntax highlighting for code snippets")


# ==================== Knowledge Entry Types ====================

KnowledgeType = Literal["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]

# Language mappings for syntax highlighting
LANGUAGE_MAPPINGS = {
    "python": ["py", "python"],
    "javascript": ["js", "javascript", "jsx"],
    "typescript": ["ts", "typescript", "tsx"],
    "java": ["java"],
    "go": ["go", "golang"],
    "rust": ["rs", "rust"],
    "c": ["c"],
    "cpp": ["cpp", "c++"],
    "csharp": ["cs", "c#"],
    "ruby": ["rb", "ruby"],
    "php": ["php"],
    "sql": ["sql"],
    "bash": ["sh", "bash", "shell"],
    "html": ["html", "htm"],
    "css": ["css"],
    "json": ["json"],
    "yaml": ["yaml", "yml"],
    "markdown": ["md", "markdown"],
    "text": ["txt", "text"]
}

def detect_language_from_content(content: str, filename: Optional[str] = None) -> str:
    """Detect programming language from content or filename."""
    if filename:
        ext = filename.split('.')[-1].lower() if '.' in filename else filename.lower()
        for lang, extensions in LANGUAGE_MAPPINGS.items():
            if ext in extensions:
                return lang
    
    # Simple content-based detection
    content_lower = content.lower()
    if 'def ' in content_lower or 'import ' in content_lower or 'class ' in content_lower:
        return "python"
    elif 'function ' in content_lower or 'const ' in content_lower or 'let ' in content_lower:
        return "javascript"
    elif 'public class ' in content_lower or 'private ' in content_lower:
        return "java"
    elif 'package main' in content_lower or 'func ' in content_lower:
        return "go"
    elif '#include' in content or 'int main' in content:
        return "c"
    
    return "text"


# ==================== Shared Knowledge Client (Write-Only) ====================

class KnowledgeWriteClient:
    """Shared SQLite client for write-only knowledge base operations."""

    def __init__(self, config: KnowledgeWriteConfig):
        self.config = config
        self.connection = None
        self._ensure_database()

    def _ensure_database(self):
        """Ensure the knowledge base database and tables exist."""
        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()
        
        # Create main knowledge entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('business_knowledge', 'code_snippet', 'documentation', 'faq', 'best_practice')),
                category TEXT,
                tags TEXT,  -- JSON array stored as text
                language TEXT,  -- For code snippets
                source TEXT,  -- URL, file path, or other source
                confidence REAL DEFAULT 1.0,  -- Confidence score (0.0 - 1.0)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT  -- Additional metadata as JSON
            )
        ''')
        
        # Create FTS5 virtual table for full-text search if enabled
        if self.config.enable_fts:
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_entries_fts 
                USING fts5(title, content, category, tags, source, metadata, 
                          content=knowledge_entries, content_rowid=id)
            ''')
            
            # Create triggers to keep FTS table in sync
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS knowledge_entries_ai AFTER INSERT ON knowledge_entries BEGIN
                    INSERT INTO knowledge_entries_fts(rowid, title, content, category, tags, source, metadata)
                    VALUES (new.id, new.title, new.content, new.category, new.tags, new.source, new.metadata);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS knowledge_entries_ad AFTER DELETE ON knowledge_entries BEGIN
                    INSERT INTO knowledge_entries_fts(knowledge_entries_fts, rowid, title, content, category, tags, source, metadata)
                    VALUES ('delete', old.id, old.title, old.content, old.category, old.tags, old.source, old.metadata);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS knowledge_entries_au AFTER UPDATE ON knowledge_entries BEGIN
                    INSERT INTO knowledge_entries_fts(knowledge_entries_fts, rowid, title, content, category, tags, source, metadata)
                    VALUES ('delete', old.id, old.title, old.content, old.category, old.tags, old.source, old.metadata);
                    INSERT INTO knowledge_entries_fts(rowid, title, content, category, tags, source, metadata)
                    VALUES (new.id, new.title, new.content, new.category, new.tags, new.source, new.metadata);
                END
            ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_entries(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_entries(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_language ON knowledge_entries(language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge_entries(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_entries(tags)')
        
        conn.commit()
        conn.close()

    def connect(self):
        """Establish SQLite connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.config.database_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        """Close SQLite connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def store_knowledge(self, 
                       title: str, 
                       content: str, 
                       type: KnowledgeType,
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       language: Optional[str] = None,
                       source: Optional[str] = None,
                       confidence: float = 1.0,
                       metadata: Optional[Dict[str, Any]] = None) -> int:
        """Store a new knowledge entry."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Auto-detect language if not provided and it's a code snippet
        if type == "code_snippet" and not language:
            language = detect_language_from_content(content, source)
        
        # Convert tags list to JSON string
        tags_str = json.dumps(tags) if tags else None
        metadata_str = json.dumps(metadata) if metadata else None
        
        cursor.execute(
            """
            INSERT INTO knowledge_entries 
            (title, content, type, category, tags, language, source, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, content, type, category, tags_str, language, source, confidence, metadata_str)
        )
        
        knowledge_id = cursor.lastrowid
        if knowledge_id is None:
            raise RuntimeError("Failed to get knowledge ID after insertion")
        conn.commit()
        return knowledge_id


# ==================== Lifespan Management ====================

# Global knowledge client instance
_knowledge_write_client: Optional[KnowledgeWriteClient] = None

def get_knowledge_write_client() -> KnowledgeWriteClient:
    """Get the global knowledge write client instance."""
    if _knowledge_write_client is None:
        raise RuntimeError("Knowledge write client not initialized")
    return _knowledge_write_client

@asynccontextmanager
async def app_lifespan(app):
    """Manage knowledge write client lifecycle."""
    global _knowledge_write_client
    
    # Load configuration from environment or use defaults
    config = KnowledgeWriteConfig(
        database_path=os.getenv("KNOWLEDGE_DB_PATH", "knowledge.db"),
        max_knowledge_size=int(os.getenv("KNOWLEDGE_MAX_SIZE", "50000")),
        enable_fts=os.getenv("KNOWLEDGE_ENABLE_FTS", "true").lower() == "true",
        code_highlight_enabled=os.getenv("KNOWLEDGE_CODE_HIGHLIGHT", "true").lower() == "true"
    )

    _knowledge_write_client = KnowledgeWriteClient(config)
    yield {"knowledge_write": _knowledge_write_client}

    # Cleanup
    if _knowledge_write_client and _knowledge_write_client.connection:
        _knowledge_write_client.close()
    _knowledge_write_client = None


# Reinitialize MCP with lifespan
mcp = FastMCP("kb_write_mcp", lifespan=app_lifespan)


# ==================== Enums and Response Models ====================

from enum import Enum

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ==================== Tool: Store Knowledge ====================

class StoreKnowledgeInput(BaseModel):
    """Input for storing knowledge."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    title: str = Field(
        ...,
        description="Descriptive title for the knowledge entry",
        min_length=1,
        max_length=200
    )
    content: str = Field(
        ...,
        description="Complete knowledge content. For code snippets, include the full code with comments.",
        min_length=1
    )
    type: KnowledgeType = Field(
        ...,
        description="Type of knowledge: business_knowledge, code_snippet, documentation, faq, or best_practice"
    )
    category: Optional[str] = Field(
        default=None,
        description="Category to organize knowledge (e.g., 'Database', 'API', 'Frontend', 'Security')"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="List of tags for better organization and search (e.g., ['python', 'async', 'database'])"
    )
    language: Optional[str] = Field(
        default=None,
        description="Programming language for code snippets (auto-detected if not provided)"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the knowledge (URL, file path, document name, etc.)"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence level in the accuracy of this knowledge (0.0 - 1.0)",
        ge=0.0,
        le=1.0
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional structured metadata (e.g., author, version, related_files)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="kb_store_knowledge",
    description="Store business knowledge, code snippets, documentation, FAQs, or best practices in the knowledge base for future reference and retrieval."
)
async def store_knowledge(params: StoreKnowledgeInput, ctx: Context) -> str:
    """
    Store a new knowledge entry with comprehensive metadata.

    Args:
        params (StoreKnowledgeInput): Input parameters containing:
            - title (str): Descriptive title for the knowledge entry
            - content (str): Complete knowledge content
            - type (KnowledgeType): Type of knowledge
            - category (Optional[str]): Category for organization
            - tags (Optional[List[str]]): Tags for search and filtering
            - language (Optional[str]): Programming language (for code)
            - source (Optional[str]): Source of the knowledge
            - confidence (float): Confidence level (0.0-1.0)
            - metadata (Optional[Dict]): Additional metadata
            - response_format (ResponseFormat): Output format

    Returns:
        str: Result of the knowledge storage operation.
    """
    knowledge_client: KnowledgeWriteClient = get_knowledge_write_client()

    try:
        knowledge_id = knowledge_client.store_knowledge(
            title=params.title,
            content=params.content,
            type=params.type,
            category=params.category,
            tags=params.tags,
            language=params.language,
            source=params.source,
            confidence=params.confidence,
            metadata=params.metadata
        )
        
        result = {
            "success": True,
            "knowledge_id": knowledge_id,
            "message": "Knowledge stored successfully",
            "type": params.type,
            "title": params.title
        }

        if params.response_format == ResponseFormat.MARKDOWN:
            return f"✅ **Knowledge stored successfully**\n\n- **ID**: {knowledge_id}\n- **Type**: {params.type}\n- **Title**: {params.title}\n- **Category**: {params.category or 'N/A'}"
        else:
            return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error storing knowledge: {e}")
        result = {
            "success": False,
            "error": str(e),
            "message": "Failed to store knowledge"
        }
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"❌ **Error storing knowledge**: {str(e)}"
        else:
            return json.dumps(result, indent=2)


# ==================== Main Entry Point ====================

def create_kb_write_mcp():
    """Create and configure the Knowledge Write MCP server."""
    mcp = FastMCP("kb_write_mcp", lifespan=app_lifespan)
    
    # Register tools here
    @mcp.tool(
        name="kb_store_knowledge",
        description="Store business knowledge, code snippets, documentation, FAQs, or best practices in the knowledge base for future reference and retrieval."
    )
    async def store_knowledge(params: StoreKnowledgeInput, ctx: Context) -> str:
        """
        Store a new knowledge entry with comprehensive metadata.

        Args:
            params (StoreKnowledgeInput): Input parameters containing:
                - title (str): Descriptive title for the knowledge entry
                - content (str): Complete knowledge content
                - type (KnowledgeType): Type of knowledge
                - category (Optional[str]): Category for organization
                - tags (Optional[List[str]]): Tags for search and filtering
                - language (Optional[str]): Programming language (for code)
                - source (Optional[str]): Source of the knowledge
                - confidence (float): Confidence level (0.0-1.0)
                - metadata (Optional[Dict]): Additional metadata
                - response_format (ResponseFormat): Output format

        Returns:
            str: Result of the knowledge storage operation.
        """
        knowledge_client: KnowledgeWriteClient = get_knowledge_write_client()

        try:
            knowledge_id = knowledge_client.store_knowledge(
                title=params.title,
                content=params.content,
                type=params.type,
                category=params.category,
                tags=params.tags,
                language=params.language,
                source=params.source,
                confidence=params.confidence,
                metadata=params.metadata
            )
            
            result = {
                "success": True,
                "knowledge_id": knowledge_id,
                "message": "Knowledge stored successfully",
                "type": params.type,
                "title": params.title
            }

            if params.response_format == ResponseFormat.MARKDOWN:
                return f"✅ **Knowledge stored successfully**\n\n- **ID**: {knowledge_id}\n- **Type**: {params.type}\n- **Title**: {params.title}\n- **Category**: {params.category or 'N/A'}"
            else:
                return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            result = {
                "success": False,
                "error": str(e),
                "message": "Failed to store knowledge"
            }
            
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"❌ **Error storing knowledge**: {str(e)}"
            else:
                return json.dumps(result, indent=2)
    
    return mcp

if __name__ == "__main__":
    # Parse command line arguments early to get host/port
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Write MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable_http"],
        default="streamable_http",
        help="Transport mechanism (default: streamable_http)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8327,
        help="HTTP port (default: 8327)"
    )

    args = parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments early to get host/port
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Write MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable_http"],
        default="streamable_http",
        help="Transport mechanism (default: streamable_http)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8327,
        help="HTTP port (default: 8327)"
    )

    args = parser.parse_args()

    # Create MCP instance with tools registered and host/port
    if args.transport == "streamable_http":
        mcp = FastMCP("kb_write_mcp", lifespan=app_lifespan, host=args.host, port=args.port)
        
        @mcp.tool(
            name="kb_store_knowledge",
            description="Store business knowledge, code snippets, documentation, FAQs, or best practices in the knowledge base for future reference and retrieval."
        )
        async def store_knowledge(params: StoreKnowledgeInput, ctx: Context) -> str:
            """
            Store a new knowledge entry with comprehensive metadata.

            Args:
                params (StoreKnowledgeInput): Input parameters containing:
                    - title (str): Descriptive title for the knowledge entry
                    - content (str): Complete knowledge content
                    - type (KnowledgeType): Type of knowledge
                    - category (Optional[str]): Category for organization
                    - tags (Optional[List[str]]): Tags for search and filtering
                    - language (Optional[str]): Programming language (for code)
                    - source (Optional[str]): Source of the knowledge
                    - confidence (float): Confidence level (0.0-1.0)
                    - metadata (Optional[Dict]): Additional metadata
                    - response_format (ResponseFormat): Output format

            Returns:
                str: Result of the knowledge storage operation.
            """
            knowledge_client: KnowledgeWriteClient = get_knowledge_write_client()

            try:
                knowledge_id = knowledge_client.store_knowledge(
                    title=params.title,
                    content=params.content,
                    type=params.type,
                    category=params.category,
                    tags=params.tags,
                    language=params.language,
                    source=params.source,
                    confidence=params.confidence,
                    metadata=params.metadata
                )
                
                result = {
                    "success": True,
                    "knowledge_id": knowledge_id,
                    "message": "Knowledge stored successfully",
                    "type": params.type,
                    "title": params.title
                }

                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"✅ **Knowledge stored successfully**\n\n- **ID**: {knowledge_id}\n- **Type**: {params.type}\n- **Title**: {params.title}\n- **Category**: {params.category or 'N/A'}"
                else:
                    return json.dumps(result, indent=2)

            except Exception as e:
                logger.error(f"Error storing knowledge: {e}")
                result = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to store knowledge"
                }
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error storing knowledge**: {str(e)}"
                else:
                    return json.dumps(result, indent=2)
        
        mcp.run(transport="sse")
    else:
        mcp = FastMCP("kb_write_mcp", lifespan=app_lifespan)
        
        @mcp.tool(
            name="kb_store_knowledge",
            description="Store business knowledge, code snippets, documentation, FAQs, or best practices in the knowledge base for future reference and retrieval."
        )
        async def store_knowledge(params: StoreKnowledgeInput, ctx: Context) -> str:
            knowledge_client: KnowledgeWriteClient = get_knowledge_write_client()
            try:
                knowledge_id = knowledge_client.store_knowledge(
                    title=params.title,
                    content=params.content,
                    type=params.type,
                    category=params.category,
                    tags=params.tags,
                    language=params.language,
                    source=params.source,
                    confidence=params.confidence,
                    metadata=params.metadata
                )
                result = {
                    "success": True,
                    "knowledge_id": knowledge_id,
                    "message": "Knowledge stored successfully",
                    "type": params.type,
                    "title": params.title
                }
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"✅ **Knowledge stored successfully**\n\n- **ID**: {knowledge_id}\n- **Type**: {params.type}\n- **Title**: {params.title}\n- **Category**: {params.category or 'N/A'}"
                else:
                    return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Error storing knowledge: {e}")
                result = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to store knowledge"
                }
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error storing knowledge**: {str(e)}"
                else:
                    return json.dumps(result, indent=2)
        
        mcp.run(transport="stdio")