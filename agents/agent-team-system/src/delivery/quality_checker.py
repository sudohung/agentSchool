"""质量检查器 - 交付前质量把关."""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .models import (
    QualityCheckResult,
    QualityLevel,
    DeliveryPackage,
)


@dataclass
class CheckConfig:
    """检查配置"""
    name: str
    weight: float
    required: bool = False
    threshold: float = 0.0


class QualityChecker:
    """
    质量检查器
    
    功能：
    - 文档完整性检查
    - 内容质量检查
    - 结构规范检查
    - 评分计算
    """
    
    DEFAULT_CHECKS = [
        CheckConfig(name="document_completeness", weight=0.2, required=True),
        CheckConfig(name="content_quality", weight=0.3),
        CheckConfig(name="structure_compliance", weight=0.2),
        CheckConfig(name="metadata_completeness", weight=0.15),
        CheckConfig(name="format_consistency", weight=0.15),
    ]
    
    def __init__(self, checks: Optional[List[CheckConfig]] = None):
        self.checks = checks or self.DEFAULT_CHECKS
        self._check_functions = {
            "document_completeness": self._check_document_completeness,
            "content_quality": self._check_content_quality,
            "structure_compliance": self._check_structure_compliance,
            "metadata_completeness": self._check_metadata_completeness,
            "format_consistency": self._check_format_consistency,
        }
    
    async def check(self, package: DeliveryPackage) -> List[QualityCheckResult]:
        """执行质量检查"""
        results = []
        
        for check_config in self.checks:
            check_func = self._check_functions.get(check_config.name)
            
            if not check_func:
                continue
            
            try:
                result = await check_func(package, check_config)
                results.append(result)
            except Exception as e:
                results.append(QualityCheckResult(
                    check_name=check_config.name,
                    passed=False,
                    score=0.0,
                    message=f"Check failed: {str(e)}",
                ))
        
        return results
    
    async def _check_document_completeness(
        self,
        package: DeliveryPackage,
        config: CheckConfig,
    ) -> QualityCheckResult:
        """检查文档完整性"""
        required_docs = ["PRD", "设计", "代码"]
        
        found = {}
        missing = []
        
        for req_doc in required_docs:
            found_any = False
            for artifact in package.artifacts:
                if req_doc.lower() in artifact.name.lower():
                    found[req_doc] = artifact.name
                    found_any = True
                    break
            
            if not found_any:
                missing.append(req_doc)
        
        score = len(found) / len(required_docs) if required_docs else 1.0
        passed = len(missing) == 0
        
        return QualityCheckResult(
            check_name="document_completeness",
            passed=passed,
            score=score,
            message=f"Found {len(found)}/{len(required_docs)} required documents",
            details={
                "found": found,
                "missing": missing,
            },
        )
    
    async def _check_content_quality(
        self,
        package: DeliveryPackage,
        config: CheckConfig,
    ) -> QualityCheckResult:
        """检查内容质量"""
        if not package.artifacts:
            return QualityCheckResult(
                check_name="content_quality",
                passed=False,
                score=0.0,
                message="No artifacts to check",
            )
        
        total_score = 0.0
        
        for artifact in package.artifacts:
            artifact_score = 0.0
            content = artifact.content or ""
            
            if len(content) >= 100:
                artifact_score += 0.2
            if len(content) >= 500:
                artifact_score += 0.2
            
            if artifact.type == "document":
                if re.search(r'^#\s+', content, re.MULTILINE):
                    artifact_score += 0.2
                if re.search(r'^##\s+', content, re.MULTILINE):
                    artifact_score += 0.2
                if re.search(r'```', content):
                    artifact_score += 0.1
            
            elif artifact.type == "code":
                if len(content) >= 50:
                    artifact_score += 0.3
                if re.search(r'def\s+\w+|function\s+\w+|class\s+\w+', content):
                    artifact_score += 0.4
            
            total_score += min(artifact_score, 1.0)
        
        avg_score = total_score / len(package.artifacts)
        
        return QualityCheckResult(
            check_name="content_quality",
            passed=avg_score >= config.threshold,
            score=avg_score,
            message=f"Average content quality: {avg_score:.1%}",
        )
    
    async def _check_structure_compliance(
        self,
        package: DeliveryPackage,
        config: CheckConfig,
    ) -> QualityCheckResult:
        """检查结构规范性"""
        expected_dirs = {"docs", "src", "tests"}
        
        found_dirs = set()
        for artifact in package.artifacts:
            parts = artifact.path.split("/")
            if len(parts) > 1:
                found_dirs.add(parts[0])
        
        overlap = expected_dirs & found_dirs
        score = len(overlap) / len(expected_dirs) if expected_dirs else 0.0
        
        return QualityCheckResult(
            check_name="structure_compliance",
            passed=score >= 0.5,
            score=score,
            message=f"Found {len(overlap)}/{len(expected_dirs)} expected directories",
            details={
                "expected": list(expected_dirs),
                "found": list(found_dirs),
            },
        )
    
    async def _check_metadata_completeness(
        self,
        package: DeliveryPackage,
        config: CheckConfig,
    ) -> QualityCheckResult:
        """检查元数据完整性"""
        required_fields = ["author", "version"]
        
        complete_count = 0
        
        for artifact in package.artifacts:
            metadata = artifact.metadata
            has_all = all(field in metadata for field in required_fields)
            if has_all:
                complete_count += 1
        
        score = complete_count / len(package.artifacts) if package.artifacts else 0.0
        
        return QualityCheckResult(
            check_name="metadata_completeness",
            passed=score >= 0.8,
            score=score,
            message=f"{complete_count}/{len(package.artifacts)} artifacts have complete metadata",
        )
    
    async def _check_format_consistency(
        self,
        package: DeliveryPackage,
        config: CheckConfig,
    ) -> QualityCheckResult:
        """检查格式一致性"""
        extensions = {}
        
        for artifact in package.artifacts:
            ext = artifact.path.split(".")[-1] if "." in artifact.path else "no_ext"
            if artifact.type not in extensions:
                extensions[artifact.type] = {}
            extensions[artifact.type][ext] = extensions[artifact.type].get(ext, 0) + 1
        
        consistent_types = 0
        total_types = len(extensions)
        
        for artifact_type, exts in extensions.items():
            if len(exts) == 1:
                consistent_types += 1
        
        score = consistent_types / total_types if total_types else 0.0
        
        return QualityCheckResult(
            check_name="format_consistency",
            passed=score >= 0.7,
            score=score,
            message=f"{consistent_types}/{total_types} artifact types have consistent formats",
            details=extensions,
        )
    
    def calculate_overall_score(
        self,
        results: List[QualityCheckResult],
    ) -> tuple[float, QualityLevel]:
        """计算总体评分"""
        if not results:
            return 0.0, QualityLevel.POOR
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for check_config in self.checks:
            result = next(
                (r for r in results if r.check_name == check_config.name),
                None
            )
            
            if result:
                weighted_score += result.score * check_config.weight
                total_weight += check_config.weight
        
        score = weighted_score / total_weight if total_weight else 0.0
        
        if score >= 0.9:
            level = QualityLevel.EXCELLENT
        elif score >= 0.75:
            level = QualityLevel.GOOD
        elif score >= 0.6:
            level = QualityLevel.ACCEPTABLE
        else:
            level = QualityLevel.POOR
        
        return score, level
