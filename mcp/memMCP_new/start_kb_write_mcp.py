#!/usr/bin/env python
"""
Launcher for Knowledge Base Write MCP Server
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

    server = here / "kb_write_mcp_server.py"
    if not server.exists():
        print(f"Error: {server} not found", file=sys.stderr)
        sys.exit(2)

    os.execv(sys.executable, [sys.executable, str(server), "--transport", "stdio"])

if __name__ == "__main__":
    main()