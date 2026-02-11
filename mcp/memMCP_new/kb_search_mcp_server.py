#!/usr/bin/env python3
"""
Knowledge Base Search MCP Server - 只读检索专用

这是一个专门用于业务知识和代码片段检索的只读 MCP 服务器。
提供高效的全文搜索、过滤和查询功能，不包含任何写入操作。
"""

import os
import json
import sqlite3
import logging
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
mcp = FastMCP("kb_search_mcp")


# ==================== Configuration ====================

class KnowledgeSearchConfig(BaseModel):
    """Knowledge base search configuration."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database_path: str = Field(default="knowledge.db", description="Path to SQLite knowledge base file")
    enable_fts: bool = Field(default=True, description="Enable full-text search using FTS5")


# ==================== Knowledge Entry Types ====================

KnowledgeType = Literal["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]

# ==================== Shared Knowledge Client (Read-Only) ====================

class KnowledgeSearchClient:
    """Shared SQLite client for read-only knowledge base operations."""

    def __init__(self, config: KnowledgeSearchConfig):
        self.config = config
        self.connection = None
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure the knowledge base database exists."""
        if not os.path.exists(self.config.database_path):
            raise FileNotFoundError(f"Knowledge base database not found: {self.config.database_path}")

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

    def search_knowledge(self, 
                        query: str, 
                        types: Optional[List[KnowledgeType]] = None,
                        categories: Optional[List[str]] = None,
                        languages: Optional[List[str]] = None,
                        tags: Optional[List[str]] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge entries with advanced filtering."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Build WHERE clause for filtering
        where_conditions = []
        params = [query, limit]
        
        if types:
            type_placeholders = ','.join(['?' for _ in types])
            where_conditions.append(f"type IN ({type_placeholders})")
            params = types + params
        
        if categories:
            category_placeholders = ','.join(['?' for _ in categories])
            where_conditions.append(f"category IN ({category_placeholders})")
            params = categories + params
            
        if languages:
            language_placeholders = ','.join(['?' for _ in languages])
            where_conditions.append(f"language IN ({language_placeholders})")
            params = languages + params
            
        if tags:
            # For tags, we need to use LIKE since they're stored as JSON
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.insert(0, f'%"{tag}"%')  # JSON array contains the tag
            if tag_conditions:
                where_conditions.append(f"({' OR '.join(tag_conditions)})")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        if self.config.enable_fts:
            # Use FTS5 full-text search with filtering
            base_query = f"""
                SELECT k.id, k.title, k.content, k.type, k.category, k.tags, k.language, 
                       k.source, k.confidence, k.created_at, k.updated_at, k.metadata
                FROM knowledge_entries k
                JOIN knowledge_entries_fts fts ON k.id = fts.rowid
                WHERE knowledge_entries_fts MATCH ?
                {where_clause}
                ORDER BY rank
                LIMIT ?
            """
        else:
            # Use basic LIKE search with filtering
            base_query = f"""
                SELECT id, title, content, type, category, tags, language, 
                       source, confidence, created_at, updated_at, metadata
                FROM knowledge_entries
                WHERE (title LIKE ? OR content LIKE ?)
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params = [f"%{query}%", f"%{query}%"] + params[1:]  # Replace query with two LIKE patterns
        
        cursor.execute(base_query, params)
        
        results = []
        for row in cursor.fetchall():
            result = {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "type": row["type"],
                "category": row["category"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "language": row["language"],
                "source": row["source"],
                "confidence": row["confidence"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
            results.append(result)
        
        return results

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific knowledge entry by ID."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, title, content, type, category, tags, language, 
                   source, confidence, created_at, updated_at, metadata
            FROM knowledge_entries WHERE id = ?
            """,
            (knowledge_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "type": row["type"],
                "category": row["category"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "language": row["language"],
                "source": row["source"],
                "confidence": row["confidence"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
        return None

    def list_knowledge(self, 
                      types: Optional[List[KnowledgeType]] = None,
                      categories: Optional[List[str]] = None,
                      limit: int = 10, 
                      offset: int = 0) -> List[Dict[str, Any]]:
        """List knowledge entries with optional filtering and pagination."""
        conn = self.connect()
        cursor = conn.cursor()
        
        where_conditions = []
        params = [limit, offset]
        
        if types:
            type_placeholders = ','.join(['?' for _ in types])
            where_conditions.append(f"type IN ({type_placeholders})")
            params = types + params
            
        if categories:
            category_placeholders = ','.join(['?' for _ in categories])
            where_conditions.append(f"category IN ({category_placeholders})")
            params = categories + params
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        cursor.execute(
            f"""
            SELECT id, title, content, type, category, tags, language, 
                   source, confidence, created_at, updated_at, metadata
            FROM knowledge_entries
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params
        )
        
        results = []
        for row in cursor.fetchall():
            result = {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "type": row["type"],
                "category": row["category"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "language": row["language"],
                "source": row["source"],
                "confidence": row["confidence"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
            results.append(result)
        
        return results

    def get_knowledge_count(self, 
                           types: Optional[List[KnowledgeType]] = None,
                           categories: Optional[List[str]] = None) -> int:
        """Get total number of knowledge entries with optional filtering."""
        conn = self.connect()
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if types:
            type_placeholders = ','.join(['?' for _ in types])
            where_conditions.append(f"type IN ({type_placeholders})")
            params.extend(types)
            
        if categories:
            category_placeholders = ','.join(['?' for _ in categories])
            where_conditions.append(f"category IN ({category_placeholders})")
            params.extend(categories)
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        cursor.execute(f"SELECT COUNT(*) as count FROM knowledge_entries {where_clause}", params)
        return cursor.fetchone()["count"]

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM knowledge_entries WHERE category IS NOT NULL ORDER BY category")
        return [row[0] for row in cursor.fetchall()]

    def get_tags(self) -> List[str]:
        """Get all unique tags."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT tags FROM knowledge_entries WHERE tags IS NOT NULL")
        all_tags = set()
        for row in cursor.fetchall():
            tags = json.loads(row[0])
            all_tags.update(tags)
        
        return sorted(list(all_tags))

    def get_languages(self) -> List[str]:
        """Get all unique programming languages (for code snippets)."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT language FROM knowledge_entries WHERE language IS NOT NULL ORDER BY language")
        return [row[0] for row in cursor.fetchall()]


# ==================== Lifespan Management ====================

# Global knowledge client instance
_knowledge_search_client: Optional[KnowledgeSearchClient] = None

def get_knowledge_search_client() -> KnowledgeSearchClient:
    """Get the global knowledge search client instance."""
    if _knowledge_search_client is None:
        raise RuntimeError("Knowledge search client not initialized")
    return _knowledge_search_client

@asynccontextmanager
async def app_lifespan(app):
    """Manage knowledge search client lifecycle."""
    global _knowledge_search_client
    
    # Load configuration from environment or use defaults
    config = KnowledgeSearchConfig(
        database_path=os.getenv("KNOWLEDGE_DB_PATH", "knowledge.db"),
        enable_fts=os.getenv("KNOWLEDGE_ENABLE_FTS", "true").lower() == "true"
    )

    _knowledge_search_client = KnowledgeSearchClient(config)
    yield {"knowledge_search": _knowledge_search_client}

    # Cleanup
    if _knowledge_search_client and _knowledge_search_client.connection:
        _knowledge_search_client.close()
    _knowledge_search_client = None


# Reinitialize MCP with lifespan
mcp = FastMCP("kb_search_mcp", lifespan=app_lifespan)


# ==================== Enums and Response Models ====================

from enum import Enum

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ==================== Utility Functions ====================

def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format data as markdown table."""
    if not rows:
        return "*No data available*"

    # Header row
    md = "| " + " | ".join(headers) + " |\n"
    # Separator
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    # Data rows
    for row in rows:
        md += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    return md

def format_code_block(content: str, language: Optional[str] = None) -> str:
    """Format content as code block with syntax highlighting."""
    if language and language != "text":
        return f"```{language}\n{content}\n```"
    else:
        return f"```\n{content}\n```"


# ==================== Tool: Search Knowledge ====================

class SearchKnowledgeInput(BaseModel):
    """Input for searching knowledge."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(
        ...,
        description="Natural language search query to find relevant knowledge. Use descriptive terms related to what you're looking for.",
        min_length=1
    )
    types: Optional[List[KnowledgeType]] = Field(
        default=None,
        description="Filter by knowledge types (e.g., ['code_snippet', 'business_knowledge'])"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories (e.g., ['Database', 'API', 'Frontend'])"
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Filter by programming languages (for code snippets)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (e.g., ['python', 'async', 'security'])"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of search results to return (1-100). Use higher values for comprehensive searches, lower for focused results.",
        ge=1,
        le=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="kb_search_knowledge",
    description="Search the knowledge base using natural language queries with advanced filtering options for business knowledge, code snippets, and documentation."
)
async def search_knowledge(params: SearchKnowledgeInput, ctx: Context) -> str:
    """
    Search knowledge entries with advanced filtering capabilities.

    Args:
        params (SearchKnowledgeInput): Input parameters containing:
            - query (str): Natural language search query
            - types (Optional[List[KnowledgeType]]): Filter by knowledge types
            - categories (Optional[List[str]]): Filter by categories
            - languages (Optional[List[str]]): Filter by programming languages
            - tags (Optional[List[str]]): Filter by tags
            - limit (int): Maximum number of results to return
            - response_format (ResponseFormat): Output format

    Returns:
        str: Search results.
    """
    knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

    try:
        results = knowledge_client.search_knowledge(
            query=params.query,
            types=params.types,
            categories=params.categories,
            languages=params.languages,
            tags=params.tags,
            limit=params.limit
        )
        
        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return f"*No knowledge entries found matching query: '{params.query}'*"
            
            lines = [f"# Knowledge Search Results for: `{params.query}`", ""]
            lines.append(f"Found {len(results)} knowledge entr{'y' if len(results) == 1 else 'ies'}")
            if params.types:
                lines.append(f"Types: {', '.join(params.types)}")
            if params.categories:
                lines.append(f"Categories: {', '.join(params.categories)}")
            if params.languages:
                lines.append(f"Languages: {', '.join(params.languages)}")
            if params.tags:
                lines.append(f"Tags: {', '.join(params.tags)}")
            lines.append("")
            
            for i, knowledge in enumerate(results, 1):
                lines.append(f"## {i}. {knowledge['title']} (ID: {knowledge['id']})")
                lines.append(f"**Type**: {knowledge['type']}")
                lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                if knowledge['tags']:
                    lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                if knowledge['language']:
                    lines.append(f"**Language**: {knowledge['language']}")
                if knowledge['source']:
                    lines.append(f"**Source**: {knowledge['source']}")
                lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                lines.append(f"**Created**: {knowledge['created_at']}")
                lines.append("")
                lines.append("**Content**:")
                if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                    lines.append(format_code_block(knowledge['content'], knowledge['language']))
                else:
                    lines.append(f"```\n{knowledge['content']}\n```")
                lines.append("")
            
            return "\n".join(lines)
        
        else:
            return json.dumps({
                "query": params.query,
                "filters": {
                    "types": params.types,
                    "categories": params.categories,
                    "languages": params.languages,
                    "tags": params.tags
                },
                "count": len(results),
                "results": results
            }, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"❌ **Error searching knowledge**: {str(e)}"
        else:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to search knowledge"
            }, indent=2)


# ==================== Tool: Get Knowledge by ID ====================

class GetKnowledgeInput(BaseModel):
    """Input for getting knowledge by ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    knowledge_id: int = Field(
        ...,
        description="ID of the knowledge entry to retrieve",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="kb_get_knowledge",
    description="Retrieve a specific knowledge entry by its ID when you need exact information that was previously stored."
)
async def get_knowledge(params: GetKnowledgeInput, ctx: Context) -> str:
    """
    Retrieve a specific knowledge entry by ID.

    Args:
        params (GetKnowledgeInput): Input parameters containing:
            - knowledge_id (int): ID of the knowledge entry to retrieve
            - response_format (ResponseFormat): Output format

    Returns:
        str: Retrieved knowledge entry or error message.
    """
    knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

    try:
        knowledge = knowledge_client.get_knowledge_by_id(params.knowledge_id)
        
        if not knowledge:
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"*Knowledge entry with ID {params.knowledge_id} not found*"
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Knowledge entry with ID {params.knowledge_id} not found",
                    "message": "Knowledge entry not found"
                }, indent=2)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Knowledge Entry Details (ID: {knowledge['id']})", ""]
            lines.append(f"**Title**: {knowledge['title']}")
            lines.append(f"**Type**: {knowledge['type']}")
            lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
            if knowledge['tags']:
                lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
            if knowledge['language']:
                lines.append(f"**Language**: {knowledge['language']}")
            if knowledge['source']:
                lines.append(f"**Source**: {knowledge['source']}")
            lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
            lines.append(f"**Created**: {knowledge['created_at']}")
            lines.append(f"**Updated**: {knowledge['updated_at']}")
            if knowledge['metadata']:
                lines.append(f"**Metadata**: ```json\n{json.dumps(knowledge['metadata'], indent=2)}\n```")
            lines.append("")
            lines.append("**Content**:")
            if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                lines.append(format_code_block(knowledge['content'], knowledge['language']))
            else:
                lines.append(f"```\n{knowledge['content']}\n```")
            return "\n".join(lines)
        
        else:
            return json.dumps(knowledge, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error retrieving knowledge: {e}")
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"❌ **Error retrieving knowledge**: {str(e)}"
        else:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve knowledge"
            }, indent=2)


# ==================== Tool: List Knowledge ====================

class ListKnowledgeInput(BaseModel):
    """Input for listing knowledge."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    types: Optional[List[KnowledgeType]] = Field(
        default=None,
        description="Filter by knowledge types"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of knowledge entries to return",
        ge=1,
        le=100
    )
    offset: int = Field(
        default=0,
        description="Number of knowledge entries to skip (for pagination)",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="kb_list_knowledge",
    description="Browse all stored knowledge entries with filtering and pagination to understand what information is available in your knowledge base."
)
async def list_knowledge(params: ListKnowledgeInput, ctx: Context) -> str:
    """
    List knowledge entries with filtering and pagination.

    Args:
        params (ListKnowledgeInput): Input parameters containing:
            - types (Optional[List[KnowledgeType]]): Filter by knowledge types
            - categories (Optional[List[str]]): Filter by categories
            - limit (int): Maximum number of knowledge entries to return
            - offset (int): Number of knowledge entries to skip (for pagination)
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of knowledge entries or error message.
    """
    knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

    try:
        results = knowledge_client.list_knowledge(
            types=params.types,
            categories=params.categories,
            limit=params.limit,
            offset=params.offset
        )
        total_count = knowledge_client.get_knowledge_count(
            types=params.types,
            categories=params.categories
        )
        
        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return "*No knowledge entries found*"
            
            lines = ["# Knowledge Base Entries", ""]
            lines.append(f"Showing entries {params.offset + 1} to {min(params.offset + params.limit, total_count)} of {total_count}")
            if params.types:
                lines.append(f"Types: {', '.join(params.types)}")
            if params.categories:
                lines.append(f"Categories: {', '.join(params.categories)}")
            lines.append("")
            
            headers = ["ID", "Type", "Category", "Title", "Language", "Created"]
            table_rows = []
            
            for knowledge in results:
                row = [
                    knowledge['id'],
                    knowledge['type'],
                    knowledge['category'] or 'N/A',
                    knowledge['title'][:40] + "..." if len(knowledge['title']) > 40 else knowledge['title'],
                    knowledge['language'] or 'N/A',
                    knowledge['created_at']
                ]
                table_rows.append(row)
            
            lines.append(format_markdown_table(headers, table_rows))
            return "\n".join(str(line) for line in lines)
        
        else:
            return json.dumps({
                "total_count": total_count,
                "offset": params.offset,
                "limit": params.limit,
                "filters": {
                    "types": params.types,
                    "categories": params.categories
                },
                "results": results
            }, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"❌ **Error listing knowledge**: {str(e)}"
        else:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to list knowledge"
            }, indent=2)


# ==================== Tool: Get Knowledge Statistics ====================

class GetStatisticsInput(BaseModel):
    """Input for getting knowledge statistics."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="kb_get_statistics",
    description="Get statistics about the knowledge base including total counts, categories, tags, and languages available."
)
async def get_statistics(params: GetStatisticsInput, ctx: Context) -> str:
    """
    Get statistics about the knowledge base.

    Args:
        params (GetStatisticsInput): Input parameters containing:
            - response_format (ResponseFormat): Output format

    Returns:
        str: Knowledge base statistics.
    """
    knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

    try:
        total_count = knowledge_client.get_knowledge_count()
        categories = knowledge_client.get_categories()
        tags = knowledge_client.get_tags()
        languages = knowledge_client.get_languages()
        
        # Count by type
        type_counts = {}
        for knowledge_type in ["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]:
            count = knowledge_client.get_knowledge_count(types=[knowledge_type])
            if count > 0:
                type_counts[knowledge_type] = count
        
        stats = {
            "total_entries": total_count,
            "type_distribution": type_counts,
            "categories": categories,
            "tags": tags,
            "languages": languages,
            "database_path": knowledge_client.config.database_path
        }
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Knowledge Base Statistics", ""]
            lines.append(f"**Total Entries**: {total_count}")
            lines.append("")
            lines.append("## Type Distribution")
            for knowledge_type, count in type_counts.items():
                lines.append(f"- **{knowledge_type.replace('_', ' ').title()}**: {count}")
            lines.append("")
            lines.append(f"## Categories ({len(categories)})")
            if categories:
                lines.append(", ".join(f"`{cat}`" for cat in categories))
            else:
                lines.append("None")
            lines.append("")
            lines.append(f"## Tags ({len(tags)})")
            if tags:
                lines.append(", ".join(f"`{tag}`" for tag in tags[:20]))  # Show first 20
                if len(tags) > 20:
                    lines.append(f"... and {len(tags) - 20} more")
            else:
                lines.append("None")
            lines.append("")
            lines.append(f"## Languages ({len(languages)})")
            if languages:
                lines.append(", ".join(f"`{lang}`" for lang in languages))
            else:
                lines.append("None")
            lines.append("")
            lines.append(f"**Database Path**: `{knowledge_client.config.database_path}`")
            
            return "\n".join(lines)
        
        else:
            return json.dumps(stats, indent=2)

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"❌ **Error getting statistics**: {str(e)}"
        else:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to get statistics"
            }, indent=2)


# ==================== Main Entry Point ====================

def create_kb_search_mcp():
    """Create and configure the Knowledge Search MCP server."""
    mcp = FastMCP("kb_search_mcp", lifespan=app_lifespan)
    
    # Register all search tools here
    @mcp.tool(
        name="kb_search_knowledge",
        description="Search the knowledge base using natural language queries with advanced filtering options for business knowledge, code snippets, and documentation."
    )
    async def search_knowledge(params: SearchKnowledgeInput, ctx: Context) -> str:
        """
        Search knowledge entries with advanced filtering capabilities.

        Args:
            params (SearchKnowledgeInput): Input parameters containing:
                - query (str): Natural language search query
                - types (Optional[List[KnowledgeType]]): Filter by knowledge types
                - categories (Optional[List[str]]): Filter by categories
                - languages (Optional[List[str]]): Filter by programming languages
                - tags (Optional[List[str]]): Filter by tags
                - limit (int): Maximum number of results to return
                - response_format (ResponseFormat): Output format

        Returns:
            str: Search results.
        """
        knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

        try:
            results = knowledge_client.search_knowledge(
                query=params.query,
                types=params.types,
                categories=params.categories,
                languages=params.languages,
                tags=params.tags,
                limit=params.limit
            )
            
            if params.response_format == ResponseFormat.MARKDOWN:
                if not results:
                    return f"*No knowledge entries found matching query: '{params.query}'*"
                
                lines = [f"# Knowledge Search Results for: `{params.query}`", ""]
                lines.append(f"Found {len(results)} knowledge entr{'y' if len(results) == 1 else 'ies'}")
                if params.types:
                    lines.append(f"Types: {', '.join(params.types)}")
                if params.categories:
                    lines.append(f"Categories: {', '.join(params.categories)}")
                if params.languages:
                    lines.append(f"Languages: {', '.join(params.languages)}")
                if params.tags:
                    lines.append(f"Tags: {', '.join(params.tags)}")
                lines.append("")
                
                for i, knowledge in enumerate(results, 1):
                    lines.append(f"## {i}. {knowledge['title']} (ID: {knowledge['id']})")
                    lines.append(f"**Type**: {knowledge['type']}")
                    lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                    if knowledge['tags']:
                        lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                    if knowledge['language']:
                        lines.append(f"**Language**: {knowledge['language']}")
                    if knowledge['source']:
                        lines.append(f"**Source**: {knowledge['source']}")
                    lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                    lines.append(f"**Created**: {knowledge['created_at']}")
                    lines.append("")
                    lines.append("**Content**:")
                    if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                        lines.append(format_code_block(knowledge['content'], knowledge['language']))
                    else:
                        lines.append(f"```\n{knowledge['content']}\n```")
                    lines.append("")
                
                return "\n".join(lines)
            
            else:
                return json.dumps({
                    "query": params.query,
                    "filters": {
                        "types": params.types,
                        "categories": params.categories,
                        "languages": params.languages,
                        "tags": params.tags
                    },
                    "count": len(results),
                    "results": results
                }, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"❌ **Error searching knowledge**: {str(e)}"
            else:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search knowledge"
                }, indent=2)
    
    @mcp.tool(
        name="kb_get_knowledge",
        description="Retrieve a specific knowledge entry by its ID when you need exact information that was previously stored."
    )
    async def get_knowledge(params: GetKnowledgeInput, ctx: Context) -> str:
        """
        Retrieve a specific knowledge entry by ID.

        Args:
            params (GetKnowledgeInput): Input parameters containing:
                - knowledge_id (int): ID of the knowledge entry to retrieve
                - response_format (ResponseFormat): Output format

        Returns:
            str: Retrieved knowledge entry or error message.
        """
        knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

        try:
            knowledge = knowledge_client.get_knowledge_by_id(params.knowledge_id)
            
            if not knowledge:
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"*Knowledge entry with ID {params.knowledge_id} not found*"
                else:
                    return json.dumps({
                        "success": False,
                        "error": f"Knowledge entry with ID {params.knowledge_id} not found",
                        "message": "Knowledge entry not found"
                    }, indent=2)
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [f"# Knowledge Entry Details (ID: {knowledge['id']})", ""]
                lines.append(f"**Title**: {knowledge['title']}")
                lines.append(f"**Type**: {knowledge['type']}")
                lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                if knowledge['tags']:
                    lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                if knowledge['language']:
                    lines.append(f"**Language**: {knowledge['language']}")
                if knowledge['source']:
                    lines.append(f"**Source**: {knowledge['source']}")
                lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                lines.append(f"**Created**: {knowledge['created_at']}")
                lines.append(f"**Updated**: {knowledge['updated_at']}")
                if knowledge['metadata']:
                    lines.append(f"**Metadata**: ```json\n{json.dumps(knowledge['metadata'], indent=2)}\n```")
                lines.append("")
                lines.append("**Content**:")
                if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                    lines.append(format_code_block(knowledge['content'], knowledge['language']))
                else:
                    lines.append(f"```\n{knowledge['content']}\n```")
                return "\n".join(lines)
            
            else:
                return json.dumps(knowledge, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"❌ **Error retrieving knowledge**: {str(e)}"
            else:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to retrieve knowledge"
                }, indent=2)

    @mcp.tool(
        name="kb_list_knowledge",
        description="Browse all stored knowledge entries with filtering and pagination to understand what information is available in your knowledge base."
    )
    async def list_knowledge(params: ListKnowledgeInput, ctx: Context) -> str:
        """
        List knowledge entries with filtering and pagination.

        Args:
            params (ListKnowledgeInput): Input parameters containing:
                - types (Optional[List[KnowledgeType]]): Filter by knowledge types
                - categories (Optional[List[str]]): Filter by categories
                - limit (int): Maximum number of knowledge entries to return
                - offset (int): Number of knowledge entries to skip (for pagination)
                - response_format (ResponseFormat): Output format

        Returns:
            str: List of knowledge entries or error message.
        """
        knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

        try:
            results = knowledge_client.list_knowledge(
                types=params.types,
                categories=params.categories,
                limit=params.limit,
                offset=params.offset
            )
            total_count = knowledge_client.get_knowledge_count(
                types=params.types,
                categories=params.categories
            )
            
            if params.response_format == ResponseFormat.MARKDOWN:
                if not results:
                    return "*No knowledge entries found*"
                
                lines = ["# Knowledge Base Entries", ""]
                lines.append(f"Showing entries {params.offset + 1} to {min(params.offset + params.limit, total_count)} of {total_count}")
                if params.types:
                    lines.append(f"Types: {', '.join(params.types)}")
                if params.categories:
                    lines.append(f"Categories: {', '.join(params.categories)}")
                lines.append("")
                
                headers = ["ID", "Type", "Category", "Title", "Language", "Created"]
                table_rows = []
                
                for knowledge in results:
                    row = [
                        knowledge['id'],
                        knowledge['type'],
                        knowledge['category'] or 'N/A',
                        knowledge['title'][:40] + "..." if len(knowledge['title']) > 40 else knowledge['title'],
                        knowledge['language'] or 'N/A',
                        knowledge['created_at']
                    ]
                    table_rows.append(row)
                
                lines.append(format_markdown_table(headers, table_rows))
                return "\n".join(str(line) for line in lines)
            
            else:
                return json.dumps({
                    "total_count": total_count,
                    "offset": params.offset,
                    "limit": params.limit,
                    "filters": {
                        "types": params.types,
                        "categories": params.categories
                    },
                    "results": results
                }, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error listing knowledge: {e}")
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"❌ **Error listing knowledge**: {str(e)}"
            else:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to list knowledge"
                }, indent=2)

    @mcp.tool(
        name="kb_get_statistics",
        description="Get statistics about the knowledge base including total counts, categories, tags, and languages available."
    )
    async def get_statistics(params: GetStatisticsInput, ctx: Context) -> str:
        """
        Get statistics about the knowledge base.

        Args:
            params (GetStatisticsInput): Input parameters containing:
                - response_format (ResponseFormat): Output format

        Returns:
            str: Knowledge base statistics.
        """
        knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

        try:
            total_count = knowledge_client.get_knowledge_count()
            categories = knowledge_client.get_categories()
            tags = knowledge_client.get_tags()
            languages = knowledge_client.get_languages()
            
            # Count by type
            type_counts = {}
            for knowledge_type in ["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]:
                count = knowledge_client.get_knowledge_count(types=[knowledge_type])
                if count > 0:
                    type_counts[knowledge_type] = count
            
            stats = {
                "total_entries": total_count,
                "type_distribution": type_counts,
                "categories": categories,
                "tags": tags,
                "languages": languages,
                "database_path": knowledge_client.config.database_path
            }
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Knowledge Base Statistics", ""]
                lines.append(f"**Total Entries**: {total_count}")
                lines.append("")
                lines.append("## Type Distribution")
                for knowledge_type, count in type_counts.items():
                    lines.append(f"- **{knowledge_type.replace('_', ' ').title()}**: {count}")
                lines.append("")
                lines.append(f"## Categories ({len(categories)})")
                if categories:
                    lines.append(", ".join(f"`{cat}`" for cat in categories))
                else:
                    lines.append("None")
                lines.append("")
                lines.append(f"## Tags ({len(tags)})")
                if tags:
                    lines.append(", ".join(f"`{tag}`" for tag in tags[:20]))  # Show first 20
                    if len(tags) > 20:
                        lines.append(f"... and {len(tags) - 20} more")
                else:
                    lines.append("None")
                lines.append("")
                lines.append(f"## Languages ({len(languages)})")
                if languages:
                    lines.append(", ".join(f"`{lang}`" for lang in languages))
                else:
                    lines.append("None")
                lines.append("")
                lines.append(f"**Database Path**: `{knowledge_client.config.database_path}`")
                
                return "\n".join(lines)
            
            else:
                return json.dumps(stats, indent=2)

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"❌ **Error getting statistics**: {str(e)}"
            else:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get statistics"
                }, indent=2)
    
    return mcp

if __name__ == "__main__":
    # Parse command line arguments early to get host/port
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Search MCP Server")
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
        default=8326,
        help="HTTP port (default: 8326)"
    )

    args = parser.parse_args()

    # Create MCP instance with tools registered and host/port
    if args.transport == "streamable_http":
        mcp = FastMCP("kb_search_mcp", lifespan=app_lifespan, host=args.host, port=args.port)
        
        # Register all search tools here
        @mcp.tool(
            name="kb_search_knowledge",
            description="Search the knowledge base using natural language queries with advanced filtering options for business knowledge, code snippets, and documentation."
        )
        async def search_knowledge(params: SearchKnowledgeInput, ctx: Context) -> str:
            """
            Search knowledge entries with advanced filtering capabilities.

            Args:
                params (SearchKnowledgeInput): Input parameters containing:
                    - query (str): Natural language search query
                    - types (Optional[List[KnowledgeType]]): Filter by knowledge types
                    - categories (Optional[List[str]]): Filter by categories
                    - languages (Optional[List[str]]): Filter by programming languages
                    - tags (Optional[List[str]]): Filter by tags
                    - limit (int): Maximum number of results to return
                    - response_format (ResponseFormat): Output format

            Returns:
                str: Search results.
            """
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

            try:
                results = knowledge_client.search_knowledge(
                    query=params.query,
                    types=params.types,
                    categories=params.categories,
                    languages=params.languages,
                    tags=params.tags,
                    limit=params.limit
                )
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    if not results:
                        return f"*No knowledge entries found matching query: '{params.query}'*"
                    
                    lines = [f"# Knowledge Search Results for: `{params.query}`", ""]
                    lines.append(f"Found {len(results)} knowledge entr{'y' if len(results) == 1 else 'ies'}")
                    if params.types:
                        lines.append(f"Types: {', '.join(params.types)}")
                    if params.categories:
                        lines.append(f"Categories: {', '.join(params.categories)}")
                    if params.languages:
                        lines.append(f"Languages: {', '.join(params.languages)}")
                    if params.tags:
                        lines.append(f"Tags: {', '.join(params.tags)}")
                    lines.append("")
                    
                    for i, knowledge in enumerate(results, 1):
                        lines.append(f"## {i}. {knowledge['title']} (ID: {knowledge['id']})")
                        lines.append(f"**Type**: {knowledge['type']}")
                        lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                        if knowledge['tags']:
                            lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                        if knowledge['language']:
                            lines.append(f"**Language**: {knowledge['language']}")
                        if knowledge['source']:
                            lines.append(f"**Source**: {knowledge['source']}")
                        lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                        lines.append(f"**Created**: {knowledge['created_at']}")
                        lines.append("")
                        lines.append("**Content**:")
                        if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                            lines.append(format_code_block(knowledge['content'], knowledge['language']))
                        else:
                            lines.append(f"```\n{knowledge['content']}\n```")
                        lines.append("")
                    
                    return "\n".join(lines)
                
                else:
                    return json.dumps({
                        "query": params.query,
                        "filters": {
                            "types": params.types,
                            "categories": params.categories,
                            "languages": params.languages,
                            "tags": params.tags
                        },
                        "count": len(results),
                        "results": results
                    }, indent=2, default=str)

            except Exception as e:
                logger.error(f"Error searching knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error searching knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to search knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_get_knowledge",
            description="Retrieve a specific knowledge entry by its ID when you need exact information that was previously stored."
        )
        async def get_knowledge(params: GetKnowledgeInput, ctx: Context) -> str:
            """
            Retrieve a specific knowledge entry by ID.

            Args:
                params (GetKnowledgeInput): Input parameters containing:
                    - knowledge_id (int): ID of the knowledge entry to retrieve
                    - response_format (ResponseFormat): Output format

            Returns:
                str: Retrieved knowledge entry or error message.
            """
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

            try:
                knowledge = knowledge_client.get_knowledge_by_id(params.knowledge_id)
                
                if not knowledge:
                    if params.response_format == ResponseFormat.MARKDOWN:
                        return f"*Knowledge entry with ID {params.knowledge_id} not found*"
                    else:
                        return json.dumps({
                            "success": False,
                            "error": f"Knowledge entry with ID {params.knowledge_id} not found",
                            "message": "Knowledge entry not found"
                        }, indent=2)
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    lines = [f"# Knowledge Entry Details (ID: {knowledge['id']})", ""]
                    lines.append(f"**Title**: {knowledge['title']}")
                    lines.append(f"**Type**: {knowledge['type']}")
                    lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                    if knowledge['tags']:
                        lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                    if knowledge['language']:
                        lines.append(f"**Language**: {knowledge['language']}")
                    if knowledge['source']:
                        lines.append(f"**Source**: {knowledge['source']}")
                    lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                    lines.append(f"**Created**: {knowledge['created_at']}")
                    lines.append(f"**Updated**: {knowledge['updated_at']}")
                    if knowledge['metadata']:
                        lines.append(f"**Metadata**: ```json\n{json.dumps(knowledge['metadata'], indent=2)}\n```")
                    lines.append("")
                    lines.append("**Content**:")
                    if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                        lines.append(format_code_block(knowledge['content'], knowledge['language']))
                    else:
                        lines.append(f"```\n{knowledge['content']}\n```")
                    return "\n".join(lines)
                
                else:
                    return json.dumps(knowledge, indent=2, default=str)

            except Exception as e:
                logger.error(f"Error retrieving knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error retrieving knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to retrieve knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_list_knowledge",
            description="Browse all stored knowledge entries with filtering and pagination to understand what information is available in your knowledge base."
        )
        async def list_knowledge(params: ListKnowledgeInput, ctx: Context) -> str:
            """
            List knowledge entries with filtering and pagination.

            Args:
                params (ListKnowledgeInput): Input parameters containing:
                    - types (Optional[List[KnowledgeType]]): Filter by knowledge types
                    - categories (Optional[List[str]]): Filter by categories
                    - limit (int): Maximum number of knowledge entries to return
                    - offset (int): Number of knowledge entries to skip (for pagination)
                    - response_format (ResponseFormat): Output format

            Returns:
                str: List of knowledge entries or error message.
            """
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

            try:
                results = knowledge_client.list_knowledge(
                    types=params.types,
                    categories=params.categories,
                    limit=params.limit,
                    offset=params.offset
                )
                total_count = knowledge_client.get_knowledge_count(
                    types=params.types,
                    categories=params.categories
                )
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    if not results:
                        return "*No knowledge entries found*"
                    
                    lines = ["# Knowledge Base Entries", ""]
                    lines.append(f"Showing entries {params.offset + 1} to {min(params.offset + params.limit, total_count)} of {total_count}")
                    if params.types:
                        lines.append(f"Types: {', '.join(params.types)}")
                    if params.categories:
                        lines.append(f"Categories: {', '.join(params.categories)}")
                    lines.append("")
                    
                    headers = ["ID", "Type", "Category", "Title", "Language", "Created"]
                    table_rows = []
                    
                    for knowledge in results:
                        row = [
                            knowledge['id'],
                            knowledge['type'],
                            knowledge['category'] or 'N/A',
                            knowledge['title'][:40] + "..." if len(knowledge['title']) > 40 else knowledge['title'],
                            knowledge['language'] or 'N/A',
                            knowledge['created_at']
                        ]
                        table_rows.append(row)
                    
                    lines.append(format_markdown_table(headers, table_rows))
                    return "\n".join(str(line) for line in lines)
                
                else:
                    return json.dumps({
                        "total_count": total_count,
                        "offset": params.offset,
                        "limit": params.limit,
                        "filters": {
                            "types": params.types,
                            "categories": params.categories
                        },
                        "results": results
                    }, indent=2, default=str)

            except Exception as e:
                logger.error(f"Error listing knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error listing knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to list knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_get_statistics",
            description="Get statistics about the knowledge base including total counts, categories, tags, and languages available."
        )
        async def get_statistics(params: GetStatisticsInput, ctx: Context) -> str:
            """
            Get statistics about the knowledge base.

            Args:
                params (GetStatisticsInput): Input parameters containing:
                    - response_format (ResponseFormat): Output format

            Returns:
                str: Knowledge base statistics.
            """
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()

            try:
                total_count = knowledge_client.get_knowledge_count()
                categories = knowledge_client.get_categories()
                tags = knowledge_client.get_tags()
                languages = knowledge_client.get_languages()
                
                # Count by type
                type_counts = {}
                for knowledge_type in ["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]:
                    count = knowledge_client.get_knowledge_count(types=[knowledge_type])
                    if count > 0:
                        type_counts[knowledge_type] = count
                
                stats = {
                    "total_entries": total_count,
                    "type_distribution": type_counts,
                    "categories": categories,
                    "tags": tags,
                    "languages": languages,
                    "database_path": knowledge_client.config.database_path
                }
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    lines = ["# Knowledge Base Statistics", ""]
                    lines.append(f"**Total Entries**: {total_count}")
                    lines.append("")
                    lines.append("## Type Distribution")
                    for knowledge_type, count in type_counts.items():
                        lines.append(f"- **{knowledge_type.replace('_', ' ').title()}**: {count}")
                    lines.append("")
                    lines.append(f"## Categories ({len(categories)})")
                    if categories:
                        lines.append(", ".join(f"`{cat}`" for cat in categories))
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"## Tags ({len(tags)})")
                    if tags:
                        lines.append(", ".join(f"`{tag}`" for tag in tags[:20]))  # Show first 20
                        if len(tags) > 20:
                            lines.append(f"... and {len(tags) - 20} more")
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"## Languages ({len(languages)})")
                    if languages:
                        lines.append(", ".join(f"`{lang}`" for lang in languages))
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"**Database Path**: `{knowledge_client.config.database_path}`")
                    
                    return "\n".join(lines)
                
                else:
                    return json.dumps(stats, indent=2)

            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error getting statistics**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to get statistics"
                    }, indent=2)
        
        mcp.run(transport="sse")
    else:
        mcp = FastMCP("kb_search_mcp", lifespan=app_lifespan)
        
        # Register all search tools here (same as above)
        @mcp.tool(
            name="kb_search_knowledge",
            description="Search the knowledge base using natural language queries with advanced filtering options for business knowledge, code snippets, and documentation."
        )
        async def search_knowledge(params: SearchKnowledgeInput, ctx: Context) -> str:
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()
            try:
                results = knowledge_client.search_knowledge(
                    query=params.query,
                    types=params.types,
                    categories=params.categories,
                    languages=params.languages,
                    tags=params.tags,
                    limit=params.limit
                )
                if params.response_format == ResponseFormat.MARKDOWN:
                    if not results:
                        return f"*No knowledge entries found matching query: '{params.query}'*"
                    lines = [f"# Knowledge Search Results for: `{params.query}`", ""]
                    lines.append(f"Found {len(results)} knowledge entr{'y' if len(results) == 1 else 'ies'}")
                    if params.types:
                        lines.append(f"Types: {', '.join(params.types)}")
                    if params.categories:
                        lines.append(f"Categories: {', '.join(params.categories)}")
                    if params.languages:
                        lines.append(f"Languages: {', '.join(params.languages)}")
                    if params.tags:
                        lines.append(f"Tags: {', '.join(params.tags)}")
                    lines.append("")
                    for i, knowledge in enumerate(results, 1):
                        lines.append(f"## {i}. {knowledge['title']} (ID: {knowledge['id']})")
                        lines.append(f"**Type**: {knowledge['type']}")
                        lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                        if knowledge['tags']:
                            lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                        if knowledge['language']:
                            lines.append(f"**Language**: {knowledge['language']}")
                        if knowledge['source']:
                            lines.append(f"**Source**: {knowledge['source']}")
                        lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                        lines.append(f"**Created**: {knowledge['created_at']}")
                        lines.append("")
                        lines.append("**Content**:")
                        if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                            lines.append(format_code_block(knowledge['content'], knowledge['language']))
                        else:
                            lines.append(f"```\n{knowledge['content']}\n```")
                        lines.append("")
                    return "\n".join(lines)
                else:
                    return json.dumps({
                        "query": params.query,
                        "filters": {
                            "types": params.types,
                            "categories": params.categories,
                            "languages": params.languages,
                            "tags": params.tags
                        },
                        "count": len(results),
                        "results": results
                    }, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error searching knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error searching knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to search knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_get_knowledge",
            description="Retrieve a specific knowledge entry by its ID when you need exact information that was previously stored."
        )
        async def get_knowledge(params: GetKnowledgeInput, ctx: Context) -> str:
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()
            try:
                knowledge = knowledge_client.get_knowledge_by_id(params.knowledge_id)
                if not knowledge:
                    if params.response_format == ResponseFormat.MARKDOWN:
                        return f"*Knowledge entry with ID {params.knowledge_id} not found*"
                    else:
                        return json.dumps({
                            "success": False,
                            "error": f"Knowledge entry with ID {params.knowledge_id} not found",
                            "message": "Knowledge entry not found"
                        }, indent=2)
                if params.response_format == ResponseFormat.MARKDOWN:
                    lines = [f"# Knowledge Entry Details (ID: {knowledge['id']})", ""]
                    lines.append(f"**Title**: {knowledge['title']}")
                    lines.append(f"**Type**: {knowledge['type']}")
                    lines.append(f"**Category**: {knowledge['category'] or 'N/A'}")
                    if knowledge['tags']:
                        lines.append(f"**Tags**: {', '.join(knowledge['tags'])}")
                    if knowledge['language']:
                        lines.append(f"**Language**: {knowledge['language']}")
                    if knowledge['source']:
                        lines.append(f"**Source**: {knowledge['source']}")
                    lines.append(f"**Confidence**: {knowledge['confidence']:.2f}")
                    lines.append(f"**Created**: {knowledge['created_at']}")
                    lines.append(f"**Updated**: {knowledge['updated_at']}")
                    if knowledge['metadata']:
                        lines.append(f"**Metadata**: ```json\n{json.dumps(knowledge['metadata'], indent=2)}\n```")
                    lines.append("")
                    lines.append("**Content**:")
                    if knowledge['type'] == "code_snippet" and knowledge.get('language'):
                        lines.append(format_code_block(knowledge['content'], knowledge['language']))
                    else:
                        lines.append(f"```\n{knowledge['content']}\n```")
                    return "\n".join(lines)
                else:
                    return json.dumps(knowledge, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error retrieving knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error retrieving knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to retrieve knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_list_knowledge",
            description="Browse all stored knowledge entries with filtering and pagination to understand what information is available in your knowledge base."
        )
        async def list_knowledge(params: ListKnowledgeInput, ctx: Context) -> str:
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()
            try:
                results = knowledge_client.list_knowledge(
                    types=params.types,
                    categories=params.categories,
                    limit=params.limit,
                    offset=params.offset
                )
                total_count = knowledge_client.get_knowledge_count(
                    types=params.types,
                    categories=params.categories
                )
                if params.response_format == ResponseFormat.MARKDOWN:
                    if not results:
                        return "*No knowledge entries found*"
                    lines = ["# Knowledge Base Entries", ""]
                    lines.append(f"Showing entries {params.offset + 1} to {min(params.offset + params.limit, total_count)} of {total_count}")
                    if params.types:
                        lines.append(f"Types: {', '.join(params.types)}")
                    if params.categories:
                        lines.append(f"Categories: {', '.join(params.categories)}")
                    lines.append("")
                    headers = ["ID", "Type", "Category", "Title", "Language", "Created"]
                    table_rows = []
                    for knowledge in results:
                        row = [
                            knowledge['id'],
                            knowledge['type'],
                            knowledge['category'] or 'N/A',
                            knowledge['title'][:40] + "..." if len(knowledge['title']) > 40 else knowledge['title'],
                            knowledge['language'] or 'N/A',
                            knowledge['created_at']
                        ]
                        table_rows.append(row)
                    lines.append(format_markdown_table(headers, table_rows))
                    return "\n".join(str(line) for line in lines)
                else:
                    return json.dumps({
                        "total_count": total_count,
                        "offset": params.offset,
                        "limit": params.limit,
                        "filters": {
                            "types": params.types,
                            "categories": params.categories
                        },
                        "results": results
                    }, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error listing knowledge: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error listing knowledge**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to list knowledge"
                    }, indent=2)
        
        @mcp.tool(
            name="kb_get_statistics",
            description="Get statistics about the knowledge base including total counts, categories, tags, and languages available."
        )
        async def get_statistics(params: GetStatisticsInput, ctx: Context) -> str:
            knowledge_client: KnowledgeSearchClient = get_knowledge_search_client()
            try:
                total_count = knowledge_client.get_knowledge_count()
                categories = knowledge_client.get_categories()
                tags = knowledge_client.get_tags()
                languages = knowledge_client.get_languages()
                type_counts = {}
                for knowledge_type in ["business_knowledge", "code_snippet", "documentation", "faq", "best_practice"]:
                    count = knowledge_client.get_knowledge_count(types=[knowledge_type])
                    if count > 0:
                        type_counts[knowledge_type] = count
                stats = {
                    "total_entries": total_count,
                    "type_distribution": type_counts,
                    "categories": categories,
                    "tags": tags,
                    "languages": languages,
                    "database_path": knowledge_client.config.database_path
                }
                if params.response_format == ResponseFormat.MARKDOWN:
                    lines = ["# Knowledge Base Statistics", ""]
                    lines.append(f"**Total Entries**: {total_count}")
                    lines.append("")
                    lines.append("## Type Distribution")
                    for knowledge_type, count in type_counts.items():
                        lines.append(f"- **{knowledge_type.replace('_', ' ').title()}**: {count}")
                    lines.append("")
                    lines.append(f"## Categories ({len(categories)})")
                    if categories:
                        lines.append(", ".join(f"`{cat}`" for cat in categories))
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"## Tags ({len(tags)})")
                    if tags:
                        lines.append(", ".join(f"`{tag}`" for tag in tags[:20]))
                        if len(tags) > 20:
                            lines.append(f"... and {len(tags) - 20} more")
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"## Languages ({len(languages)})")
                    if languages:
                        lines.append(", ".join(f"`{lang}`" for lang in languages))
                    else:
                        lines.append("None")
                    lines.append("")
                    lines.append(f"**Database Path**: `{knowledge_client.config.database_path}`")
                    return "\n".join(lines)
                else:
                    return json.dumps(stats, indent=2)
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                if params.response_format == ResponseFormat.MARKDOWN:
                    return f"❌ **Error getting statistics**: {str(e)}"
                else:
                    return json.dumps({
                        "success": False,
                        "error": str(e),
                        "message": "Failed to get statistics"
                    }, indent=2)
        
        mcp.run(transport="stdio")