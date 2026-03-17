"""Example: Async chat with OpenCode."""

import asyncio
from opencode_4_py import AsyncOpenCodeClient


async def main():
    async with AsyncOpenCodeClient() as client:
        # Check server health
        health = await client.health_check()
        print(f"Server version: {health['version']}")
        
        # Create a session
        session = await client.session.create(title="Async Chat Session")
        print(f"Created session: {session.id}")
        
        # Send a message
        result = await client.message.send_text(
            session_id=session.id,
            text="Hello! Can you help me write a Python function to calculate factorial?",
        )
        
        # Print response
        print("\nAssistant response:")
        for part in result.parts:
            if part.type == "text":
                print(part.text)


if __name__ == "__main__":
    asyncio.run(main())
