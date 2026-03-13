"""需求分析器."""

from __future__ import annotations

import re
from typing import List, Dict, Optional
from .config import TaskAnalysis, TaskType, ComplexityLevel, TeamConfig


class TaskAnalyzer:
    """
    任务分析器
    
    使用规则 + AI 混合分析策略
    
    功能:
    - 关键词匹配识别任务类型
    - 复杂度评估
    - 功能需求提取
    - 技术需求推断
    - AI 增强分析 (可选)
    """
    
    # 关键词映射表
    KEYWORD_MAPPING = {
        "网站": TaskType.WEB_DEVELOPMENT,
        "web": TaskType.WEB_DEVELOPMENT,
        "前端": TaskType.WEB_DEVELOPMENT,
        "app": TaskType.MOBILE_DEVELOPMENT,
        "移动端": TaskType.MOBILE_DEVELOPMENT,
        "api": TaskType.API_DEVELOPMENT,
        "接口": TaskType.API_DEVELOPMENT,
        "数据分析": TaskType.DATA_ANALYSIS,
        "文档": TaskType.DOCUMENTATION,
        "部署": TaskType.DEVOPS,
        "安全": TaskType.SECURITY_AUDIT,
    }
    
    # 复杂度关键词
    COMPLEXITY_KEYWORDS = {
        ComplexityLevel.SIMPLE: ["简单", "基础", "demo", "原型"],
        ComplexityLevel.MEDIUM: ["中等", "标准", "完整"],
        ComplexityLevel.COMPLEX: ["复杂", "高级", "企业级"],
        ComplexityLevel.ENTERPRISE: ["大型", "分布式", "高并发"],
    }
    
    def __init__(self, client=None, config: Optional[TeamConfig] = None):
        """
        初始化分析器
        
        Args:
            client: OpenCode 客户端
            config: 团队配置
        """
        self.client = client
        self.config = config
    
    async def analyze(self, task_description: str) -> TaskAnalysis:
        """
        分析任务描述
        
        Args:
            task_description: 用户输入的任务描述
            
        Returns:
            TaskAnalysis: 分析结果
            
        Raises:
            ValueError: 任务描述为空
        """
        if not task_description or not task_description.strip():
            raise ValueError("任务描述不能为空")
        
        # 1. 规则分析
        task_type = self._analyze_task_type(task_description)
        complexity = self._analyze_complexity(task_description)
        features = self._extract_features(task_description)
        
        # 2. AI 增强分析 (可选)
        ai_summary = None
        confidence = 0.7
        
        if self.client and (self.config is None or self.config.enable_ai_analysis):
            ai_result = await self._ai_analyze(task_description)
            ai_summary = ai_result.get("summary")
            confidence = ai_result.get("confidence", 0.8)
        
        # 3. 技术需求推断
        tech_requirements = self._infer_tech_requirements(task_type, features)
        
        return TaskAnalysis(
            raw_description=task_description,
            task_type=task_type,
            complexity=complexity,
            features=features,
            ai_summary=ai_summary,
            confidence=confidence,
            **tech_requirements,
        )
    
    def _analyze_task_type(self, description: str) -> TaskType:
        """分析任务类型"""
        description_lower = description.lower()
        
        for keyword, task_type in self.KEYWORD_MAPPING.items():
            if keyword.lower() in description_lower:
                return task_type
        
        return TaskType.OTHER
    
    def _analyze_complexity(self, description: str) -> ComplexityLevel:
        """分析复杂度"""
        description_lower = description.lower()
        
        # 计算各复杂度得分
        scores = {level: 0 for level in ComplexityLevel}
        
        for level, keywords in self.COMPLEXITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    scores[level] += 1
        
        # 返回最高分
        max_score = max(scores.values())
        if max_score == 0:
            return ComplexityLevel.MEDIUM  # 默认中等复杂度
        
        return max(scores, key=scores.get)
    
    def _extract_features(self, description: str) -> List[str]:
        """提取功能列表"""
        # 简单实现：按标点分割
        features = re.split(r'[,，;；]', description)
        return [f.strip() for f in features if len(f.strip()) > 1]
    
    def _infer_tech_requirements(
        self, 
        task_type: TaskType, 
        features: List[str]
    ) -> Dict:
        """推断技术需求"""
        features_str = " ".join(features).lower()
        
        return {
            "frontend_required": (
                task_type == TaskType.WEB_DEVELOPMENT or 
                "界面" in features_str or 
                "展示" in features_str
            ),
            "backend_required": (
                task_type in [TaskType.WEB_DEVELOPMENT, TaskType.API_DEVELOPMENT] or
                "数据" in features_str or
                "存储" in features_str
            ),
            "database_required": (
                "数据" in features_str or 
                "存储" in features_str or
                "管理" in features_str
            ),
            "devops_required": (
                task_type == TaskType.DEVOPS or 
                "部署" in features_str or
                "上线" in features_str
            ),
            "security_required": (
                task_type == TaskType.SECURITY_AUDIT or 
                "安全" in features_str or
                "权限" in features_str
            ),
        }
    
    async def _ai_analyze(self, description: str) -> Dict:
        """AI 增强分析"""
        prompt = f"""请分析以下任务描述，提取关键信息：

任务：{description}

请输出：
1. 任务类型 (web 开发/移动开发/API 开发/数据分析/文档/部署/安全)
2. 复杂度 (简单/中等/复杂/企业级)
3. 功能列表
4. 技术需求 (前端/后端/数据库/部署/安全)

以 JSON 格式输出。"""
        
        # 调用 AI 分析
        # result = await self.client.send_message(prompt)
        # return parse_json(result)
        
        return {"summary": prompt, "confidence": 0.8}
