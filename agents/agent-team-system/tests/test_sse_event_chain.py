"""SSE 事件流和决策 Agent 测试."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Optional, Any

# 测试事件模块
from event.chain import (
    SSEEventType,
    SSEEvent,
    QuestionAskedEvent,
    PermissionAskedEvent,
    EventContext,
    EventResult,
    EventHandler,
    EventHandlerChain,
)
from event.handlers import (
    QuestionAskHandler,
    PermissionAskHandler,
    DefaultHandler,
    PermissionDecision,
    PermissionAnalysis,
)
from event.manager import SSEEventManager


# ==================== Mock 决策 Agent ====================

class MockDecisionAgent:
    """模拟决策 Agent 用于测试"""
    
    def __init__(self):
        self.decisions = []
        self.question_analyze_count = 0
        self.permission_analyze_count = 0
    
    async def analyze_question(
        self,
        question: Optional[str],
        options: Optional[list] = None,
        context: Optional[dict] = None,
    ) -> str:
        """模拟问题分析"""
        self.question_analyze_count += 1
        
        # 简单决策逻辑
        if not question:
            return "I need more information."
        
        if options:
            # 有选项时选择第一个
            answer = options[0] if options else "Unknown"
        else:
            # 无选项时生成回答
            answer = f"Based on analysis: {question[:50]}"
        
        self.decisions.append({
            "type": "question",
            "question": question,
            "answer": answer,
        })
        
        return answer
    
    async def analyze_permission(
        self,
        permission_type: Optional[str],
        resource: Optional[str],
        agent_role: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> PermissionAnalysis:
        """模拟权限分析"""
        self.permission_analyze_count += 1
        
        # 简单决策逻辑
        if not permission_type or not resource:
            return PermissionAnalysis(
                decision=PermissionDecision.DENY,
                reason="Invalid permission request",
                risk_level="unknown",
                confidence=0.0,
            )
        
        # 危险操作
        dangerous = ["rm -rf", "sudo", ".env", "credentials"]
        if any(d in resource.lower() for d in dangerous):
            return PermissionAnalysis(
                decision=PermissionDecision.DENY,
                reason=f"Dangerous operation: {resource}",
                risk_level="high",
                confidence=1.0,
            )
        
        # 安全操作
        safe = ["/src/", "git status", "npm list"]
        if any(s in resource.lower() for s in safe):
            return PermissionAnalysis(
                decision=PermissionDecision.ALLOW,
                reason=f"Safe operation: {resource}",
                risk_level="low",
                confidence=1.0,
            )
        
        # 默认：中等风险，允许
        return PermissionAnalysis(
            decision=PermissionDecision.ALLOW,
            reason=f"Normal operation: {resource}",
            risk_level="medium",
            confidence=0.8,
        )


# ==================== 辅助函数 ====================

def create_mock_event(
    event_type: SSEEventType,
    data: dict = None,
    raw_event: Any = None,
) -> SSEEvent:
    """创建模拟事件"""
    return SSEEvent(
        id=f"evt_test_{event_type.value}",
        type=event_type,
        source="test",
        data=data or {},
        timestamp=1234567890,
        session_id="test_session",
        raw_event=raw_event,
    )


def create_mock_context(decision_agent: Any = None) -> EventContext:
    """创建模拟上下文"""
    mock_client = Mock()
    mock_client.question = Mock()
    mock_client.question.answer = Mock()
    mock_client.permission = Mock()
    mock_client.permission.respond = Mock()
    
    return EventContext(
        session_id="test_session",
        opencode_client=mock_client,
        decision_agent=decision_agent or MockDecisionAgent(),
    )


# ==================== SSE 事件类型测试 ====================

class TestSSEEventType:
    """SSE 事件类型测试"""
    
    def test_event_types(self):
        """测试事件类型定义"""
        assert SSEEventType.QUESTION_ASKED.value == "question_asked"
        assert SSEEventType.PERMISSION_ASKED.value == "permission_asked"
        assert SSEEventType.MESSAGE_UPDATED.value == "message_updated"
        assert SSEEventType.FILE_EDITED.value == "file_edited"
        assert SSEEventType.SESSION_ERROR.value == "session_error"
    
    def test_event_count(self):
        """测试事件类型数量"""
        assert len(SSEEventType) >= 9


# ==================== SSE 事件模型测试 ====================

class TestSSEEvent:
    """SSE 事件模型测试"""
    
    def test_create_event(self):
        """测试创建事件"""
        event = SSEEvent(
            id="evt_123",
            type=SSEEventType.QUESTION_ASKED,
            source="opencode",
            data={"question": "Test?"},
            timestamp=1234567890,
            session_id="test_session",
        )
        
        assert event.id == "evt_123"
        assert event.type == SSEEventType.QUESTION_ASKED
        assert event.data["question"] == "Test?"
    
    def test_question_event_from_sse(self):
        """测试从 SSE 事件创建问题事件"""
        raw = Mock()
        raw.question_id = "q_123"
        raw.question = "What is the answer?"
        raw.options = ["Option A", "Option B"]
        
        event = create_mock_event(
            SSEEventType.QUESTION_ASKED,
            raw_event=raw,
        )
        
        question_event = QuestionAskedEvent.from_sse_event(event)
        
        assert question_event.question_id == "q_123"
        assert question_event.question == "What is the answer?"
        assert question_event.options == ["Option A", "Option B"]
    
    def test_permission_event_from_sse(self):
        """测试从 SSE 事件创建权限事件"""
        raw = Mock()
        raw.permission_id = "p_123"
        raw.type = "file_write"
        raw.resource = "/src/test.py"
        raw.agent = "Backend Developer"
        
        event = create_mock_event(
            SSEEventType.PERMISSION_ASKED,
            raw_event=raw,
        )
        
        permission_event = PermissionAskedEvent.from_sse_event(event)
        
        assert permission_event.permission_id == "p_123"
        assert permission_event.permission_type == "file_write"
        assert permission_event.resource == "/src/test.py"
        assert permission_event.agent_role == "Backend Developer"


# ==================== 责任链框架测试 ====================

class TestEventHandlerChain:
    """责任链框架测试"""
    
    def test_create_chain(self):
        """测试创建责任链"""
        context = create_mock_context()
        chain = EventHandlerChain(context)
        
        assert chain._head is None
        assert len(chain._handlers) == 0
    
    def test_add_handler(self):
        """测试添加处理器"""
        context = create_mock_context()
        chain = EventHandlerChain(context)
        
        handler1 = QuestionAskHandler()
        handler2 = PermissionAskHandler()
        
        chain.add_handler(handler1)
        chain.add_handler(handler2)
        
        assert len(chain._handlers) == 2
        assert chain._head == handler1
        assert handler1._next == handler2
    
    def test_set_next_chain(self):
        """测试设置责任链"""
        h1 = QuestionAskHandler()
        h2 = PermissionAskHandler()
        h3 = DefaultHandler()
        
        h1.set_next(h2).set_next(h3)
        
        assert h1._next == h2
        assert h2._next == h3


# ==================== QuestionAskHandler 测试 ====================

class TestQuestionAskHandler:
    """问题询问处理器测试"""
    
    @pytest.mark.asyncio
    async def test_can_handle_question(self):
        """测试能否处理问题事件"""
        handler = QuestionAskHandler()
        
        assert handler.can_handle(SSEEventType.QUESTION_ASKED) is True
        assert handler.can_handle(SSEEventType.PERMISSION_ASKED) is False
    
    @pytest.mark.asyncio
    async def test_handle_question(self):
        """测试处理问题事件"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        handler = QuestionAskHandler()
        
        # 创建问题事件
        event = create_mock_event(
            SSEEventType.QUESTION_ASKED,
            data={"question": "What is Python?"},
        )
        
        # 处理事件
        result = await handler.handle(event, context)
        
        assert result is not None
        assert result.handled is True
        assert result.action == "answered"
        assert decision_agent.question_analyze_count == 1
    
    @pytest.mark.asyncio
    async def test_handle_question_with_options(self):
        """测试处理带选项的问题"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        handler = QuestionAskHandler()
        
        # 创建带选项的问题事件
        raw = Mock()
        raw.question_id = "q_1"
        raw.question = "Choose one:"
        raw.options = ["A", "B", "C"]
        
        event = create_mock_event(
            SSEEventType.QUESTION_ASKED,
            raw_event=raw,
        )
        
        result = await handler.handle(event, context)
        
        assert result.handled is True
        assert decision_agent.decisions[0]["answer"] == "A"
    
    @pytest.mark.asyncio
    async def test_handle_no_decision_agent(self):
        """测试没有决策 Agent 的情况"""
        # 创建没有决策 Agent 的上下文
        mock_client = Mock()
        mock_client.question = Mock()
        mock_client.question.answer = Mock()
        
        context = EventContext(
            session_id="test",
            opencode_client=mock_client,
            decision_agent=None,  # 没有决策 Agent
        )
        
        handler = QuestionAskHandler()
        
        # 创建带问题的事件
        event = create_mock_event(
            SSEEventType.QUESTION_ASKED,
            data={"question": "Test?"},
        )
        
        result = await handler.handle(event, context)
        
        # 没有决策 Agent 时，会返回错误
        assert result is not None
        assert result.handled is False  # 事件未被处理
        assert result.action == "error"  # 错误
        assert "No decision agent" in result.message  # 错误消息


# ==================== PermissionAskHandler 测试 ====================

class TestPermissionAskHandler:
    """权限请求处理器测试"""
    
    @pytest.mark.asyncio
    async def test_can_handle_permission(self):
        """测试能否处理权限事件"""
        handler = PermissionAskHandler()
        
        assert handler.can_handle(SSEEventType.PERMISSION_ASKED) is True
        assert handler.can_handle(SSEEventType.QUESTION_ASKED) is False
    
    @pytest.mark.asyncio
    async def test_auto_allow_safe_operation(self):
        """测试自动允许安全操作"""
        handler = PermissionAskHandler()
        
        # 检查自动规则
        result = handler._check_auto_rules("file_read", "/src/test.py")
        
        assert result is not None
        assert result.decision == PermissionDecision.ALLOW
        assert result.risk_level == "low"
    
    @pytest.mark.asyncio
    async def test_auto_deny_dangerous_operation(self):
        """测试自动拒绝危险操作"""
        handler = PermissionAskHandler()
        
        # 检查自动规则
        result = handler._check_auto_rules("file_read", ".env")
        
        assert result is not None
        assert result.decision == PermissionDecision.DENY
        assert result.risk_level == "high"
    
    @pytest.mark.asyncio
    async def test_handle_permission_safe(self):
        """测试处理安全权限请求"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        handler = PermissionAskHandler()
        
        # 创建带 raw_event 的事件
        raw = Mock()
        raw.permission_id = "p_safe"
        raw.type = "file_read"
        raw.resource = "/src/main.py"
        raw.agent = "Backend Developer"
        
        event = create_mock_event(
            SSEEventType.PERMISSION_ASKED,
            raw_event=raw,
        )
        
        result = await handler.handle(event, context)
        
        assert result.handled is True
        assert result.action == "allow"
        assert result.data.get("auto") is True
    
    @pytest.mark.asyncio
    async def test_handle_permission_dangerous(self):
        """测试处理危险权限请求"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        handler = PermissionAskHandler()
        
        # 创建带 raw_event 的事件
        raw = Mock()
        raw.permission_id = "p_danger"
        raw.type = "file_read"
        raw.resource = ".env"
        raw.agent = "Backend Developer"
        
        event = create_mock_event(
            SSEEventType.PERMISSION_ASKED,
            raw_event=raw,
        )
        
        result = await handler.handle(event, context)
        
        assert result.handled is True
        assert result.action == "deny"
        assert result.data.get("auto") is True
    
    @pytest.mark.asyncio
    async def test_handle_permission_needs_decision(self):
        """测试需要决策的权限请求"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        handler = PermissionAskHandler()
        
        # 不确定的操作，需要 LLM 决策（不在自动规则中）
        # 创建带 raw_event 的事件，这样 PermissionAskedEvent.from_sse_event 能正确解析
        raw = Mock()
        raw.permission_id = "p_test"
        raw.type = "command_execute"
        raw.resource = "npm run build"
        raw.agent = "Backend Developer"
        
        event = create_mock_event(
            SSEEventType.PERMISSION_ASKED,
            raw_event=raw,
        )
        
        result = await handler.handle(event, context)
        
        assert result.handled is True
        # 由于 npm run build 不在自动规则中，会调用决策 Agent
        assert decision_agent.permission_analyze_count == 1


# ==================== DefaultHandler 测试 ====================

class TestDefaultHandler:
    """默认处理器测试"""
    
    @pytest.mark.asyncio
    async def test_can_handle_all(self):
        """测试能处理所有事件"""
        handler = DefaultHandler()
        
        assert handler.can_handle(SSEEventType.MESSAGE_UPDATED) is True
        assert handler.can_handle(SSEEventType.SESSION_ERROR) is True
        assert handler.can_handle(SSEEventType.UNKNOWN) is True
    
    @pytest.mark.asyncio
    async def test_handle_unknown_event(self):
        """测试处理未知事件"""
        context = create_mock_context()
        handler = DefaultHandler()
        
        event = create_mock_event(SSEEventType.MESSAGE_UPDATED)
        
        result = await handler.handle(event, context)
        
        assert result.handled is True
        assert result.action == "logged"


# ==================== 责任链集成测试 ====================

class TestChainIntegration:
    """责任链集成测试"""
    
    @pytest.mark.asyncio
    async def test_question_handler_in_chain(self):
        """测试问题处理器在链中"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        
        chain = EventHandlerChain(context)
        chain.add_handler(QuestionAskHandler())
        chain.add_handler(PermissionAskHandler())
        chain.add_handler(DefaultHandler())
        
        event = create_mock_event(
            SSEEventType.QUESTION_ASKED,
            data={"question": "Test question"},
        )
        
        result = await chain.process(event)
        
        assert result.handled is True
        assert decision_agent.question_analyze_count == 1
    
    @pytest.mark.asyncio
    async def test_permission_handler_in_chain(self):
        """测试权限处理器在链中"""
        decision_agent = MockDecisionAgent()
        context = create_mock_context(decision_agent)
        
        chain = EventHandlerChain(context)
        chain.add_handler(QuestionAskHandler())
        chain.add_handler(PermissionAskHandler())
        chain.add_handler(DefaultHandler())
        
        # 创建带 raw_event 的事件
        raw = Mock()
        raw.permission_id = "p_chain"
        raw.type = "command_execute"
        raw.resource = "npm run build"
        raw.agent = "Backend Developer"
        
        event = create_mock_event(
            SSEEventType.PERMISSION_ASKED,
            raw_event=raw,
        )
        
        result = await chain.process(event)
        
        assert result.handled is True
        assert decision_agent.permission_analyze_count == 1
    
    @pytest.mark.asyncio
    async def test_default_handler_fallback(self):
        """测试默认处理器兜底"""
        context = create_mock_context()
        
        chain = EventHandlerChain(context)
        chain.add_handler(QuestionAskHandler())
        chain.add_handler(PermissionAskHandler())
        chain.add_handler(DefaultHandler())
        
        # 其他事件类型
        event = create_mock_event(SSEEventType.SESSION_ERROR)
        
        result = await chain.process(event)
        
        assert result.handled is True
        assert result.action == "logged"


# ==================== EventContext 测试 ====================

class TestEventContext:
    """事件上下文测试"""
    
    def test_create_context(self):
        """测试创建上下文"""
        mock_client = Mock()
        mock_agent = Mock()
        
        context = EventContext(
            session_id="test",
            opencode_client=mock_client,
            decision_agent=mock_agent,
        )
        
        assert context.session_id == "test"
        assert context.get_sdk() == mock_client
        assert context.get_decision_agent() == mock_agent


# ==================== EventResult 测试 ====================

class TestEventResult:
    """事件处理结果测试"""
    
    def test_create_result(self):
        """测试创建结果"""
        result = EventResult(
            handled=True,
            action="answered",
            message="Test answer",
        )
        
        assert result.handled is True
        assert result.action == "answered"
        assert result.message == "Test answer"
    
    def test_result_defaults(self):
        """测试默认结果"""
        result = EventResult(handled=False)
        
        assert result.handled is False
        assert result.action is None
        assert result.message is None


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
