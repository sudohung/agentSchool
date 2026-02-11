#!/usr/bin/env python3
"""
MySQL MCP Server for Business Data Analysis

This MCP server connects to a MySQL database and provides tools to explore
database structure, relationships, and data to understand business patterns.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, TypedDict
from enum import Enum
from contextlib import asynccontextmanager
import pymysql
import pymysql.cursors

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("mysql_mcp")


# ==================== Configuration ====================

class ConnectionConfig(BaseModel):
    """MySQL connection configuration."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    host: str = Field(default="localhost", description="MySQL server hostname")
    port: int = Field(default=3306, description="MySQL server port", ge=1, le=65535)
    user: str = Field(..., description="MySQL username")
    password: str = Field(default="", description="MySQL password")
    database: Optional[str] = Field(default=None, description="Default database to use")
    charset: str = Field(default="utf8mb4", description="Character set")


# ==================== Shared Database Client ====================

class DatabaseClient:
    """Shared MySQL client for connection pooling."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection = None
    
    def connect(self):
        """Establish MySQL connection"""
        if self.connection is None:
            password = self.config.password if self.config.password else ""
            self.connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=password,
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=pymysql.cursors.DictCursor
            )

    async def connect(self):
        """Establish connection to MySQL."""
        if self.connection is None or not self.connection.open:
            self.connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            logger.info(f"Connected to MySQL: {self.config.host}:{self.config.port}")

    async def close(self):
        """Close MySQL connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("MySQL connection closed")

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        await self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except pymysql.Error as e:
            logger.error(f"Query error: {e}")
            raise


# ==================== Lifespan Management ====================

# Global database client instance
_db_client: Optional[DatabaseClient] = None

def get_db_client() -> DatabaseClient:
    """Get the global database client instance."""
    if _db_client is None:
        raise RuntimeError("Database client not initialized")
    return _db_client

@asynccontextmanager
async def app_lifespan(app):
    """Manage database client lifecycle."""
    global _db_client
    
    # Load configuration from environment or use defaults
    config = ConnectionConfig(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE"),
        charset=os.getenv("MYSQL_CHARSET", "utf8mb4")
    )

    _db_client = DatabaseClient(config)
    yield {"db": _db_client}

    # Cleanup
    await _db_client.close()
    _db_client = None


# Parse command line arguments early to get host/port
import argparse

parser = argparse.ArgumentParser(description="MySQL MCP Server")
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
    default=8000,
    help="HTTP port (default: 8000)"
)

args = parser.parse_args()

# Reinitialize MCP with lifespan and host/port
mcp = FastMCP("mysql_mcp", lifespan=app_lifespan, host=args.host, port=args.port)


# ==================== Enums and Response Models ====================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class DatabaseInfo(TypedDict):
    """Database information structure."""
    name: str
    table_count: int
    size_mb: float


class TableInfo(TypedDict):
    """Table information structure."""
    name: str
    engine: str
    rows: int
    size_mb: float
    comment: Optional[str]


class ColumnInfo(TypedDict):
    """Column information structure."""
    name: str
    type: str
    nullable: bool
    key: str
    default: Optional[str]
    extra: str
    comment: Optional[str]


class ForeignKeyInfo(TypedDict):
    """Foreign key information structure."""
    constraint_name: str
    column_name: str
    referenced_table: str
    referenced_column: str


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


def truncate_value(value: Any, max_length: int = 100) -> str:
    """Truncate long values for display."""
    str_value = str(value) if value is not None else "NULL"
    if len(str_value) > max_length:
        return str_value[:max_length] + "..."
    return str_value


# ==================== Tool: List Databases ====================

class ListDatabasesInput(BaseModel):
    """Input for listing databases."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    filter_pattern: Optional[str] = Field(
        default=None,
        description="Optional SQL LIKE pattern to filter database names (e.g., '%prod%', 'myapp_%')"
    )
    include_system: bool = Field(
        default=False,
        description="Whether to include system databases (mysql, information_schema, performance_schema, sys)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_list_databases",
    annotations={
        "title": "List MySQL Databases",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_databases(params: ListDatabasesInput, ctx: Context) -> str:
    """
    List all available databases on the MySQL server.

    Args:
        params (ListDatabasesInput): Input parameters containing:
            - filter_pattern (Optional[str]): SQL LIKE pattern to filter names
            - include_system (bool): Include system databases (default: False)
            - response_format (ResponseFormat): Output format (markdown/json)

    Returns:
        str: Formatted list of databases with metadata.
    """
    db: DatabaseClient = get_db_client()

    try:
        # Build query
        query = """
            SELECT
                SCHEMA_NAME as database_name,
                DEFAULT_CHARACTER_SET_NAME as charset,
                DEFAULT_COLLATION_NAME as collation
            FROM INFORMATION_SCHEMA.SCHEMATA
        """

        where_clauses = []
        params_list = []

        if not params.include_system:
            where_clauses.append(
                "SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')"
            )

        if params.filter_pattern:
            where_clauses.append("SCHEMA_NAME LIKE %s")
            params_list.append(params.filter_pattern)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY SCHEMA_NAME"

        results = await db.execute_query(query, tuple(params_list))

        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return "*No databases found matching the criteria*"

            lines = ["# Available Databases", ""]
            lines.append(f"Found {len(results)} database(s)")
            lines.append("")

            for db_info in results:
                lines.append(f"## `{db_info['database_name']}`")
                lines.append(f"- **Charset**: {db_info['charset']}")
                lines.append(f"- **Collation**: {db_info['collation']}")
                lines.append("")

            return "\n".join(lines)

        else:
            return json.dumps({
                "count": len(results),
                "databases": results
            }, indent=2)

    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return f"Error: Failed to list databases: {str(e)}"


# ==================== Tool: Database Overview ====================

class DatabaseOverviewInput(BaseModel):
    """Input for database overview."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    include_table_count: bool = Field(
        default=True,
        description="Whether to include table count in the overview"
    )
    include_size: bool = Field(
        default=True,
        description="Whether to include database size information"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_database_overview",
    annotations={
        "title": "Database Overview",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def database_overview(params: DatabaseOverviewInput, ctx: Context) -> str:
    """
    Get comprehensive overview of a database including table count and size.

    Args:
        params (DatabaseOverviewInput): Input parameters containing:
            - database (Optional[str]): Database name
            - include_table_count (bool): Include table count
            - include_size (bool): Include size info
            - response_format (ResponseFormat): Output format

    Returns:
        str: Database overview information.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        info_parts = []

        # Get basic info
        basic_info = await db.execute_query("""
            SELECT
                SCHEMA_NAME as name,
                DEFAULT_CHARACTER_SET_NAME as charset,
                DEFAULT_COLLATION_NAME as collation,
                SCHEMA_COMMENT as comment
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = %s
        """, (target_db,))

        if not basic_info:
            return f"Error: Database '{target_db}' not found"

        info = basic_info[0]
        info_parts.append(info)

        # Get table count
        if params.include_table_count:
            table_count_result = await db.execute_query("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """, (target_db,))
            info["table_count"] = table_count_result[0]["count"]

        # Get size
        if params.include_size:
            size_result = await db.execute_query("""
                SELECT
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb,
                    ROUND(SUM(data_length) / 1024 / 1024, 2) as data_mb,
                    ROUND(SUM(index_length) / 1024 / 1024, 2) as index_mb
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
            """, (target_db,))
            size_info = size_result[0]
            info["size_mb"] = size_info["size_mb"]
            info["data_mb"] = size_info["data_mb"]
            info["index_mb"] = size_info["index_mb"]

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Database: `{target_db}`", ""]
            lines.append(f"**Charset**: {info.get('charset')}")
            lines.append(f"**Collation**: {info.get('collation')}")
            if info.get('comment'):
                lines.append(f"**Comment**: {info.get('comment')}")
            lines.append("")

            if params.include_table_count:
                lines.append(f"**Tables**: {info.get('table_count', 0)} tables")
            if params.include_size:
                lines.append(f"**Total Size**: {info.get('size_mb', 0)} MB")
                lines.append(f"  - Data: {info.get('data_mb', 0)} MB")
                lines.append(f"  - Index: {info.get('index_mb', 0)} MB")

            return "\n".join(lines)

        else:
            return json.dumps(info, indent=2)

    except Exception as e:
        logger.error(f"Error getting database overview: {e}")
        return f"Error: Failed to get database overview: {str(e)}"


# ==================== Tool: List Tables ====================

class ListTablesInput(BaseModel):
    """Input for listing tables."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    table_pattern: Optional[str] = Field(
        default=None,
        description="SQL LIKE pattern to filter table names (e.g., '%user%', 'order_%')"
    )
    include_views: bool = Field(
        default=False,
        description="Whether to include views (default: only base tables)"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of tables to return",
        ge=1,
        le=1000
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_list_tables",
    annotations={
        "title": "List Database Tables",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_tables(params: ListTablesInput, ctx: Context) -> str:
    """
    List all tables (and optionally views) in a database.

    Args:
        params (ListTablesInput): Input parameters containing:
            - database (Optional[str]): Database name
            - table_pattern (Optional[str]): SQL LIKE pattern to filter
            - include_views (bool): Include views
            - limit (Optional[int]): Maximum results
            - response_format (ResponseFormat): Output format

    Returns:
        str: Formatted list of tables with metadata.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        # Build query
        table_types = "'BASE TABLE', 'VIEW'" if params.include_views else "'BASE TABLE'"

        query = f"""
            SELECT
                TABLE_NAME as name,
                TABLE_TYPE as type,
                ENGINE as engine,
                TABLE_ROWS as rows,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb,
                TABLE_COMMENT as comment
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE IN ({table_types})
        """

        params_list = [target_db]

        if params.table_pattern:
            query += " AND TABLE_NAME LIKE %s"
            params_list.append(params.table_pattern)

        query += " ORDER BY TABLE_NAME"

        if params.limit:
            query += f" LIMIT {params.limit}"

        results = await db.execute_query(query, tuple(params_list))

        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return "*No tables found matching the criteria*"

            lines = [f"# Tables in `{target_db}`", ""]
            lines.append(f"Found {len(results)} table(s)")
            lines.append("")

            # Create markdown table
            headers = ["Table Name", "Type", "Engine", "Rows", "Size (MB)", "Comment"]
            table_rows = []

            for table in results:
                row = [
                    f"`{table['name']}`",
                    table['type'],
                    table['engine'] or "N/A",
                    f"{table['rows']:,}" if table['rows'] else "N/A",
                    table['size_mb'] or 0,
                    table['comment'] or ""
                ]
                table_rows.append(row)

            lines.append(format_markdown_table(headers, table_rows))
            lines.append("")

            # Add summary
            total_tables = len([t for t in results if t['type'] == 'BASE TABLE'])
            total_views = len([t for t in results if t['type'] == 'VIEW'])
            total_size = sum(t['size_mb'] or 0 for t in results if t['type'] == 'BASE TABLE')

            lines.append("**Summary**")
            lines.append(f"- Base Tables: {total_tables}")
            if params.include_views:
                lines.append(f"- Views: {total_views}")
            lines.append(f"- Total Size: {total_size:.2f} MB")

            return "\n".join(str(line) for line in lines)

        else:
            return json.dumps({
                "database": target_db,
                "count": len(results),
                "tables": results
            }, indent=2)

    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return f"Error: Failed to list tables: {str(e)}"


# ==================== Tool: Get Table Schema ====================

class GetTableSchemaInput(BaseModel):
    """Input for getting table schema."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    table: str = Field(
        ...,
        description="Table name to get schema for",
        min_length=1
    )
    include_indexes: bool = Field(
        default=True,
        description="Whether to include index information"
    )
    include_foreign_keys: bool = Field(
        default=True,
        description="Whether to include foreign key information"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_get_table_schema",
    annotations={
        "title": "Get Table Schema",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_table_schema(params: GetTableSchemaInput, ctx: Context) -> str:
    """
    Get detailed schema information for a table including columns, indexes, and foreign keys.

    Args:
        params (GetTableSchemaInput): Input parameters containing:
            - database (Optional[str]): Database name
            - table (str): Table name
            - include_indexes (bool): Include index info
            - include_foreign_keys (bool): Include foreign key info
            - response_format (ResponseFormat): Output format

    Returns:
        str: Formatted table schema information.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        # Get basic table info
        table_info = await db.execute_query("""
            SELECT
                TABLE_NAME,
                ENGINE,
                TABLE_ROWS,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as size_mb,
                TABLE_COMMENT,
                CREATE_TIME,
                UPDATE_TIME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """, (target_db, params.table))

        if not table_info:
            return f"Error: Table '{params.table}' not found in database '{target_db}'"

        info = table_info[0]

        # Get columns
        columns = await db.execute_query("""
            SELECT
                COLUMN_NAME as name,
                COLUMN_TYPE as type,
                IS_NULLABLE = 'YES' as nullable,
                COLUMN_KEY as key,
                COLUMN_DEFAULT as default,
                EXTRA as extra,
                COLUMN_COMMENT as comment
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (target_db, params.table))

        result = {
            "database": target_db,
            "table": params.table,
            "engine": info["ENGINE"],
            "rows": info["TABLE_ROWS"],
            "size_mb": info["size_mb"],
            "comment": info["TABLE_COMMENT"],
            "columns": columns
        }

        # Get indexes
        if params.include_indexes:
            indexes = await db.execute_query("""
                SELECT
                    INDEX_NAME as name,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    NON_UNIQUE = 0 as is_unique,
                    INDEX_TYPE as type
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                GROUP BY INDEX_NAME, NON_UNIQUE, INDEX_TYPE
                ORDER BY INDEX_NAME
            """, (target_db, params.table))
            result["indexes"] = indexes

        # Get foreign keys
        if params.include_foreign_keys:
            foreign_keys = await db.execute_query("""
                SELECT
                    CONSTRAINT_NAME as constraint_name,
                    COLUMN_NAME as column_name,
                    REFERENCED_TABLE_NAME as referenced_table,
                    REFERENCED_COLUMN_NAME as referenced_column
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                    AND TABLE_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
            """, (target_db, params.table))
            result["foreign_keys"] = foreign_keys

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Table Schema: `{target_db}`.`{params.table}`", ""]

            # Basic info
            lines.append("## Basic Information")
            lines.append(f"- **Engine**: {info['ENGINE']}")
            lines.append(f"- **Rows**: {info['TABLE_ROWS']:,}" if info['TABLE_ROWS'] else "- **Rows**: N/A")
            lines.append(f"- **Size**: {info['size_mb']} MB")
            if info['TABLE_COMMENT']:
                lines.append(f"- **Comment**: {info['TABLE_COMMENT']}")
            lines.append("")

            # Columns
            lines.append("## Columns")
            headers = ["Column", "Type", "Nullable", "Key", "Default", "Extra", "Comment"]
            table_rows = []

            for col in columns:
                row = [
                    f"`{col['name']}`",
                    col['type'],
                    "✓" if col['nullable'] else "✗",
                    col['key'] or "",
                    col['default'] if col['default'] is not None else "NULL",
                    col['extra'],
                    col['comment'] or ""
                ]
                table_rows.append(row)

            lines.append(format_markdown_table(headers, table_rows))
            lines.append("")

            # Indexes
            if params.include_indexes and result.get("indexes"):
                lines.append("## Indexes")
                headers = ["Index Name", "Columns", "Unique", "Type"]
                table_rows = []

                for idx in result["indexes"]:
                    row = [
                        idx['name'],
                        idx['columns'],
                        "✓" if not idx['is_unique'] else "✗",
                        idx['type']
                    ]
                    table_rows.append(row)

                lines.append(format_markdown_table(headers, table_rows))
                lines.append("")

            # Foreign Keys
            if params.include_foreign_keys and result.get("foreign_keys"):
                lines.append("## Foreign Keys")
                headers = ["Constraint", "Column", "References"]
                table_rows = []

                for fk in result["foreign_keys"]:
                    row = [
                        fk['constraint_name'],
                        f"`{fk['column_name']}`",
                        f"`{fk['referenced_table']}`.`{fk['referenced_column']}`"
                    ]
                    table_rows.append(row)

                lines.append(format_markdown_table(headers, table_rows))

            return "\n".join(str(line) for line in lines)

        else:
            return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error getting table schema: {e}")
        return f"Error: Failed to get table schema: {str(e)}"


# ==================== Tool: Sample Table Data ====================

class SampleTableDataInput(BaseModel):
    """Input for sampling table data."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    table: str = Field(
        ...,
        description="Table name to sample data from",
        min_length=1
    )
    limit: int = Field(
        default=10,
        description="Number of rows to sample",
        ge=1,
        le=100
    )
    columns: Optional[str] = Field(
        default=None,
        description="Comma-separated list of columns to select (e.g., 'id,name,email'). If not provided, selects all columns."
    )
    where_clause: Optional[str] = Field(
        default=None,
        description="Optional WHERE clause (without 'WHERE' keyword) for filtering (e.g., 'status=\"active\"'). Only for advanced users."
    )
    order_by: Optional[str] = Field(
        default=None,
        description="Optional ORDER BY clause (without 'ORDER BY' keyword) (e.g., 'created_at DESC')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_sample_table_data",
    annotations={
        "title": "Sample Table Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def sample_table_data(params: SampleTableDataInput, ctx: Context) -> str:
    """
    Sample data from a table to understand its content.

    Args:
        params (SampleTableDataInput): Input parameters containing:
            - database (Optional[str]): Database name
            - table (str): Table name
            - limit (int): Number of rows to sample (default: 10)
            - columns (Optional[str]): Comma-separated column names
            - where_clause (Optional[str]): WHERE clause for filtering
            - order_by (Optional[str]): ORDER BY clause
            - response_format (ResponseFormat): Output format

    Returns:
        str: Sampled table data.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        # Build query
        if params.columns:
            columns_clause = params.columns
        else:
            # Get all columns
            cols = await db.execute_query("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (target_db, params.table))
            columns_clause = ", ".join([f"`{c['COLUMN_NAME']}`" for c in cols])

        query = f"SELECT {columns_clause} FROM `{target_db}`.`{params.table}`"

        if params.where_clause:
            query += f" WHERE {params.where_clause}"

        if params.order_by:
            query += f" ORDER BY {params.order_by}"

        query += f" LIMIT {params.limit}"

        results = await db.execute_query(query)

        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return f"*No data found in table `{params.table}`*"

            lines = [f"# Sample Data: `{target_db}`.`{params.table}`", ""]
            lines.append(f"Showing {len(results)} row(s)")

            # Create markdown table
            headers = list(results[0].keys())
            table_rows = []

            for row in results:
                table_rows.append([truncate_value(row.get(h)) for h in headers])

            lines.append(format_markdown_table(headers, table_rows))

            return "\n".join(str(line) for line in lines)

        else:
            return json.dumps({
                "database": target_db,
                "table": params.table,
                "count": len(results),
                "data": results
            }, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error sampling table data: {e}")
        return f"Error: Failed to sample table data: {str(e)}"


# ==================== Tool: Analyze Table Statistics ====================

class AnalyzeTableStatisticsInput(BaseModel):
    """Input for analyzing table statistics."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    table: str = Field(
        ...,
        description="Table name to analyze",
        min_length=1
    )
    include_column_stats: bool = Field(
        default=True,
        description="Whether to include per-column statistics (null counts, distinct values)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_analyze_table_statistics",
    annotations={
        "title": "Analyze Table Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def analyze_table_statistics(params: AnalyzeTableStatisticsInput, ctx: Context) -> str:
    """
    Analyze table statistics including row counts, null values, and data distribution.

    Args:
        params (AnalyzeTableStatisticsInput): Input parameters containing:
            - database (Optional[str]): Database name
            - table (str): Table name
            - include_column_stats (bool): Include per-column statistics
            - response_format (ResponseFormat): Output format

    Returns:
        str: Table statistics and analysis.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        # Get table info
        table_info = await db.execute_query("""
            SELECT
                TABLE_ROWS as estimated_rows,
                AVG_ROW_LENGTH as avg_row_length,
                DATA_LENGTH,
                INDEX_LENGTH,
                UPDATE_TIME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """, (target_db, params.table))

        if not table_info:
            return f"Error: Table '{params.table}' not found in database '{target_db}'"

        info = table_info[0]
        result = {
            "database": target_db,
            "table": params.table,
            "estimated_rows": info["estimated_rows"],
            "avg_row_length": info["avg_row_length"],
            "data_length": info["DATA_LENGTH"],
            "index_length": info["INDEX_LENGTH"],
            "update_time": info["UPDATE_TIME"]
        }

        # Get exact row count
        exact_count = await db.execute_query(
            f"SELECT COUNT(*) as count FROM `{target_db}`.`{params.table}`"
        )
        result["exact_rows"] = exact_count[0]["count"]

        # Get column statistics
        if params.include_column_stats:
            columns = await db.execute_query("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (target_db, params.table))

            column_stats = []

            for col in columns:
                col_info = {
                    "name": col["COLUMN_NAME"],
                    "data_type": col["DATA_TYPE"],
                    "nullable": col["IS_NULLABLE"] == "YES"
                }

                # Count nulls if nullable
                if col["IS_NULLABLE"] == "YES":
                    null_count_result = await db.execute_query(
                        f"SELECT COUNT(*) as count FROM `{target_db}`.`{params.table}` WHERE `{col['COLUMN_NAME']}` IS NULL"
                    )
                    col_info["null_count"] = null_count_result[0]["count"]
                    col_info["null_percentage"] = round(
                        (col_info["null_count"] / result["exact_rows"] * 100) if result["exact_rows"] > 0 else 0,
                        2
                    )

                # Count distinct values for reasonable data types
                if col["DATA_TYPE"] in ["varchar", "char", "text", "int", "bigint", "tinyint", "smallint", "mediumint"]:
                    distinct_result = await db.execute_query(
                        f"SELECT COUNT(DISTINCT `{col['COLUMN_NAME']}`) as count FROM `{target_db}`.`{params.table}`"
                    )
                    col_info["distinct_count"] = distinct_result[0]["count"]

                column_stats.append(col_info)

            result["column_statistics"] = column_stats

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Table Statistics: `{target_db}`.`{params.table}`", ""]

            # Basic stats
            lines.append("## Basic Statistics")
            lines.append(f"- **Exact Row Count**: {result['exact_rows']:,}")
            lines.append(f"- **Estimated Row Count**: {result['estimated_rows']:,}" if result['estimated_rows'] else "- **Estimated Row Count**: N/A")
            lines.append(f"- **Average Row Length**: {result['avg_row_length']} bytes" if result['avg_row_length'] else "")
            lines.append(f"- **Data Size**: {result['data_length'] / 1024 / 1024:.2f} MB")
            lines.append(f"- **Index Size**: {result['index_length'] / 1024 / 1024:.2f} MB")
            if result['update_time']:
                lines.append(f"- **Last Updated**: {result['update_time']}")
            lines.append("")

            # Column statistics
            if params.include_column_stats and result.get("column_statistics"):
                lines.append("## Column Statistics")
                headers = ["Column", "Type", "Null Count", "Null %", "Distinct"]
                table_rows = []

                for col in result["column_statistics"]:
                    row = [
                        f"`{col['name']}`",
                        col['data_type'],
                        col.get('null_count', 'N/A'),
                        f"{col.get('null_percentage', 0):.2f}%" if 'null_percentage' in col else "N/A",
                        col.get('distinct_count', 'N/A')
                    ]
                    table_rows.append(row)

                lines.append(format_markdown_table(headers, table_rows))

            return "\n".join(str(line) for line in lines)

        else:
            return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error analyzing table statistics: {e}")
        return f"Error: Failed to analyze table statistics: {str(e)}"


# ==================== Tool: List Foreign Key Relationships ====================

class ListForeignKeyRelationshipsInput(BaseModel):
    """Input for listing foreign key relationships."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    table: Optional[str] = Field(
        default=None,
        description="Optional table name to filter relationships for a specific table"
    )
    direction: str = Field(
        default="both",
        description="Direction of relationships: 'outgoing' (tables this table references), 'incoming' (tables that reference this table), or 'both'"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_list_foreign_key_relationships",
    annotations={
        "title": "List Foreign Key Relationships",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_foreign_key_relationships(params: ListForeignKeyRelationshipsInput, ctx: Context) -> str:
    """
    List foreign key relationships to understand table relationships and data model.

    Args:
        params (ListForeignKeyRelationshipsInput): Input parameters containing:
            - database (Optional[str]): Database name
            - table (Optional[str]): Filter by specific table
            - direction (str): 'outgoing', 'incoming', or 'both'
            - response_format (ResponseFormat): Output format

    Returns:
        str: Foreign key relationship information.
    """
    db: DatabaseClient = get_db_client()

    try:
        target_db = params.database or get_db_client().config.database

        if not target_db:
            return "Error: No database specified. Please provide database name or configure default database."

        # Build query
        query = """
            SELECT
                TABLE_NAME as child_table,
                COLUMN_NAME as child_column,
                CONSTRAINT_NAME as constraint_name,
                REFERENCED_TABLE_NAME as parent_table,
                REFERENCED_COLUMN_NAME as parent_column
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
        """

        params_list = [target_db]

        if params.table:
            if params.direction == "outgoing":
                query += " AND TABLE_NAME = %s"
                params_list.append(params.table)
            elif params.direction == "incoming":
                query += " AND REFERENCED_TABLE_NAME = %s"
                params_list.append(params.table)
            else:  # both
                query += " AND (TABLE_NAME = %s OR REFERENCED_TABLE_NAME = %s)"
                params_list.extend([params.table, params.table])

        query += " ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION"

        results = await db.execute_query(query, tuple(params_list))

        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                if params.table:
                    return f"*No foreign key relationships found for table `{params.table}`*"
                return "*No foreign key relationships found in database*"

            lines = [f"# Foreign Key Relationships in `{target_db}`", ""]
            lines.append(f"Found {len(results)} relationship(s)")
            lines.append("")

            # Group by constraint
            from collections import defaultdict
            constraints = defaultdict(list)
            for row in results:
                constraints[row['constraint_name']].append(row)

            for constraint_name, rows in constraints.items():
                first_row = rows[0]
                lines.append(f"## `{constraint_name}`")
                lines.append(f"**{first_row['child_table']}** ⟶ **{first_row['parent_table']}**")
                lines.append("")

                for row in rows:
                    lines.append(f"- `{row['child_column']}` ⟶ `{row['parent_column']}`")
                lines.append("")

            # Summary
            child_tables = set(r['child_table'] for r in results)
            parent_tables = set(r['parent_table'] for r in results)
            lines.append("---")
            lines.append("**Summary**")
            lines.append(f"- Child Tables (referencing): {len(child_tables)}")
            lines.append(f"- Parent Tables (referenced): {len(parent_tables)}")
            lines.append(f"- Total Relationships: {len(results)}")

            return "\n".join(str(line) for line in lines)

        else:
            # Group relationships by constraint
            from collections import defaultdict
            grouped = defaultdict(list)
            for row in results:
                grouped[row['constraint_name']].append(row)

            relationships = []
            for constraint, rows in grouped.items():
                relationships.append({
                    "constraint_name": constraint,
                    "child_table": rows[0]["child_table"],
                    "parent_table": rows[0]["parent_table"],
                    "columns": [
                        {
                            "child_column": r["child_column"],
                            "parent_column": r["parent_column"]
                        }
                        for r in rows
                    ]
                })

            return json.dumps({
                "database": target_db,
                "count": len(relationships),
                "relationships": relationships
            }, indent=2)

    except Exception as e:
        logger.error(f"Error listing foreign key relationships: {e}")
        return f"Error: Failed to list foreign key relationships: {str(e)}"


# ==================== Tool: Execute Custom Query ====================

class ExecuteCustomQueryInput(BaseModel):
    """Input for executing custom SQL query."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    database: Optional[str] = Field(
        default=None,
        description="Database name. If not provided, uses default database from connection."
    )
    query: str = Field(
        ...,
        description="SQL query to execute (SELECT statements only for safety)",
        min_length=1
    )
    limit: Optional[int] = Field(
        default=100,
        description="Maximum number of rows to return (default: 100, max: 1000)",
        ge=1,
        le=1000
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="mysql_execute_custom_query",
    annotations={
        "title": "Execute Custom Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def execute_custom_query(params: ExecuteCustomQueryInput, ctx: Context) -> str:
    """
    Execute a custom read-only SQL query on the database.

    SECURITY NOTE: This tool only allows SELECT queries for safety.
    DML (INSERT, UPDATE, DELETE) and DDL (CREATE, ALTER, DROP) statements are not allowed.

    Args:
        params (ExecuteCustomQueryInput): Input parameters containing:
            - database (Optional[str]): Database name
            - query (str): SQL SELECT query to execute
            - limit (Optional[int]): Maximum rows to return
            - response_format (ResponseFormat): Output format

    Returns:
        str: Query results.
    """
    db: DatabaseClient = get_db_client()

    try:
        # Security check: Only allow SELECT queries
        normalized_query = params.query.strip().upper()
        if not normalized_query.startswith("SELECT"):
            return "Error: Only SELECT queries are allowed for safety. DML and DDL statements are prohibited."

        # Add LIMIT clause if not present and limit is specified
        if params.limit and "LIMIT" not in normalized_query:
            query = f"{params.query} LIMIT {params.limit}"
        else:
            query = params.query

        results = await db.execute_query(query)

        if params.response_format == ResponseFormat.MARKDOWN:
            if not results:
                return "*Query returned no results*"

            lines = ["# Custom Query Results", ""]
            lines.append(f"Returned {len(results)} row(s)")
            lines.append("")

            # Create markdown table
            headers = list(results[0].keys())
            table_rows = []

            for row in results:
                table_rows.append([truncate_value(row.get(h)) for h in headers])

            lines.append(format_markdown_table(headers, table_rows))

            return "\n".join(str(line) for line in lines)

        else:
            return json.dumps({
                "query": params.query,
                "count": len(results),
                "data": results
            }, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error executing custom query: {e}")
        return f"Error: Failed to execute query: {str(e)}"


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    # Run with HTTP transport for remote access
    if args.transport == "streamable_http":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
