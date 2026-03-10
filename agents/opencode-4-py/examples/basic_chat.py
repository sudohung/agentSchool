"""Example: Basic chat with OpenCode."""

from opencode_4_py import OpenCodeClient


def main():
    with OpenCodeClient() as client:
        # Check server health
        health = client.health_check()
        print(f"Server version: {health['version']}")
        
        # Create a session
        session = client.session.create(title="Chat Session")
        print(f"Created session: {session.id}")
        
        # Send a message
        result = client.message.send_text(
            session_id=session.id,
            text="Hello! Can you help me write a Python function to calculate factorial?",
        )
        
        # Print response
        print("\nAssistant response:")
        for part in result.parts:
            if part.type == "text":
                print(part.text)


if __name__ == "__main__":
    main()
