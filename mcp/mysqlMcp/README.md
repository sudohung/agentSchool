# MySQL MCP Server

An MCP (Model Context Protocol) server for exploring and analyzing MySQL databases to understand business data patterns and relationships.

## Features

- 📊 **Database Discovery**: List all databases and get comprehensive overviews
- 📋 **Table Exploration**: List tables with metadata (rows, size, engine)
- 🔍 **Schema Analysis**: Detailed table schemas with columns, indexes, and foreign keys
- 📈 **Data Sampling**: Sample table data to understand content and structure
- 📊 **Statistics**: Table statistics including row counts, null values, and data distribution
- 🔗 **Relationship Mapping**: Visualize foreign key relationships between tables
- 💡 **Custom Queries**: Execute read-only SQL queries for deep analysis

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Configure MySQL connection using environment variables:

```bash
export MYSQL_HOST="localhost"
export MYSQL_PORT="3306"
export MYSQL_USER="your_username"
export MYSQL_PASSWORD="your_password"
export MYSQL_DATABASE="your_database"  # Optional: default database
export MYSQL_CHARSET="utf8mb4"
```

Or pass credentials at runtime using the connection tools.

## Running the Server

### HTTP Transport (Recommended for Remote Access)

```bash
python mysql_mcp_server.py --transport streamable_http --port 8000
```

The server will start on `http://localhost:8000`.

### Stdio Transport (For Local Tools)

```bash
python mysql_mcp_server.py --transport stdio
```

## Available Tools

### 1. `mysql_list_databases`
List all available databases on the MySQL server.

**Parameters:**
- `filter_pattern`: SQL LIKE pattern to filter database names (optional)
- `include_system`: Include system databases (default: false)
- `response_format`: Output format (markdown/json)

### 2. `mysql_database_overview`
Get comprehensive overview of a database.

**Parameters:**
- `database`: Database name (optional, uses default if not provided)
- `include_table_count`: Include table count (default: true)
- `include_size`: Include size information (default: true)
- `response_format`: Output format (markdown/json)

### 3. `mysql_list_tables`
List all tables in a database.

**Parameters:**
- `database`: Database name (optional)
- `table_pattern`: SQL LIKE pattern to filter tables (optional)
- `include_views`: Include views (default: false)
- `limit`: Maximum number of tables to return (optional)
- `response_format`: Output format (markdown/json)

### 4. `mysql_get_table_schema`
Get detailed schema information for a table.

**Parameters:**
- `database`: Database name (optional)
- `table`: Table name (required)
- `include_indexes`: Include index information (default: true)
- `include_foreign_keys`: Include foreign key information (default: true)
- `response_format`: Output format (markdown/json)

### 5. `mysql_sample_table_data`
Sample data from a table to understand its content.

**Parameters:**
- `database`: Database name (optional)
- `table`: Table name (required)
- `limit`: Number of rows to sample (default: 10, max: 100)
- `columns`: Comma-separated column names (optional, selects all if not provided)
- `where_clause`: WHERE clause for filtering (optional, advanced users)
- `order_by`: ORDER BY clause (optional)
- `response_format`: Output format (markdown/json)

### 6. `mysql_analyze_table_statistics`
Analyze table statistics including row counts and data distribution.

**Parameters:**
- `database`: Database name (optional)
- `table`: Table name (required)
- `include_column_stats`: Include per-column statistics (default: true)
- `response_format`: Output format (markdown/json)

### 7. `mysql_list_foreign_key_relationships`
List foreign key relationships to understand data model.

**Parameters:**
- `database`: Database name (optional)
- `table`: Filter by specific table (optional)
- `direction`: Relationship direction (outgoing/incoming/both, default: both)
- `response_format`: Output format (markdown/json)

### 8. `mysql_execute_custom_query`
Execute a custom read-only SQL query.

**Parameters:**
- `database`: Database name (optional)
- `query`: SQL SELECT query (required)
- `limit`: Maximum rows to return (default: 100, max: 1000)
- `response_format`: Output format (markdown/json)


## Integration with Claude Desktop

To integrate with Claude Desktop, add the following to your `opencode.json`:

```json
{
  "mcp": {
    "memory": {
      "type": "remote",
      "url": "localhost:8000/sse",
      "enabled": true
    }
  }
}
```

## Usage Examples

### Explore Database Structure

1. **List all databases:**
   ```
   mysql_list_databases
   ```

2. **Get database overview:**
   ```
   mysql_database_overview
   database: "myapp"
   ```

3. **List tables:**
   ```
   mysql_list_tables
   database: "myapp"
   table_pattern: "%user%"
   ```

### Understand Table Schema

4. **Get table schema:**
   ```
   mysql_get_table_schema
   database: "myapp"
   table: "users"
   ```

5. **Sample data:**
   ```
   mysql_sample_table_data
   database: "myapp"
   table: "users"
   limit: 5
   ```

### Analyze Data Patterns

6. **Analyze statistics:**
   ```
   mysql_analyze_table_statistics
   database: "myapp"
   table: "orders"
   ```

7. **List relationships:**
   ```
   mysql_list_foreign_key_relationships
   database: "myapp"
   direction: "both"
   ```

8. **Custom query:**
   ```
   mysql_execute_custom_query
   query: "SELECT status, COUNT(*) as count FROM orders GROUP BY status"
   ```

## Response Formats

Tools support two output formats:

- **Markdown**: Human-readable formatted output, ideal for exploration
- **JSON**: Machine-readable structured data, ideal for programmatic use

Specify `response_format: "json"` for structured data processing.

## Security Notes

- The `mysql_execute_custom_query` tool only allows SELECT statements for safety
- DML (INSERT, UPDATE, DELETE) and DDL (CREATE, ALTER, DROP) statements are prohibited
- All tools are read-only (`readOnlyHint: true`) and non-destructive

## Development

### Testing

Test the server with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Then connect to `http://localhost:8000`.

### Adding New Tools

Follow the existing patterns:
1. Create a Pydantic `Input` model with `Field()` descriptions
2. Use `@mcp.tool()` decorator with proper annotations
3. Implement async function with comprehensive docstring
4. Handle errors gracefully and return actionable messages

## License

MIT License
