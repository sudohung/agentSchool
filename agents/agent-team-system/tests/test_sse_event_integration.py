"""SSE 事件接收和处理集成测试.

测试完整的 SSE 事件流程：
1. 从 OpenCode SDK 订阅事件
2. 接收原始事件
3. 解析为 SSEEvent
4. 通过责任链处理
5. 调用 DecisionAgent 决策
6. 通过 SDK 响应
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, call
from typing import List, Any

from event.chain import (
    SSEEvent,
    SSEEventType,
    EventContext,
    EventResult,
)
from event.manager import SSEEventManager
from event.handlers import PermissionDecision


# ==================== Mock OpenCode SDK ====================

class MockOpenCodeEventAPI:
    """模拟 OpenCode Event API"""
    
    def __init__(self, events_to_emit: List[Any] = None):
        self.events_to_emit = events_to_emit or []
        self.answer_calls = []
        self.respond_calls = []
    
    async def subscribe(self, session_id: str):
        """模拟订阅事件流"""
        for event in self.events_to_emit:
            yield event
            await asyncio.sleep(0.01)  # 模拟异步
    
    def answer(self, question_id: str, answer: str):
        """模拟回答问题"""
        self.answer_calls.append((question_id, answer))
    
    def respond(self, permission_id: str, allow: bool, reason: str = ""):
        """模拟响应权限"""
        self.respond_calls.append((permission_id, allow, reason))


class MockOpenCodeClient:
    """模拟 OpenCode 客户端"""
    
    def __init__(self, events_to_emit: List[Any] = None):
        self.event = MockOpenCodeEventAPI(events_to_emit)
        self.session_id_counter = 0
        
        # 添加 question 和 permission API（被 handlers 使用）
        self.question = Mock()
        self.question.answer = self.event.answer
        
        self.permission = Mock()
        self.permission.respond = self.event.respond
        
        self.message = Mock()
        self.message.send_text = Mock()
    
    def health_check(self):
        return Mock(version="1.2.24")


# ==================== Mock SSE 事件对象 ====================

# 直接使用正确的类名，这样 from_opencode 能正确解析
class EventQuestionAsked:
    """模拟 EventQuestionAsked - 类名必须匹配 SDK"""
    
    def __init__(self, question_id: str, question: str, options: List[str] = None):
        self.question_id = question_id
        self.question = question
        self.options = options or []
    
    def model_dump(self) -> dict:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "options": self.options,
        }


class EventPermissionAsked:
    """模拟 EventPermissionAsked - 类名必须匹配 SDK"""
    
    def __init__(self, permission_id: str, perm_type: str, resource: str, agent: str = None):
        self.permission_id = permission_id
        self.type = perm_type
        self.resource = resource
        self.agent = agent
    
    def model_dump(self) -> dict:
        return {
            "permission_id": self.permission_id,
            "type": self.type,
            "resource": self.resource,
            "agent": self.agent,
        }


# ==================== Mock Decision Agent ====================

class MockDecisionAgentForIntegration:
    """用于集成测试的决策 Agent"""
    
    def __init__(self):
        self.decisions = []
    
    async def analyze_question(
        self,
        question: str,
        options: List[str] = None,
        context: dict = None,
    ) -> str:
        """分析问题"""
        # 根据问题内容决策
        if options:
            answer = options[0]  # 选择第一个选项
        else:
            answer = f"Answer to: {question[:50]}"
        
        self.decisions.append({
            "type": "question",
            "question": question,
            "answer": answer,
        })
        
        return answer
    
    async def analyze_permission(
        self,
        permission_type: str,
        resource: str,
        agent_role: str = None,
        context: dict = None,
    ):
        """分析权限"""
        from event.handlers.permission import PermissionAnalysis
        
        # 简单决策逻辑
        if "dangerous" in resource.lower() or ".env" in resource.lower():
            return PermissionAnalysis(
                decision=PermissionDecision.DENY,
                reason=f"Dangerous: {resource}",
                risk_level="high",
                confidence=1.0,
            )
        
        return PermissionAnalysis(
            decision=PermissionDecision.ALLOW,
            reason=f"Safe: {resource}",
            risk_level="low",
            confidence=0.9,
        )


# ==================== 集成测试 ====================

class TestSSEEventReceptionAndProcessing:
    """SSE 事件接收和处理集成测试"""
    
    @pytest.mark.asyncio
    async def test_receive_and_process_question_event(self):
        """测试接收和处理问题事件"""
        # 1. 准备模拟事件
        question_event = EventQuestionAsked(
            question_id="q_123",
            question="What is the best programming language?",
            options=["Python", "Java", "C++"],
        )
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=[question_event])
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建 SSE 事件管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 启动管理器（只处理有限事件）
        manager._running = True
        
        # 6. 手动触发事件处理（模拟 SSE 监听）
        await manager._handle_raw_event(question_event)
        
        # 7. 验证结果
        assert decision_agent.decisions[0]["type"] == "question"
        assert decision_agent.decisions[0]["answer"] == "Python"  # 第一个选项
        
        # 8. 验证 SDK 被调用
        assert len(mock_client.event.answer_calls) == 1
        assert mock_client.event.answer_calls[0] == ("q_123", "Python")
    
    @pytest.mark.asyncio
    async def test_receive_and_process_permission_event_safe(self):
        """测试接收和处理安全权限事件"""
        # 1. 准备模拟事件（安全操作）
        permission_event = EventPermissionAsked(
            permission_id="p_456",
            perm_type="file_read",
            resource="/src/main.py",
            agent="Backend Developer",
        )
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=[permission_event])
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建 SSE 事件管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 处理事件
        manager._running = True
        await manager._handle_raw_event(permission_event)
        
        # 6. 验证结果（安全操作应该被自动允许）
        assert len(mock_client.event.respond_calls) == 1
        perm_id, allowed, reason = mock_client.event.respond_calls[0]
        assert perm_id == "p_456"
        assert allowed is True
        assert "Safe" in reason or "Auto" in reason
    
    @pytest.mark.asyncio
    async def test_receive_and_process_permission_event_dangerous(self):
        """测试接收和处理危险权限事件"""
        # 1. 准备模拟事件（危险操作）
        permission_event = EventPermissionAsked(
            permission_id="p_789",
            perm_type="file_read",
            resource=".env",
            agent="Unknown Agent",
        )
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=[permission_event])
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建 SSE 事件管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 处理事件
        manager._running = True
        await manager._handle_raw_event(permission_event)
        
        # 6. 验证结果（危险操作应该被拒绝）
        assert len(mock_client.event.respond_calls) == 1
        perm_id, allowed, reason = mock_client.event.respond_calls[0]
        assert perm_id == "p_789"
        assert allowed is False
        assert "Dangerous" in reason or "Auto" in reason
    
    @pytest.mark.asyncio
    async def test_receive_multiple_events_sequentially(self):
        """测试顺序接收多个事件"""
        # 1. 准备多个模拟事件
        events = [
            EventQuestionAsked("q_1", "Question 1?", ["A", "B"]),
            EventPermissionAsked("p_1", "file_read", "/src/test.py"),
            EventQuestionAsked("q_2", "Question 2?"),
            EventPermissionAsked("p_2", "file_read", ".env"),
        ]
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=events)
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建 SSE 事件管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 处理所有事件
        manager._running = True
        for event in events:
            await manager._handle_raw_event(event)
        
        # 6. 验证结果
        # 2 个问题被回答
        assert len(mock_client.event.answer_calls) == 2
        assert mock_client.event.answer_calls[0] == ("q_1", "A")
        assert "Answer to: Question 2" in mock_client.event.answer_calls[1][1]
        
        # 2 个权限被响应（1 个允许，1 个拒绝）
        assert len(mock_client.event.respond_calls) == 2
        assert mock_client.event.respond_calls[0][1] is True  # /src/test.py 允许
        assert mock_client.event.respond_calls[1][1] is False  # .env 拒绝
        
        # 决策 Agent 被调用 4 次（2 次问题 + 2 次权限，但权限可能有自动规则）
        assert len(decision_agent.decisions) >= 2  # 至少 2 次问题决策
    
    @pytest.mark.asyncio
    async def test_sse_event_parsing(self):
        """测试 SSE 事件解析"""
        # 1. 准备原始事件
        raw_event = EventQuestionAsked(
            question_id="q_test",
            question="Test question?",
            options=["Option 1"],
        )
        
        # 2. 转换为 SSEEvent
        sse_event = SSEEvent.from_opencode(raw_event, "test_session")
        
        # 3. 验证解析结果
        assert sse_event.type == SSEEventType.QUESTION_ASKED
        assert sse_event.session_id == "test_session"
        assert sse_event.data["question_id"] == "q_test"
        assert sse_event.data["question"] == "Test question?"
        assert sse_event.data["options"] == ["Option 1"]
    
    @pytest.mark.asyncio
    async def test_sse_event_manager_statistics(self):
        """测试 SSE 事件管理器统计"""
        # 1. 准备事件
        events = [
            EventQuestionAsked("q_1", "Q1?"),
            EventPermissionAsked("p_1", "file_read", "/src/test.py"),
            EventPermissionAsked("p_2", "file_read", ".env"),
        ]
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=events)
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 处理事件
        manager._running = True
        for event in events:
            await manager._handle_raw_event(event)
        
        # 6. 获取统计
        stats = manager.get_statistics()
        
        # 7. 验证统计
        assert stats["events_received"] == 3
        assert stats["events_processed"] == 3
        assert stats["questions_answered"] == 1
        assert stats["permissions_handled"] == 2
        
        # 责任链统计
        chain_stats = stats["chain_stats"]
        assert chain_stats["handlers_count"] == 3  # Question, Permission, Default


# ==================== SSE 监听器测试 ====================

class TestSSEListener:
    """SSE 监听器测试"""
    
    @pytest.mark.asyncio
    async def test_sse_listener_receives_events(self):
        """测试 SSE 监听器接收事件"""
        # 1. 准备事件流
        events_to_emit = [
            EventQuestionAsked("q_1", "Question 1?"),
            EventQuestionAsked("q_2", "Question 2?"),
            EventQuestionAsked("q_3", "Question 3?"),
        ]
        
        # 2. 创建 Mock SDK
        mock_client = MockOpenCodeClient(events_to_emit=events_to_emit)
        
        # 3. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 4. 创建管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 5. 启动监听器（短时间）
        manager._running = True
        listener_task = asyncio.create_task(manager._sse_listener())
        
        # 6. 等待事件处理完成
        await asyncio.sleep(0.5)
        
        # 7. 停止监听器
        manager._running = False
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
        # 8. 验证所有事件都被处理
        assert decision_agent.decisions[0]["question"] == "Question 1?"
        assert decision_agent.decisions[1]["question"] == "Question 2?"
        assert decision_agent.decisions[2]["question"] == "Question 3?"
    
    @pytest.mark.asyncio
    async def test_sse_listener_error_recovery(self):
        """测试 SSE 监听器错误恢复"""
        # 1. 创建会抛出异常的 Mock SDK
        mock_client = MagicMock()
        mock_client.event.subscribe = AsyncMock(side_effect=Exception("Connection error"))
        
        # 2. 创建决策 Agent
        decision_agent = MockDecisionAgentForIntegration()
        
        # 3. 创建管理器
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="test_session",
            decision_agent=decision_agent,
        )
        
        # 4. 启动监听器（会失败并重试）
        manager._running = True
        listener_task = asyncio.create_task(manager._sse_listener())
        
        # 5. 等待重试
        await asyncio.sleep(0.3)
        
        # 6. 停止监听器
        manager._running = False
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
        # 7. 验证 SDK 被多次调用（重试）
        assert mock_client.event.subscribe.call_count >= 2


# ==================== 真实场景测试 ====================

class TestRealWorldScenarios:
    """真实场景测试"""
    
    @pytest.mark.asyncio
    async def test_agent_asks_for_user_input(self):
        """测试场景：Agent 执行时需要用户输入"""
        # 场景：Backend Developer 需要确认 API 设计
        
        question_event = EventQuestionAsked(
            question_id="q_api_design",
            question="Should we use REST or GraphQL for this API?",
            options=["REST", "GraphQL"],
        )
        
        mock_client = MockOpenCodeClient(events_to_emit=[question_event])
        decision_agent = MockDecisionAgentForIntegration()
        
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="dev_session",
            decision_agent=decision_agent,
        )
        
        manager._running = True
        await manager._handle_raw_event(question_event)
        
        # 验证：决策 Agent 选择了第一个选项（REST）
        assert decision_agent.decisions[0]["answer"] == "REST"
        assert mock_client.event.answer_calls[0] == ("q_api_design", "REST")
    
    @pytest.mark.asyncio
    async def test_agent_needs_file_permission(self):
        """测试场景：Agent 需要文件写入权限"""
        # 场景：Frontend Developer 需要写入配置文件
        
        permission_event = EventPermissionAsked(
            permission_id="p_config_write",
            perm_type="file_write",
            resource="/src/config/settings.json",
            agent="Frontend Developer",
        )
        
        mock_client = MockOpenCodeClient(events_to_emit=[permission_event])
        decision_agent = MockDecisionAgentForIntegration()
        
        manager = SSEEventManager(
            opencode_client=mock_client,
            session_id="dev_session",
            decision_agent=decision_agent,
        )
        
        manager._running = True
        await manager._handle_raw_event(permission_event)
        
        # 验证：/src/ 目录下的文件写入被允许
        assert len(mock_client.event.respond_calls) == 1
        perm_id, allowed, reason = mock_client.event.respond_calls[0]
        assert perm_id == "p_config_write"
        assert allowed is True


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
