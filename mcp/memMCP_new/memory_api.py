#!/usr/bin/env python3
"""
Memory MCP HTTP API - 独立的HTTP接口用于管理记忆内容

这个脚本提供了一个简单的RESTful API来查询、删除和管理
Memory MCP Server中存储的记忆内容，无需通过MCP协议。
"""

import os
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from fastapi.responses import JSONResponse

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Memory MCP HTTP API",
    description="独立的HTTP接口用于查询和管理Memory MCP Server的记忆内容",
    version="1.0.0"
)

# Add CORS middleware to allow requests from any origin (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Configuration ====================

class APIConfig:
    """API configuration."""
    DATABASE_PATH: str = os.getenv("KNOWLEDGE_DB_PATH", "knowledge.db")
    MAX_LIMIT: int = 1000  # Maximum number of records to return in a single request


# ==================== Database Client ====================

class MemoryAPIClient:
    """Database client for memory operations via HTTP API."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            if conn:
                conn.close()

    def list_memories(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List memories with pagination."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, content, type, category, tags, language, source, confidence, created_at, updated_at, metadata
                FROM knowledge_entries
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "type": row["type"],
                    "category": row["category"],
                    "tags": json.loads(row["tags"]) if row["tags"] else None,
                    "language": row["language"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                results.append(result)
            
            return results

    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories using FTS5 if available, otherwise basic LIKE search."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if FTS5 table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries_fts'")
            fts_available = cursor.fetchone() is not None
            
            if fts_available:
                # Use FTS5 full-text search
                cursor.execute(
                    """
                    SELECT k.id, k.title, k.content, k.type, k.category, k.tags, k.language, k.source, k.confidence, k.created_at, k.updated_at, k.metadata
                    FROM knowledge_entries k
                    JOIN knowledge_entries_fts fts ON k.id = fts.rowid
                    WHERE knowledge_entries_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit)
                )
            else:
                # Use basic LIKE search
                cursor.execute(
                    """
                    SELECT id, title, content, type, category, tags, language, source, confidence, created_at, updated_at, metadata
                    FROM knowledge_entries
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", limit)
                )
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "type": row["type"],
                    "category": row["category"],
                    "tags": json.loads(row["tags"]) if row["tags"] else None,
                    "language": row["language"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                results.append(result)
            
            return results

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, content, type, category, tags, language, source, confidence, created_at, updated_at, metadata FROM knowledge_entries WHERE id = ?",
                (memory_id,)
            )
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "type": row["type"],
                    "category": row["category"],
                    "tags": json.loads(row["tags"]) if row["tags"] else None,
                    "language": row["language"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
            return None

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_entries WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def delete_all_memories(self) -> int:
        """Delete all memories and return count of deleted records."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries")
            count = cursor.fetchone()["count"]
            cursor.execute("DELETE FROM knowledge_entries")
            conn.commit()
            return count

    def get_memory_count(self) -> int:
        """Get total number of stored memories."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries")
            result = cursor.fetchone()
            return result["count"] if result else 0

    def store_memory(self, title: str, content: str, type: str = "business_knowledge", category: Optional[str] = None, tags: Optional[List[str]] = None, language: Optional[str] = None, source: Optional[str] = None, confidence: float = 1.0) -> int:
        """Store a new memory (for testing purposes)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            tags_str = json.dumps(tags) if tags else None
            cursor.execute(
                "INSERT INTO knowledge_entries (title, content, type, category, tags, language, source, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, content, type, category, tags_str, language, source, confidence)
            )
            memory_id = cursor.lastrowid
            if memory_id is None:
                raise RuntimeError("Failed to get memory ID after insertion")
            conn.commit()
            return memory_id


# Initialize database client
db_client = MemoryAPIClient(APIConfig.DATABASE_PATH)


# ==================== Pydantic Models ====================

class MemoryBase(BaseModel):
    """Base model for memory operations."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)


class MemoryCreate(MemoryBase):
    """Model for creating memories."""
    title: str = Field(
        ...,
        description="Descriptive title for the knowledge entry",
        min_length=1,
        max_length=200
    )
    content: str = Field(
        ...,
        description="Complete content to store as long-term memory",
        min_length=1
    )
    type: str = Field(
        default="business_knowledge",
        description="Type of knowledge: business_knowledge, code_snippet, documentation, faq, or best_practice"
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional category to organize memories"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags to categorize and filter memories"
    )
    language: Optional[str] = Field(
        default=None,
        description="Programming language for code snippets"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the knowledge (URL, file path, etc.)"
    )


class MemoryResponse(MemoryBase):
    """Model for memory responses."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    id: int
    title: str
    content: str
    type: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class MemoryListResponse(MemoryBase):
    """Model for listing memories."""
    total_count: int
    offset: int
    limit: int
    results: List[MemoryResponse]


class DeleteResponse(MemoryBase):
    """Model for delete operations."""
    success: bool
    message: str
    deleted_count: int = 0


# ==================== API Routes ====================

@app.get("/", summary="API Health Check", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        count = db_client.get_memory_count()
        return {
            "status": "healthy",
            "database_path": APIConfig.DATABASE_PATH,
            "total_memories": count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/memories", response_model=MemoryListResponse, summary="List All Memories", tags=["Memories"])
async def list_memories(
    limit: int = Query(10, ge=1, le=APIConfig.MAX_LIMIT, description="Maximum number of memories to return"),
    offset: int = Query(0, ge=0, description="Number of memories to skip (for pagination)")
):
    """
    List all stored memories with pagination.
    
    This endpoint returns memories sorted by creation date (newest first).
    """
    try:
        memories = db_client.list_memories(limit=limit, offset=offset)
        total_count = db_client.get_memory_count()
        
        return MemoryListResponse(
            total_count=total_count,
            offset=offset,
            limit=min(limit, total_count - offset),
            results=[
                MemoryResponse(
                    id=mem["id"],
                    title=mem["title"],
                    content=mem["content"],
                    type=mem["type"],
                    category=mem["category"],
                    tags=mem["tags"],
                    language=mem["language"],
                    source=mem["source"],
                    confidence=mem["confidence"],
                    metadata=mem["metadata"],
                    created_at=mem["created_at"],
                    updated_at=mem["updated_at"]
                )
                for mem in memories
            ]
        )
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list memories")


@app.get("/memories/search", response_model=MemoryListResponse, summary="Search Memories", tags=["Memories"])
async def search_memories(
    query: str = Query(..., min_length=1, description="Search query to find relevant memories"),
    limit: int = Query(10, ge=1, le=APIConfig.MAX_LIMIT, description="Maximum number of results to return")
):
    """
    Search memories using full-text search.
    
    Uses SQLite FTS5 for efficient natural language search when available,
    otherwise falls back to basic LIKE pattern matching.
    """
    try:
        memories = db_client.search_memories(query=query, limit=limit)
        total_count = len(memories)  # Note: This is the count of search results, not total memories
        
        return MemoryListResponse(
            total_count=total_count,
            offset=0,
            limit=min(limit, total_count),
            results=[
                MemoryResponse(
                    id=mem["id"],
                    title=mem["title"],
                    content=mem["content"],
                    type=mem["type"],
                    category=mem["category"],
                    tags=mem["tags"],
                    language=mem["language"],
                    source=mem["source"],
                    confidence=mem["confidence"],
                    metadata=mem["metadata"],
                    created_at=mem["created_at"],
                    updated_at=mem["updated_at"]
                )
                for mem in memories
            ]
        )
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail="Failed to search memories")


@app.get("/memories/{memory_id}", response_model=MemoryResponse, summary="Get Memory by ID", tags=["Memories"])
async def get_memory(
    memory_id: int = Path(..., ge=1, description="ID of the memory to retrieve")
):
    """
    Retrieve a specific memory by its ID.
    
    Returns detailed information about the memory including content, metadata, and timestamps.
    """
    try:
        memory = db_client.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
        
        return MemoryResponse(
            id=memory["id"],
            title=memory["title"],
            content=memory["content"],
            type=memory["type"],
            category=memory["category"],
            tags=memory["tags"],
            language=memory["language"],
            source=memory["source"],
            confidence=memory["confidence"],
            metadata=memory["metadata"],
            created_at=memory["created_at"],
            updated_at=memory["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory")


@app.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED, summary="Store New Memory", tags=["Memories"])
async def create_memory(memory: MemoryCreate):
    """
    Store a new memory entry.
    
    This endpoint is primarily for testing and debugging purposes.
    In production, memories should be stored through the MCP protocol.
    """
    try:
        memory_id = db_client.store_memory(
            title=memory.title,
            content=memory.content,
            type=memory.type,
            category=memory.category,
            tags=memory.tags,
            language=memory.language,
            source=memory.source,
            confidence=getattr(memory, 'confidence', 1.0)
        )
        stored_memory = db_client.get_memory_by_id(memory_id)
        
        if not stored_memory:
            raise HTTPException(status_code=500, detail="Failed to retrieve stored memory")
        
        return MemoryResponse(
            id=stored_memory["id"],
            title=stored_memory["title"],
            content=stored_memory["content"],
            type=stored_memory["type"],
            category=stored_memory["category"],
            tags=stored_memory["tags"],
            language=stored_memory["language"],
            source=stored_memory["source"],
            confidence=stored_memory["confidence"],
            metadata=stored_memory.get("metadata"),
            created_at=stored_memory["created_at"],
            updated_at=stored_memory["updated_at"]
        )
    except Exception as e:
        logger.error(f"Error storing memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@app.delete("/memories/{memory_id}", response_model=DeleteResponse, summary="Delete Memory by ID", tags=["Memories"])
async def delete_memory(
    memory_id: int = Path(..., ge=1, description="ID of the memory to delete")
):
    """
    Delete a specific memory by its ID.
    
    Returns success status and confirmation message.
    """
    try:
        success = db_client.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
        
        return DeleteResponse(
            success=True,
            message=f"Memory {memory_id} deleted successfully",
            deleted_count=1
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete memory")


@app.delete("/memories", response_model=DeleteResponse, summary="Delete All Memories", tags=["Memories"])
async def delete_all_memories():
    """
    Delete all stored memories.
    
    **WARNING**: This operation cannot be undone. Use with caution.
    Returns the count of deleted memories.
    """
    try:
        deleted_count = db_client.delete_all_memories()
        return DeleteResponse(
            success=True,
            message=f"All {deleted_count} memories deleted successfully",
            deleted_count=deleted_count
        )
    except Exception as e:
        logger.error(f"Error deleting all memories: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete all memories")


# ==================== Statistics Endpoint ====================

@app.get("/stats", summary="Get Memory Statistics", tags=["Statistics"])
async def get_statistics():
    """
    Get statistics about the memory database.
    
    Returns total count, database size, and other useful metrics.
    """
    try:
        total_count = db_client.get_memory_count()
        
        # Get database file size
        db_size = 0
        if os.path.exists(APIConfig.DATABASE_PATH):
            db_size = os.path.getsize(APIConfig.DATABASE_PATH)
        
        return {
            "total_memories": total_count,
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2) if db_size > 0 else 0,
            "database_path": APIConfig.DATABASE_PATH,
            "max_limit_per_request": APIConfig.MAX_LIMIT
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Memory MCP HTTP API Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8325,
        help="Port to listen on (default: 8325)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Memory MCP HTTP API Server on http://{args.host}:{args.port}")
    print(f"Database path: {APIConfig.DATABASE_PATH}")
    print("\nAvailable endpoints:")
    print("  GET    /                    - Health check")
    print("  GET    /memories           - List all memories")
    print("  GET    /memories/search    - Search memories")
    print("  GET    /memories/{id}      - Get specific memory")
    print("  POST   /memories           - Store new memory")
    print("  DELETE /memories/{id}      - Delete specific memory") 
    print("  DELETE /memories           - Delete all memories")
    print("  GET    /stats              - Get statistics")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "memory_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )