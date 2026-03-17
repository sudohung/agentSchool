"""决策 Agent - 用于处理 question_asked 和 permission_asked 事件."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from agent.base import Agent
from agent.config import AgentConfig, AgentStatus
from event.handlers.permission import PermissionDecision, PermissionAnalysis

logger = logging.getLogger(__name__)


class DecisionAgent(Agent):
    """
    决策 Agent
    
    角色：Team 内的决策者，负责处理需要人工判断的事件
    
    核心职责：
    1. 分析问题并做出回答
    2. 分析权限请求并做出允许/拒绝决策
    3. 通过 LLM 进行智能决策
    
    专业技能：
    - 决策分析
    - 风险评估
    - 策略制定
    """
    
    def __init__(
        self,
        session: Any = None,
        client: Any = None,
        config: Optional[AgentConfig] = None,
    ):
        """初始化决策 Agent"""
        if config is None:
            config = AgentConfig(
                role="Decision Agent",
                expertise=[
                    "决策分析",
                    "风险评估",
                    "策略制定",
                    "问题分析",
                    "安全判断",
                ],
                max_iterations=10,
            )
        
        super().__init__(
            role="Decision Agent",
            expertise=[
                "决策分析",
                "风险评估",
                "策略制定",
                "问题分析",
                "安全判断",
            ],
            session=session,
            client=client,
            config=config,
        )
        
        # 决策历史
        self._decision_history: List[Dict[str, Any]] = []
        
        # 决策策略配置
        self._decision_config = {
            # 自动决策阈值
            "auto_answer_threshold": 0.8,  # 置信度超过此值自动回答
            "auto_allow_threshold": 0.9,   # 置信度超过此值自动允许
            
            # 风险容忍度
            "risk_tolerance": "medium",  # low, medium, high
            
            # 安全模式
            "safe_mode": True,  # 安全模式下更谨慎
        }
    
    # ==================== 核心决策方法 ====================
    
    async def analyze_question(
        self,
        question: Optional[str],
        options: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        分析问题并生成回答
        
        Args:
            question: 问题内容
            options: 可选选项
            context: 上下文信息
            
        Returns:
            回答内容
        """
        logger.info(f"🔍 Analyzing question: {question}")
        
        if not question:
            return "I need more information to answer this question."
        
        # 构建决策提示
        prompt = self._build_question_prompt(question, options, context)
        
        # 使用 LLM 进行决策
        response = await self.send_message(prompt)
        
        # 提取回答
        answer = self._extract_answer(response, options)
        
        # 记录决策历史
        self._record_decision(
            decision_type="question",
            input_data={"question": question, "options": options},
            output_data={"answer": answer},
        )
        
        logger.info(f"💡 Decision made: {answer[:100]}...")
        return answer
    
    async def analyze_permission(
        self,
        permission_type: Optional[str],
        resource: Optional[str],
        agent_role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PermissionAnalysis:
        """
        分析权限请求并做出决策
        
        Args:
            permission_type: 权限类型 (file_read, file_write, command_execute)
            resource: 资源路径
            agent_role: 请求权限的 Agent 角色
            context: 上下文信息
            
        Returns:
            权限分析结果
        """
        logger.info(f"🔐 Analyzing permission: {permission_type} for {resource}")
        
        if not permission_type or not resource:
            return PermissionAnalysis(
                decision=PermissionDecision.DENY,
                reason="Invalid permission request",
                risk_level="unknown",
                confidence=0.0,
            )
        
        # 1. 安全检查 - 高风险操作直接拒绝
        if self._is_dangerous_operation(permission_type, resource):
            logger.warning(f"⚠️ Dangerous operation detected: {permission_type} {resource}")
            return PermissionAnalysis(
                decision=PermissionDecision.DENY,
                reason=f"Dangerous operation: {permission_type} on {resource}",
                risk_level="high",
                confidence=1.0,
            )
        
        # 2. 快速判断 - 安全操作直接允许
        if self._is_safe_operation(permission_type, resource):
            logger.info(f"✅ Safe operation: {permission_type} {resource}")
            return PermissionAnalysis(
                decision=PermissionDecision.ALLOW,
                reason=f"Safe operation: {permission_type} on {resource}",
                risk_level="low",
                confidence=1.0,
            )
        
        # 3. 需要 LLM 分析的情况
        prompt = self._build_permission_prompt(
            permission_type, resource, agent_role, context
        )
        
        response = await self.send_message(prompt)
        
        # 解析 LLM 响应
        analysis = self._parse_permission_response(response)
        
        # 记录决策历史
        self._record_decision(
            decision_type="permission",
            input_data={
                "permission_type": permission_type,
                "resource": resource,
                "agent_role": agent_role,
            },
            output_data={
                "decision": analysis.decision.value,
                "reason": analysis.reason,
                "risk_level": analysis.risk_level,
            },
        )
        
        logger.info(
            f"🤖 Permission decision: {analysis.decision.value} "
            f"(risk: {analysis.risk_level}, confidence: {analysis.confidence})"
        )
        
        return analysis
    
    # ==================== 提示构建方法 ====================
    
    def _build_question_prompt(
        self,
        question: str,
        options: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """构建问题分析提示"""
        prompt_parts = [
            "You are the Decision Agent in an AI agent team.",
            "Your role is to analyze questions and provide clear, actionable answers.",
            "",
            "## Current Question",
            f"Question: {question}",
        ]
        
        if options:
            prompt_parts.append(f"Options: {', '.join(options)}")
        
        if context:
            prompt_parts.append(f"\n## Context\n{context}")
        
        prompt_parts.extend([
            "",
            "## Task",
            "1. Analyze the question carefully",
            "2. Consider the context and available information",
            "3. Provide a clear, concise answer",
            "",
            "## Response Format",
            "Provide your answer directly. If options are provided, select one.",
            "Be decisive and clear. Do not be ambiguous.",
            "",
            "Your answer:",
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_permission_prompt(
        self,
        permission_type: str,
        resource: str,
        agent_role: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """构建权限分析提示"""
        prompt_parts = [
            "You are the Decision Agent in an AI agent team.",
            "Your role is to analyze permission requests and make security decisions.",
            "",
            "## Permission Request",
            f"Type: {permission_type}",
            f"Resource: {resource}",
        ]
        
        if agent_role:
            prompt_parts.append(f"Requesting Agent: {agent_role}")
        
        if context:
            prompt_parts.append(f"\n## Context\n{context}")
        
        prompt_parts.extend([
            "",
            "## Task",
            "Analyze this permission request and decide: ALLOW or DENY",
            "",
            "## Considerations",
            "1. Is this a sensitive file/directory? (.env, credentials, secrets)",
            "2. Is this a destructive operation? (rm, delete, format)",
            "3. Is the requesting agent trustworthy for this operation?",
            "4. What is the potential impact of this operation?",
            "",
            "## Response Format",
            "DECISION: [ALLOW/DENY]",
            "RISK_LEVEL: [low/medium/high]",
            "CONFIDENCE: [0.0-1.0]",
            "REASON: [Brief explanation]",
            "",
            "Your response:",
        ])
        
        return "\n".join(prompt_parts)
    
    # ==================== 响应解析方法 ====================
    
    def _extract_answer(
        self,
        response: Any,
        options: Optional[List[str]],
    ) -> str:
        """从 LLM 响应中提取回答"""
        if response is None:
            return "Unable to determine answer."
        
        # 提取文本内容
        text = ""
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'text'):
                    text += part.text
        elif isinstance(response, str):
            text = response
        else:
            text = str(response)
        
        # 如果有选项，尝试匹配
        if options:
            text_lower = text.lower()
            for option in options:
                if option.lower() in text_lower:
                    return option
        
        # 返回清理后的回答
        return text.strip()[:500]  # 限制长度
    
    def _parse_permission_response(self, response: Any) -> PermissionAnalysis:
        """解析权限分析响应"""
        default = PermissionAnalysis(
            decision=PermissionDecision.DENY,
            reason="Unable to parse LLM response",
            risk_level="medium",
            confidence=0.5,
        )
        
        if response is None:
            return default
        
        # 提取文本
        text = ""
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'text'):
                    text += part.text
        elif isinstance(response, str):
            text = response
        else:
            text = str(response)
        
        # 解析响应
        decision = PermissionDecision.DENY
        risk_level = "medium"
        confidence = 0.5
        reason = "LLM analysis"
        
        text_upper = text.upper()
        
        # 解析决策
        if "ALLOW" in text_upper and "DENY" not in text_upper.split("ALLOW")[0]:
            decision = PermissionDecision.ALLOW
        elif "DENY" in text_upper:
            decision = PermissionDecision.DENY
        
        # 解析风险等级
        if "RISK_LEVEL:" in text_upper or "RISK:" in text_upper:
            if "HIGH" in text_upper:
                risk_level = "high"
            elif "LOW" in text_upper:
                risk_level = "low"
            else:
                risk_level = "medium"
        
        # 解析置信度
        if "CONFIDENCE:" in text_upper:
            import re
            match = re.search(r'CONFIDENCE:\s*([\d.]+)', text_upper)
            if match:
                try:
                    confidence = float(match.group(1))
                    confidence = max(0.0, min(1.0, confidence))
                except ValueError:
                    pass
        
        # 解析原因
        if "REASON:" in text_upper:
            idx = text_upper.find("REASON:")
            reason = text[idx + 7:].strip().split("\n")[0][:200]
        
        return PermissionAnalysis(
            decision=decision,
            reason=reason,
            risk_level=risk_level,
            confidence=confidence,
        )
    
    # ==================== 安全检查方法 ====================
    
    def _is_dangerous_operation(self, permission_type: str, resource: str) -> bool:
        """检查是否是危险操作"""
        dangerous_patterns = [
            # 敏感文件
            ".env", "credentials", "secrets", "password", "key", "token",
            # 危险命令
            "rm -rf", "sudo", "chmod 777", "format", "mkfs",
        ]
        
        resource_lower = resource.lower()
        
        for pattern in dangerous_patterns:
            if pattern in resource_lower:
                return True
        
        # 危险权限类型
        if permission_type == "command_execute":
            dangerous_commands = ["rm", "sudo", "chmod", "chown", "mkfs", "dd"]
            for cmd in dangerous_commands:
                if cmd in resource_lower:
                    return True
        
        return False
    
    def _is_safe_operation(self, permission_type: str, resource: str) -> bool:
        """检查是否是安全操作"""
        safe_patterns = [
            # 安全目录
            "/src/", "/lib/", "/docs/", "/tests/",
            # 安全命令
            "git status", "git log", "npm list", "pip list", "ls", "cat",
        ]
        
        resource_lower = resource.lower()
        
        for pattern in safe_patterns:
            if pattern in resource_lower:
                return True
        
        return False
    
    # ==================== 历史记录方法 ====================
    
    def _record_decision(
        self,
        decision_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ):
        """记录决策历史"""
        import time
        self._decision_history.append({
            "timestamp": int(time.time()),
            "type": decision_type,
            "input": input_data,
            "output": output_data,
        })
        
        # 限制历史长度
        if len(self._decision_history) > 100:
            self._decision_history = self._decision_history[-100:]
    
    def get_decision_history(
        self,
        decision_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """获取决策历史"""
        history = self._decision_history
        
        if decision_type:
            history = [d for d in history if d["type"] == decision_type]
        
        return history[-limit:]
    
    # ==================== Ralph Loop 抽象方法实现 ====================
    
    async def read_documents(self):
        """R - 阅读文档"""
        # 决策 Agent 主要响应事件，不需要主动阅读文档
        return []
    
    async def act_on_requests(self):
        """A - 响应诉求"""
        # 决策 Agent 主要通过事件触发，不需要主动响应诉求
        return []
    
    async def leverage_expertise(self):
        """L - 发挥专业能力"""
        # 决策 Agent 主要通过 analyze_question 和 analyze_permission 发挥能力
        return None
    
    async def produce_document(self):
        """P - 产出文档"""
        # 决策 Agent 主要输出决策结果，不产出文档
        return None
    
    async def help_requests(self):
        """H - 发布诉求"""
        # 决策 Agent 通常不需要发布诉求
        return []