"""Agent 记忆系统."""

from __future__ import annotations

from typing import Optional, Dict, Any, List


class AgentMemory:
    """
    Agent 记忆系统
    
    管理短期记忆和长期记忆
    """
    
    def __init__(self):
        # 短期记忆 (当前任务)
        self.short_term: Dict[str, Any] = {}
        
        # 长期记忆 (历史经验)
        self.long_term: Dict[str, Any] = {}
        
        # 记忆索引
        self._index: Dict[str, List[str]] = {
            "short": [],
            "long": [],
        }
    
    def add(
        self,
        key: str,
        value: Any,
        scope: str = "short",
    ):
        """添加到记忆"""
        if scope == "short":
            self.short_term[key] = value
            if key not in self._index["short"]:
                self._index["short"].append(key)
        else:
            self.long_term[key] = value
            if key not in self._index["long"]:
                self._index["long"].append(key)
    
    def get(
        self,
        key: str,
        scope: str = "short",
    ) -> Optional[Any]:
        """从记忆获取"""
        if scope == "short":
            return self.short_term.get(key)
        return self.long_term.get(key)
    
    def delete(
        self,
        key: str,
        scope: str = "short",
    ) -> bool:
        """从记忆删除"""
        if scope == "short":
            if key in self.short_term:
                del self.short_term[key]
                if key in self._index["short"]:
                    self._index["short"].remove(key)
                return True
        else:
            if key in self.long_term:
                del self.long_term[key]
                if key in self._index["long"]:
                    self._index["long"].remove(key)
                return True
        return False
    
    def clear(self, scope: Optional[str] = None):
        """清空记忆"""
        if scope is None or scope == "short":
            self.short_term.clear()
            self._index["short"].clear()
        
        if scope is None or scope == "long":
            self.long_term.clear()
            self._index["long"].clear()
    
    def search(self, pattern: str, scope: str = "short") -> List[str]:
        """搜索记忆"""
        import re
        
        results = []
        target = self.short_term if scope == "short" else self.long_term
        
        for key in target.keys():
            if re.search(pattern, key, re.IGNORECASE):
                results.append(key)
        
        return results
    
    def get_all(self, scope: str = "short") -> Dict[str, Any]:
        """获取所有记忆"""
        if scope == "short":
            return self.short_term.copy()
        return self.long_term.copy()
