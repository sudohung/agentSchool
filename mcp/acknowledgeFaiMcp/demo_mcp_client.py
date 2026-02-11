"""
Demo MCP client for the FAISS knowledge-base MCP server.

This script launches the local MCP server (stdio transport) and demonstrates:
  - adding documents (server computes embeddings on CPU)
  - searching by text
  - saving the index

Requires the MCP package in this repo and that `faiss_mcp_server.py` lives in the same directory.
"""

import asyncio
import os
import json
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()


async def demo():
    here = os.path.dirname(__file__)
    server_script = os.path.join(here, "faiss_mcp_server.py")

    server_params = StdioServerParameters(
        command="python",
        args=[server_script, "--transport", "stdio"]
    )

    print("Starting FAISS MCP server (stdio)...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to FAISS MCP server")

            # 1) Add some documents (server will compute embeddings using sentence-transformers)
            docs = [
                "如何安装项目依赖并启动服务？",
                "如何在本地使用 FAISS 创建索引并保存？",
                "示例文档：讨论模型选择与调参策略。"
            ]
            ids = [1001, 1002, 1003]
            metadatas = [{"title": "install"}, {"title": "faiss"}, {"title": "notes"}]

            print("Adding documents to FAISS (server will compute embeddings on CPU)...")
            add_resp = await session.call_tool(
                "faiss_add_items",
                arguments={
                    "params": {
                        "ids": ids,
                        "documents": docs,
                        "metadatas": metadatas
                    }
                }
            )

            for part in add_resp.content:
                if hasattr(part, 'text'):
                    print(part.text)

            # 2) Search by text
            query = "如何启动服务？"
            print(f"Searching for: {query}")
            search_resp = await session.call_tool(
                "faiss_search",
                arguments={
                    "params": {
                        "query_text": query,
                        "k": 3
                    }
                }
            )

            for part in search_resp.content:
                if hasattr(part, 'text'):
                    try:
                        # Tool returns JSON string; pretty-print if possible
                        parsed = json.loads(part.text)
                        print(json.dumps(parsed, ensure_ascii=False, indent=2))
                    except Exception:
                        print(part.text)

            # 3) Persist index
            print("Saving FAISS index and metadata on server...")
            save_resp = await session.call_tool("faiss_save", arguments={"params": {}})
            for part in save_resp.content:
                if hasattr(part, 'text'):
                    print(part.text)

            print("Demo complete.")


if __name__ == "__main__":
    asyncio.run(demo())
