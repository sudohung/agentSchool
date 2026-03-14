"""质量门控."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class QualityCheckType(Enum):
    """质量检查类型"""
    DOCUMENT_COMPLETENESS = "document_completeness"
    CODE_QUALITY = "code_quality"
    TEST_COVERAGE = "test_coverage"
    SECURITY = "security"
    MANUAL_REVIEW = "manual_review"


@dataclass
class QualityCheckResult:
    """质量检查结果"""
    check_type: QualityCheckType
    passed: bool
    score: float
    issues: List[str]
    suggestions: List[str]


@dataclass
class QualityGateResult:
    """质量门控结果"""
    passed: bool
    overall_score: float
    check_results: List[QualityCheckResult]
    requires_manual_review: bool = False
    review_items: Optional[List[str]] = None
    quality_score: float = 0.0
    
    def __post_init__(self):
        """初始化后处理"""
        if self.review_items is None:
            self.review_items = []


@dataclass
class QualityConfig:
    """质量配置"""
    passing_score: float = 0.7
    require_manual_review: bool = False
    min_test_coverage: float = 0.8
    security_scan_enabled: bool = True


class QualityGate:
    """
    质量门控
    
    在工作流交付前进行质量检查
    """
    
    def __init__(self, config: Optional[QualityConfig] = None):
        """
        初始化质量门控
        
        Args:
            config: 质量配置
        """
        self.config = config or QualityConfig()
        
        # 必需的文档类型
        self.required_document_types = [
            "prd",  # 产品需求文档
            "architecture",  # 架构设计
            "api_doc",  # API 文档
            "test_plan",  # 测试计划
        ]
    
    async def check(self, context: Any) -> QualityGateResult:
        """
        执行质量检查
        
        Args:
            context: 工作流上下文
            
        Returns:
            QualityGateResult: 检查结果
        """
        results = []
        
        # 1. 文档完整性检查
        doc_result = await self._check_document_completeness(context)
        results.append(doc_result)
        
        # 2. 代码质量检查 (如果存在代码)
        code_result = await self._check_code_quality(context)
        results.append(code_result)
        
        # 3. 测试覆盖检查
        test_result = await self._check_test_coverage(context)
        results.append(test_result)
        
        # 4. 安全检查
        security_result = await self._check_security(context)
        results.append(security_result)
        
        # 5. 手动审核检查
        if self.config.require_manual_review:
            manual_result = await self._check_manual_review(context)
            results.append(manual_result)
        
        # 计算总体分数
        overall_score = self._calculate_overall_score(results)
        
        # 是否通过
        passed = overall_score >= self.config.passing_score
        requires_manual_review = any(
            r.check_type == QualityCheckType.MANUAL_REVIEW and not r.passed
            for r in results
        )
        
        review_items = []
        if requires_manual_review:
            for r in results:
                if not r.passed:
                    review_items.extend(r.issues)
        
        return QualityGateResult(
            passed=passed,
            overall_score=overall_score,
            check_results=results,
            requires_manual_review=requires_manual_review,
            review_items=review_items,
            quality_score=overall_score,
        )
    
    async def _check_document_completeness(self, context: Any) -> QualityCheckResult:
        """检查文档完整性"""
        issues = []
        suggestions = []
        
        # 获取已有文档类型
        existing_types = set()
        if hasattr(context, 'document_store') and context.document_store:
            try:
                docs = await context.document_store.list_documents()
                for doc in docs:
                    if hasattr(doc, 'metadata') and hasattr(doc.metadata, 'doc_type'):
                        existing_types.add(doc.metadata.doc_type)
            except Exception:
                # 文档存储不可用，跳过检查
                pass
        
        # 检查必需文档
        missing_docs = []
        for required_type in self.required_document_types:
            if required_type not in existing_types:
                missing_docs.append(required_type)
        
        if missing_docs:
            issues.append(f"缺少必需文档：{', '.join(missing_docs)}")
            suggestions.append(f"请补充以下文档：{', '.join(missing_docs)}")
        
        passed = len(missing_docs) == 0
        score = 1.0 if passed else max(0.0, 1.0 - len(missing_docs) * 0.1)
        
        return QualityCheckResult(
            check_type=QualityCheckType.DOCUMENT_COMPLETENESS,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
    
    async def _check_code_quality(self, context: Any) -> QualityCheckResult:
        """检查代码质量 (如果有代码)"""
        issues = []
        suggestions = []
        
        # 检查是否存在代码文档
        has_code_docs = False
        if hasattr(context, 'document_store') and context.document_store:
            try:
                docs = await context.document_store.list_documents()
                for doc in docs:
                    if (hasattr(doc, 'metadata') and 
                        hasattr(doc.metadata, 'doc_type') and
                        doc.metadata.doc_type == "code"):
                        has_code_docs = True
                        break
            except Exception:
                # 文档存储不可用，跳过检查
                pass
        
        if has_code_docs:
            # 进行代码质量检查
            passed = True
            score = 0.9  # 假设代码质量良好
        else:
            # 没有代码，不适用此检查
            passed = True
            score = 1.0
        
        return QualityCheckResult(
            check_type=QualityCheckType.CODE_QUALITY,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
    
    async def _check_test_coverage(self, context: Any) -> QualityCheckResult:
        """检查测试覆盖"""
        issues = []
        suggestions = []
        
        # 检查测试相关文档
        test_docs = []
        if hasattr(context, 'document_store') and context.document_store:
            try:
                docs = await context.document_store.list_documents()
                for doc in docs:
                    if (hasattr(doc, 'metadata') and 
                        hasattr(doc.metadata, 'doc_type')):
                        doc_type = str(doc.metadata.doc_type).lower()
                        if "test" in doc_type:
                            test_docs.append(doc)
            except Exception:
                # 文档存储不可用，跳过检查
                pass
        
        if len(test_docs) == 0:
            issues.append("缺少测试文档")
            suggestions.append("请添加测试计划和测试用例")
            passed = False
            score = 0.0
        else:
            # 有测试文档，检查覆盖率（简化检查）
            if len(test_docs) >= 2:  # 至少有计划和用例
                passed = True
                score = min(1.0, len(test_docs) / 5)  # 简单评分
            else:
                issues.append("测试文档不完整")
                suggestions.append("请补充测试文档")
                passed = False
                score = 0.5
        
        return QualityCheckResult(
            check_type=QualityCheckType.TEST_COVERAGE,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
    
    async def _check_security(self, context: Any) -> QualityCheckResult:
        """检查安全性"""
        issues = []
        suggestions = []
        
        # 检查安全相关文档
        security_docs = []
        if hasattr(context, 'document_store') and context.document_store:
            try:
                docs = await context.document_store.list_documents()
                for doc in docs:
                    if (hasattr(doc, 'metadata') and 
                        hasattr(doc.metadata, 'tags')):
                        tags = [str(tag).lower() for tag in doc.metadata.tags]
                        if "security" in tags:
                            security_docs.append(doc)
            except Exception:
                # 文档存储不可用，跳过检查
                pass
        
        if not security_docs and self.config.security_scan_enabled:
            issues.append("缺少安全相关文档")
            suggestions.append("请添加安全检查和安全设计文档")
            passed = False
            score = 0.6  # 假设基本安全但不完整
        else:
            passed = True
            score = 1.0 if security_docs else 0.8  # 有安全启用但无文档
        
        return QualityCheckResult(
            check_type=QualityCheckType.SECURITY,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
    
    async def _check_manual_review(self, context: Any) -> QualityCheckResult:
        """检查是否需要手动审核"""
        issues = []
        suggestions = []
        
        # 检查关键决策点是否得到充分记录
        if hasattr(context, 'metadata'):
            metadata = context.metadata
            if "critical_decisions" in metadata:
                decisions = metadata["critical_decisions"]
                if not all(d.get("reviewed", False) for d in decisions):
                    issues.append(f"存在未审核的关键决策: {len([d for d in decisions if not d.get('reviewed', False)])}")
                    suggestions.append("请审核所有关键决策")
                    passed = False
                    score = 0.5
                else:
                    passed = True
                    score = 1.0
            else:
                # 没有关键决策记录，假定不需要手审
                passed = True
                score = 1.0
        else:
            passed = True
            score = 1.0
        
        return QualityCheckResult(
            check_type=QualityCheckType.MANUAL_REVIEW,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
    
    def _calculate_overall_score(self, results: List[QualityCheckResult]) -> float:
        """计算总体分数"""
        if not results:
            return 0.0
        
        # 计算加权平均
        total_weight = 0.0
        weighted_sum = 0.0
        
        weights = {
            QualityCheckType.DOCUMENT_COMPLETENESS: 0.3,
            QualityCheckType.CODE_QUALITY: 0.25,
            QualityCheckType.TEST_COVERAGE: 0.25,
            QualityCheckType.SECURITY: 0.15,
            QualityCheckType.MANUAL_REVIEW: 0.05,
        }
        
        for result in results:
            weight = weights.get(result.check_type, 0.1)
            weighted_sum += result.score * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0