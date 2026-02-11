# Memory MCP Server

A lightweight MCP (Model Context Protocol) server for agent long-term memory storage using SQLite with FTS5 full-text search capabilities.

## Features

- 💾 **Persistent Storage**: SQLite-based storage for reliable memory persistence
- 🔍 **Full-Text Search**: Built-in FTS5 full-text search for efficient memory retrieval
- 📦 **Metadata Support**: Store structured metadata alongside memory content
- 🔄 **Simple API**: Clean, easy-to-use tools for memory operations
- ⚡ **Lightweight**: Minimal dependencies and resource usage
- 🔒 **Safe**: Read-only operations where appropriate, secure data handling

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Configure the memory server using environment variables:

```bash
export MEMORY_DB_PATH="memory.db"        # Path to SQLite database file
export MEMORY_MAX_SIZE="10000"          # Maximum number of memories to store
export MEMORY_ENABLE_FTS="true"         # Enable full-text search (FTS5)
```

Or create a `.env` file:

```env
MEMORY_DB_PATH=memory.db
MEMORY_MAX_SIZE=10000
MEMORY_ENABLE_FTS=true
```

## Running the Server

### HTTP Transport (Recommended for Remote Access)

```bash
python mem_mcp_server.py --transport streamable_http --port 8000
```

The server will start on `http://localhost:8000`.

### Stdio Transport (For Local Tools)

```bash
python mem_mcp_server.py --transport stdio
```

## Available Tools

### 1. `mem_store_memory`
Store a new memory entry with optional metadata.

**Parameters:**
- `content`: The content to store as memory (required)
- `metadata`: Optional metadata to associate with the memory (JSON object)
- `response_format`: Output format (markdown/json)

### 2. `mem_search_memories`
Search stored memories using full-text search.

**Parameters:**
- `query`: Search query to find relevant memories (required)
- `limit`: Maximum number of results to return (default: 10, max: 100)
- `response_format`: Output format (markdown/json)

### 3. `mem_get_memory`
Retrieve a specific memory by ID.

**Parameters:**
- `memory_id`: ID of the memory to retrieve (required)
- `response_format`: Output format (markdown/json)

### 4. `mem_list_memories`
List stored memories with pagination.

**Parameters:**
- `limit`: Maximum number of memories to return (default: 10, max: 100)
- `offset`: Number of memories to skip for pagination (default: 0)
- `response_format`: Output format (markdown/json)

### 5. `mem_delete_memory`
Delete a specific memory by ID.

**Parameters:**
- `memory_id`: ID of the memory to delete (required)
- `response_format`: Output format (markdown/json)

## Usage Examples

### Store a Memory

```yaml
mem_store_memory:
  content: "The user prefers dark mode and likes Python programming"
  metadata:
    category: "user_preferences"
    source: "conversation"
    confidence: 0.95
```

### Search Memories

```yaml
mem_search_memories:
  query: "user preferences"
  limit: 5
```

### Retrieve Specific Memory

```yaml
mem_get_memory:
  memory_id: 42
```

### List All Memories

```yaml
mem_list_memories:
  limit: 20
  offset: 0
```

### Delete Memory

```yaml
mem_delete_memory:
  memory_id: 42
```

## Response Formats

Tools support two output formats:

- **Markdown**: Human-readable formatted output, ideal for exploration
- **JSON**: Machine-readable structured data, ideal for programmatic use

Specify `response_format: "json"` for structured data processing.

## Integration with Claude Desktop

To integrate with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcp": {
    "memory": {
      "command": "python",
      "args": [
        "/path/to/mem_mcp_server.py",
        "--transport", "stdio"
      ],
      "env": {
        "MEMORY_DB_PATH": "agent_memory.db",
        "MEMORY_MAX_SIZE": "50000",
        "MEMORY_ENABLE_FTS": "true"
      }
    }
  }
}
```

## Database Schema

The SQLite database uses the following schema:

```sql
-- Main memories table
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 virtual table for full-text search (when enabled)
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content, metadata, created_at, updated_at, 
    content=memories, content_rowid=id
);
```

## Security Notes

- All memory operations are designed to be safe and non-destructive
- The database file is stored locally and can be backed up easily
- Metadata is stored as JSON and validated before storage
- Full-text search is optimized for performance and security

## Development

### Testing

Test the server with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Then connect to `http://localhost:8000`.

### Adding New Features

Follow the existing patterns:
1. Create a Pydantic `Input` model with `Field()` descriptions
2. Use `@mcp.tool()` decorator with proper annotations
3. Implement async function with comprehensive docstring
4. Handle errors gracefully and return actionable messages

## License

MIT License