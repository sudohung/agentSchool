"""OpenCode SDK 集成测试."""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.asyncio
async def test_sdk_import():
    """测试 SDK 导入."""
    from opencode_4_py import OpenCodeClient, ClientConfig
    assert OpenCodeClient is not None
    assert ClientConfig is not None


@pytest.mark.asyncio
async def test_sdk_connection():
    """测试 SDK 连接."""
    from opencode_4_py import OpenCodeClient, ClientConfig
    
    BASE_URL = "http://172.22.221.176:4096"
    config = ClientConfig(base_url=BASE_URL)
    client = OpenCodeClient(config)
    health = client.health_check()
    
    assert health is not None
    assert health.version is not None
    assert health.healthy is True


@pytest.mark.asyncio
async def test_session_management():
    """测试会话管理."""
    from opencode_4_py import OpenCodeClient, ClientConfig
    
    BASE_URL = "http://172.22.221.176:4096"
    config = ClientConfig(base_url=BASE_URL)
    client = OpenCodeClient(config)
    
    session = client.session.create(title="集成测试会话")
    assert session is not None
    assert session.id is not None
    
    # 清理
    client.close()


@pytest.mark.asyncio
async def test_message_sending():
    """测试消息发送."""
    from opencode_4_py import OpenCodeClient, ClientConfig
    
    BASE_URL = "http://172.22.221.176:4096"
    config = ClientConfig(base_url=BASE_URL)
    client = OpenCodeClient(config)
    
    session = client.session.create(title="消息测试")
    
    result = client.message.send_text(
        session_id=session.id,
        text="用一句话介绍你的能力",
    )
    
    assert result is not None
    assert len(result.parts) > 0
    
    # 清理
    client.close()


@pytest.mark.asyncio
async def test_opencode_integration():
    """测试 OpenCodeIntegration 集成."""
    from agent.opencode_integration import OpenCodeIntegration
    
    BASE_URL = "http://172.22.221.176:4096"
    opencode = OpenCodeIntegration(base_url=BASE_URL)
    
    # 连接
    connected = await opencode.connect()
    assert connected is True
    
    # 创建会话
    sess = await opencode.create_session("Integration Test")
    assert sess is not None
    assert sess.id is not None
    
    # 发送消息
    msg_result = await opencode.send_message("build", "你好")
    assert msg_result is not None
    assert len(msg_result.parts) > 0
    
    # 断开
    await opencode.disconnect()
