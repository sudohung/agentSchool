#!/usr/bin/env python
"""
Launcher for OpenCode: loads .env into environment and execs the MCP server
in STDIO mode so OpenCode can communicate with it over stdin/stdout.
Place this next to `mysql_mcp_server.py` and point OpenCode to run:
  python start_opencode_mcp.py

This script uses os.execv so the launched process inherits the same stdio
file descriptors (required for MCP stdio transport).
"""
import os
import sys
from pathlib import Path


def load_dotenv(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


def main():
    here = Path(__file__).parent
    load_dotenv(here / ".env")

    server = here / "mysql_mcp_server.py"
    if not server.exists():
        print(f"Error: {server} not found", file=sys.stderr)
        sys.exit(2)

    # Replace current process with the MCP server process, preserving stdio
    os.execv(sys.executable, [sys.executable, str(server), "--transport", "stdio"]) 


if __name__ == "__main__":
    main()
