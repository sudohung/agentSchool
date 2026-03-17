"""权限请求事件处理器."""

from __future__ import annotations

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from event.chain import (
    EventHandler,
    SSEEventType,
    SSEEvent,
    PermissionAskedEvent,
    EventContext,
    EventResult,
)

logger = logging.getLogger(__name__)


class PermissionDecision(Enum):
    """权限决策"""
    ALLOW = "allow"          # 允许
    DENY = "deny"            # 拒绝
    ASK_USER = "ask_user"   # 询问用户


@dataclass
class PermissionAnalysis:
    """权限分析结果"""
    decision: PermissionDecision
    reason: str
    risk_level: str  # low, medium, high
    confidence: float  # 0.0 - 1.0


class PermissionAskHandler(EventHandler):
    """
    权限请求事件处理器
    
    职责：
    1. 处理 permission_asked 事件
    2. 调用决策 Agent 分析风险
    3. 通过 SDK 授权或拒绝
    """
    
    # 自动允许的安全规则
    AUTO_ALLOW_PATTERNS = {
        # 文件读取 - 源代码目录
        ("file_read", "/src/"),
        ("file_read", "/lib/"),
        ("file_read", "/docs/"),
        # 常见安全命令
        ("command_execute", "git status"),
        ("command_execute", "npm list"),
        ("command_execute", "pip list"),
    }
    
    # 自动拒绝的危险规则
    AUTO_DENY_PATTERNS = {
        # 敏感文件
        ("file_read", ".env"),
        ("file_read", "credentials"),
        ("file_read", "secrets"),
        ("file_write", ".env"),
        ("file_write", "credentials"),
        # 危险命令
        ("command_execute", "rm -rf /"),
        ("command_execute", "sudo"),
        ("command_execute", "chmod 777"),
    }
    
    def can_handle(self, event_type: SSEEventType) -> bool:
        """判断是否能处理该事件"""
        return event_type == SSEEventType.PERMISSION_ASKED
    
    async def handle(
        self,
        event: SSEEvent,
        context: EventContext,
    ) -> Optional[EventResult]:
        """
        处理权限请求事件
        
        流程：
        1. 解析权限详情
        2. 检查自动规则
        3. 调用决策 Agent 分析（如需要）
        4. 通过 SDK 授权或拒绝
        """
        logger.info(f"🔐 Processing permission_asked event: {event.id}")
        
        # 解析权限请求
        permission_event = PermissionAskedEvent.from_sse_event(event)
        
        permission_id = permission_event.permission_id
        permission_type = permission_event.permission_type
        resource = permission_event.resource
        agent_role = permission_event.agent_role
        
        logger.info(f"   Type: {permission_type}")
        logger.info(f"   Resource: {resource}")
        logger.info(f"   Agent: {agent_role}")
        
        # 1. 检查自动规则
        auto_decision = self._check_auto_rules(permission_type, resource)
        if auto_decision:
            logger.info(f"⚡ Auto decision: {auto_decision.decision.value}")
            await self._respond_permission(
                context=context,
                permission_id=permission_id,
                decision=auto_decision.decision,
                reason=auto_decision.reason,
            )
            return EventResult(
                handled=True,
                action=auto_decision.decision.value,
                message=auto_decision.reason,
                data={
                    "permission_id": permission_id,
                    "auto": True,
                    "risk_level": auto_decision.risk_level,
                },
            )
        
        # 2. 调用决策 Agent 分析
        decision_agent = context.get_decision_agent()
        if not decision_agent:
            logger.warning("No decision agent available, defaulting to deny")
            await self._respond_permission(
                context=context,
                permission_id=permission_id,
                decision=PermissionDecision.DENY,
                reason="No decision agent available",
            )
            return EventResult(
                handled=True,
                action="deny",
                message="No decision agent available",
            )
        
        try:
            # 调用决策 Agent 分析权限
            analysis = await decision_agent.analyze_permission(
                permission_type=permission_type,
                resource=resource,
                agent_role=agent_role,
                context=permission_event.context,
            )
            
            logger.info(f"🤖 Decision Agent analysis:")
            logger.info(f"   Decision: {analysis.decision.value}")
            logger.info(f"   Risk: {analysis.risk_level}")
            logger.info(f"   Reason: {analysis.reason}")
            
            # 响应权限请求
            await self._respond_permission(
                context=context,
                permission_id=permission_id,
                decision=analysis.decision,
                reason=analysis.reason,
            )
            
            return EventResult(
                handled=True,
                action=analysis.decision.value,
                message=analysis.reason,
                data={
                    "permission_id": permission_id,
                    "risk_level": analysis.risk_level,
                    "confidence": analysis.confidence,
                },
            )
            
        except Exception as e:
            logger.error(f"Error analyzing permission: {e}")
            return EventResult(
                handled=False,
                action="error",
                message=str(e),
            )
    
    def _check_auto_rules(
        self,
        permission_type: str,
        resource: str,
    ) -> Optional[PermissionAnalysis]:
        """
        检查自动规则
        
        Args:
            permission_type: 权限类型
            resource: 资源路径
            
        Returns:
            自动决策结果，如果没有匹配规则则返回 None
        """
        if not permission_type or not resource:
            return None
        
        permission_type = permission_type.lower()
        resource_lower = resource.lower()
        
        # 检查自动拒绝规则
        for pattern_type, pattern_resource in self.AUTO_DENY_PATTERNS:
            if pattern_type.lower() == permission_type and pattern_resource.lower() in resource_lower:
                return PermissionAnalysis(
                    decision=PermissionDecision.DENY,
                    reason=f"Auto-deny: matches dangerous pattern '{pattern_resource}'",
                    risk_level="high",
                    confidence=1.0,
                )
        
        # 检查自动允许规则
        for pattern_type, pattern_resource in self.AUTO_ALLOW_PATTERNS:
            if pattern_type.lower() == permission_type and pattern_resource.lower() in resource_lower:
                return PermissionAnalysis(
                    decision=PermissionDecision.ALLOW,
                    reason=f"Auto-allow: matches safe pattern '{pattern_resource}'",
                    risk_level="low",
                    confidence=1.0,
                )
        
        return None
    
    async def _respond_permission(
        self,
        context: EventContext,
        permission_id: str,
        decision: PermissionDecision,
        reason: str,
    ):
        """
        通过 SDK 响应权限请求
        
        Args:
            context: 事件上下文
            permission_id: 权限 ID
            decision: 决策结果
            reason: 决策原因
        """
        client = context.get_sdk()
        if not client:
            raise RuntimeError("No OpenCode client available")
        
        try:
            # 使用 OpenCode SDK 响应权限
            if hasattr(client, 'permission') and hasattr(client.permission, 'respond'):
                client.permission.respond(
                    permission_id=permission_id,
                    allow=(decision == PermissionDecision.ALLOW),
                    reason=reason,
                )
                action = "allowed" if decision == PermissionDecision.ALLOW else "denied"
                logger.info(f"✅ Permission {action}: {permission_id}")
            else:
                # 备用方案
                logger.warning("permission.respond API not available")
                raise NotImplementedError("Permission API not available in SDK")
                
        except Exception as e:
            logger.error(f"Failed to respond to permission via SDK: {e}")
            raise