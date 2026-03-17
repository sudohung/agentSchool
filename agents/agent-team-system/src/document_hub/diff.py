"""Diff 计算器 - 计算文档版本间差异."""

from __future__ import annotations

import difflib
import re
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class DiffType(Enum):
    """Diff 类型"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffLine:
    """Diff 行"""
    type: DiffType
    content: str
    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None


@dataclass
class DiffResult:
    """Diff 结果"""
    old_version: int
    new_version: int
    additions: int
    deletions: int
    modifications: int
    lines: List[DiffLine]
    summary: str = ""


class DiffCalculator:
    """
    Diff 计算器
    
    使用 Myers diff 算法计算两个文本之间的差异
    """
    
    def calculate(
        self,
        old_content: str,
        new_content: str,
        old_version: int = 0,
        new_version: int = 0,
    ) -> DiffResult:
        """
        计算两个内容之间的 Diff
        
        Args:
            old_content: 旧内容
            new_content: 新内容
            old_version: 旧版本号
            new_version: 新版本号
            
        Returns:
            DiffResult: Diff 结果
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='old',
            tofile='new',
            lineterm=''
        )
        
        lines = self._parse_diff(list(diff))
        
        additions = sum(1 for l in lines if l.type == DiffType.ADDED)
        deletions = sum(1 for l in lines if l.type == DiffType.REMOVED)
        modifications = sum(1 for l in lines if l.type == DiffType.MODIFIED)
        
        return DiffResult(
            old_version=old_version,
            new_version=new_version,
            additions=additions,
            deletions=deletions,
            modifications=modifications,
            lines=lines,
            summary=f"+{additions} -{deletions} ~{modifications}"
        )
    
    def _parse_diff(self, diff_lines: List[str]) -> List[DiffLine]:
        """解析 diff 输出"""
        result = []
        old_line_no = 0
        new_line_no = 0
        
        for line in diff_lines:
            if line.startswith('@@'):
                match = re.search(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if match:
                    old_line_no = int(match.group(1))
                    new_line_no = int(match.group(2))
                continue
            
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            if line.startswith('-'):
                result.append(DiffLine(
                    type=DiffType.REMOVED,
                    old_line_no=old_line_no,
                    content=line[1:]
                ))
                old_line_no += 1
            elif line.startswith('+'):
                result.append(DiffLine(
                    type=DiffType.ADDED,
                    new_line_no=new_line_no,
                    content=line[1:]
                ))
                new_line_no += 1
            elif line.startswith(' '):
                result.append(DiffLine(
                    type=DiffType.UNCHANGED,
                    old_line_no=old_line_no,
                    new_line_no=new_line_no,
                    content=line[1:]
                ))
                old_line_no += 1
                new_line_no += 1
        
        return result
    
    def apply_diff(self, content: str, diff: DiffResult) -> str:
        """
        应用 Diff 到内容
        
        用于版本回滚场景
        """
        lines = content.splitlines(keepends=True)
        result = []
        
        for diff_line in diff.lines:
            if diff_line.type == DiffType.UNCHANGED:
                if diff_line.old_line_no and diff_line.old_line_no <= len(lines):
                    result.append(lines[diff_line.old_line_no - 1])
            elif diff_line.type == DiffType.ADDED:
                result.append(diff_line.content + '\n')
        
        return ''.join(result)
