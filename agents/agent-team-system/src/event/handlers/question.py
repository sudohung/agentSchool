"""问题询问事件处理器."""

from __future__ import annotations

import logging
from typing import Optional

from event.chain import (
    EventHandler,
    SSEEventType,
    SSEEvent,
    QuestionAskedEvent,
    EventContext,
    EventResult,
)

logger = logging.getLogger(__name__)


class QuestionAskHandler(EventHandler):
    """
    问题询问事件处理器
    
    职责：
    1. 处理 question_asked 事件
    2. 调用决策 Agent 分析问题
    3. 通过 SDK 回答问题
    """
    
    def can_handle(self, event_type: SSEEventType) -> bool:
        """判断是否能处理该事件"""
        return event_type == SSEEventType.QUESTION_ASKED
    
    async def handle(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> Optional[EventResult]:
        """
        处理问题询问事件
        
        流程：
        1. 解析问题详情
        2. 调用决策 Agent 分析
        3. 通过 SDK 回答
        """
        logger.info(f"🎯 Processing question_asked event: {event.id}")
        
        # 解析问题
        question_event = QuestionAskedEvent.from_sse_event(event)
        
        question_id = question_event.question_id
        question = question_event.question
        options = question_event.options
        
        logger.info(f"❓ Question: {question}")
        if options:
            logger.info(f"   Options: {options}")
        
        # 获取决策 Agent
        decision_agent = context.get_decision_agent()
        if not decision_agent:
            logger.warning("No decision agent available")
            return EventResult(
                handled=False,
                action="error",
                message="No decision agent available",
            )
        
        try:
            # 调用决策 Agent 分析并回答
            answer = await decision_agent.analyze_question(
                question=question,
                options=options,
                context=question_event.context,
            )
            
            logger.info(f"💡 Decision Agent answer: {answer}")
            
            # 通过 SDK 回答问题
            await self._answer_question(
                context=context,
                question_id=question_id,
                answer=answer,
            )
            
            return EventResult(
                handled=True,
                action="answered",
                message=answer,
                data={"question_id": question_id, "answer": answer},
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return EventResult(
                handled=False,
                action="error",
                message=str(e),
            )
    
    async def _answer_question(
        self,
        context: EventContext,
        question_id: str,
        answer: str,
    ):
        """
        通过 SDK 回答问题
        
        Args:
            context: 事件上下文
            question_id: 问题 ID
            answer: 回答内容
        """
        client = context.get_sdk()
        if not client:
            raise RuntimeError("No OpenCode client available")
        
        try:
            # 使用 OpenCode SDK 回答问题
            # client.question.answer(question_id=question_id, answer=answer)
            if hasattr(client, 'question') and hasattr(client.question, 'answer'):
                client.question.answer(
                    question_id=question_id,
                    answer=answer,
                )
                logger.info(f"✅ Answered question {question_id}")
            else:
                # 备用方案：通过消息发送回答
                logger.warning("question.answer API not available, using message")
                await self._send_answer_as_message(
                    context=context,
                    question_id=question_id,
                    answer=answer,
                )
        except Exception as e:
            logger.error(f"Failed to answer question via SDK: {e}")
            raise
    
    async def _send_answer_as_message(
        self,
        context: EventContext,
        question_id: str,
        answer: str,
    ):
        """通过消息发送回答（备用方案）"""
        client = context.get_sdk()
        session_id = context.session_id
        
        if hasattr(client, 'message') and hasattr(client.message, 'send_text'):
            client.message.send_text(
                session_id=session_id,
                text=f"[Question Answer] {answer}",
            )
            logger.info(f"✅ Sent answer as message for question {question_id}")