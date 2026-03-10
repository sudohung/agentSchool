# opencode-4-py

Python SDK for [OpenCode](https://opencode.ai) Server.

## Installation

```bash
pip install opencode-4-py
```

## Quick Start

```python
from opencode_4_py import OpenCodeClient

# Create client
client = OpenCodeClient(base_url="http://localhost:4096")

# Check server health
health = client.health_check()
print(f"Server version: {health.version}")

# Create a session
session = client.session.create(title="My Session")

# Send a message
result = client.message.send(
    session_id=session.id,
    parts=[{"type": "text", "text": "Hello, OpenCode!"}]
)

print(f"Response: {result.parts[0].text}")
```

## Async Support

```python
from opencode_4_py import AsyncOpenCodeClient

async def main():
    async with AsyncOpenCodeClient() as client:
        session = await client.session.create(title="Async Session")
        result = await client.message.send(
            session_id=session.id,
            parts=[{"type": "text", "text": "Hello!"}]
        )
        print(result)
```

## Features

- Full API coverage for OpenCode Server
- Sync and async clients
- Type-safe with Pydantic models
- SSE event streaming
- Automatic retries and error handling
- Structured output support

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Type checking
mypy src/opencode_4_py

# Linting
ruff check src/
```

## License

MIT