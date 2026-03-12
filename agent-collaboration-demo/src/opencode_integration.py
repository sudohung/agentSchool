#!/usr/bin/env python3
"""
OpenCode 集成模块
用于代码生成和执行
"""
import asyncio
import os
import sys
from typing import Optional

# OpenCode SDK 配置
OPENCODE_SERVER_URL = os.getenv("OPENCODE_SERVER_URL", "http://192.168.124.2:4096")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "CodingPlan/gml-5")


class OpenCodeClient:
    """OpenCode 客户端封装"""
    
    def __init__(self, server_url: str = None, model: str = None):
        self.server_url = server_url or OPENCODE_SERVER_URL
        self.model = model or OPENCODE_MODEL
        self.client = None
        self._connected = False
    
    async def connect(self):
        """连接 OpenCode 服务器"""
        try:
            from opencode_agent_sdk import SDKClient, AgentOptions
            
            self.client = SDKClient(options=AgentOptions(
                model=self.model,
                server_url=self.server_url,
                system_prompt="你是一个专业的软件开发工程师，负责根据需求生成高质量的代码。"
            ))
            await self.client.connect()
            self._connected = True
            print(f"[OpenCode] 已连接: {self.server_url}, 模型: {self.model}")
        except ImportError:
            print("[OpenCode] SDK 未安装，跳过 OpenCode 集成")
            self._connected = False
        except Exception as e:
            print(f"[OpenCode] 连接失败: {e}")
            self._connected = False
    
    async def generate_code(self, requirement: str, language: str = "python") -> str:
        """使用 OpenCode 生成代码"""
        if not self._connected or not self.client:
            return f"# OpenCode 未连接，使用占位代码\n# 需求: {requirement}\n\ndef main():\n    pass"
        
        prompt = f"""请根据以下需求生成 {language} 代码:

需求:
{requirement}

要求:
1. 代码完整、可运行
2. 遵循最佳实践
3. 包含必要的错误处理
4. 如需依赖请说明

请直接输出代码，不要解释。"""
        
        try:
            await self.client.query(prompt)
            response = []
            async for msg in self.client.receive_response():
                if hasattr(msg, 'content') and msg.content:
                    response.append(msg.content)
                elif hasattr(msg, 'text') and msg.text:
                    response.append(msg.text)
            
            return "\n".join(response)
        except Exception as e:
            print(f"[OpenCode] 代码生成失败: {e}")
            return f"# 代码生成失败: {e}\n\ndef main():\n    pass"
    
    async def execute_code(self, code: str, language: str = "python") -> dict:
        """使用 OpenCode 执行代码"""
        if not self._connected or not self.client:
            return {"success": False, "error": "OpenCode 未连接", "stdout": "", "stderr": ""}
        
        prompt = f"""请执行以下 {language} 代码并返回执行结果:

```{language}
{code}
```

请直接返回执行结果，格式如下:
- 如果有输出: 返回 stdout
- 如果有错误: 返回 stderr 和错误信息"""
        
        try:
            await self.client.query(prompt)
            response = []
            async for msg in self.client.receive_response():
                if hasattr(msg, 'content') and msg.content:
                    response.append(msg.content)
                elif hasattr(msg, 'text') and msg.text:
                    response.append(msg.text)
            
            result = "\n".join(response)
            return {
                "success": True,
                "stdout": result,
                "stderr": "",
                "output": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    async def generate_and_execute(self, requirement: str, language: str = "python") -> dict:
        """生成代码并执行"""
        print(f"[OpenCode] 生成代码中...")
        code = await self.generate_code(requirement, language)
        print(f"[OpenCode] 代码生成完成 ({len(code)} 字符)")
        
        print(f"[OpenCode] 执行代码中...")
        result = await self.execute_code(code, language)
        
        return {
            "code": code,
            "execution": result
        }
    
    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
            self._connected = False


# 全局实例
_opencode_client: Optional[OpenCodeClient] = None


async def get_opencode_client() -> OpenCodeClient:
    """获取全局 OpenCode 客户端"""
    global _opencode_client
    if _opencode_client is None:
        _opencode_client = OpenCodeClient()
        await _opencode_client.connect()
    return _opencode_client


async def close_opencode_client():
    """关闭全局 OpenCode 客户端"""
    global _opencode_client
    if _opencode_client:
        await _opencode_client.close()
        _opencode_client = None
