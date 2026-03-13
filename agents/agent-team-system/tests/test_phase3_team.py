"""Phase 3 团队组建模块测试."""

import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 先导入 agent.roles 以注册所有角色
import agent.roles

from team.config import (
    TaskType,
    ComplexityLevel,
    TaskAnalysis,
    TeamConfig,
    TeamContext,
)
from team.analyzer import TaskAnalyzer
from team.mapper import RoleMapper
from team.factory import AgentFactory
from team.builder import TeamBuilder, BuildResult


# ============================================================================
# Test TaskAnalyzer
# ============================================================================

class TestTaskAnalyzer:
    """测试任务分析器"""
    
    @pytest.mark.asyncio
    async def test_web_development_analysis(self):
        """测试 Web 开发任务分析"""
        analyzer = TaskAnalyzer()
        
        analysis = await analyzer.analyze("开发一个电商网站")
        
        assert analysis.task_type == TaskType.WEB_DEVELOPMENT
        assert analysis.frontend_required == True
        assert analysis.backend_required == True
    
    @pytest.mark.asyncio
    async def test_complexity_analysis(self):
        """测试复杂度分析"""
        analyzer = TaskAnalyzer()
        
        simple = await analyzer.analyze("简单 demo")
        complex_ = await analyzer.analyze("复杂企业级系统")
        
        assert simple.complexity == ComplexityLevel.SIMPLE
        assert complex_.complexity == ComplexityLevel.COMPLEX
    
    @pytest.mark.asyncio
    async def test_empty_description(self):
        """测试空描述"""
        analyzer = TaskAnalyzer()
        
        with pytest.raises(ValueError, match="任务描述不能为空"):
            await analyzer.analyze("")
    
    @pytest.mark.asyncio
    async def test_feature_extraction(self):
        """测试功能提取"""
        analyzer = TaskAnalyzer()
        
        analysis = await analyzer.analyze("开发网站，包含登录，注册，支付")
        
        assert len(analysis.features) > 0
        assert "登录" in analysis.features or "注册" in analysis.features


# ============================================================================
# Test RoleMapper
# ============================================================================

class TestRoleMapper:
    """测试角色映射器"""
    
    def test_web_development_mapping(self):
        """测试 Web 开发角色映射"""
        mapper = RoleMapper()
        
        analysis = TaskAnalysis(
            raw_description="test",
            task_type=TaskType.WEB_DEVELOPMENT,
            complexity=ComplexityLevel.MEDIUM,
            frontend_required=True,
            backend_required=True,
        )
        
        roles = mapper.map(analysis)
        
        assert "Product Manager" in roles
        assert "Tech Lead" in roles
        assert "Frontend Developer" in roles
        assert "Backend Developer" in roles
        assert "QA Engineer" in roles
    
    def test_complex_project_adds_architect(self):
        """测试复杂项目自动添加架构师"""
        mapper = RoleMapper()
        
        analysis = TaskAnalysis(
            raw_description="test",
            task_type=TaskType.WEB_DEVELOPMENT,
            complexity=ComplexityLevel.COMPLEX,
            frontend_required=True,
            backend_required=True,
        )
        
        roles = mapper.map(analysis)
        
        assert "System Architect" in roles
    
    def test_team_size_limit(self):
        """测试团队规模限制"""
        mapper = RoleMapper()
        
        analysis = TaskAnalysis(
            raw_description="test",
            task_type=TaskType.WEB_DEVELOPMENT,
            complexity=ComplexityLevel.ENTERPRISE,
            frontend_required=True,
            backend_required=True,
            devops_required=True,
            security_required=True,
        )
        
        roles = mapper.map(analysis)
        
        assert len(roles) <= RoleMapper.MAX_TEAM_SIZE
    
    def test_mobile_development(self):
        """测试移动开发映射"""
        mapper = RoleMapper()
        
        analysis = TaskAnalysis(
            raw_description="test",
            task_type=TaskType.MOBILE_DEVELOPMENT,
            complexity=ComplexityLevel.SIMPLE,
        )
        
        roles = mapper.map(analysis)
        
        assert "Full Stack Developer" in roles


# ============================================================================
# Test AgentFactory
# ============================================================================

class TestAgentFactory:
    """测试 Agent 工厂"""
    
    def test_create_single_agent(self):
        """测试创建单个 Agent"""
        factory = AgentFactory()
        
        agent = factory.create_agent("Product Manager")
        
        assert agent is not None
        assert agent.role == "Product Manager"
    
    def test_create_multiple_agents(self):
        """测试创建多个 Agent"""
        factory = AgentFactory()
        
        agents = factory.create_agents(["Product Manager", "Tech Lead"])
        
        assert len(agents) == 2
        assert all(a.role in ["Product Manager", "Tech Lead"] for a in agents)
    
    def test_create_unknown_role(self):
        """测试创建未知角色"""
        factory = AgentFactory()
        
        with pytest.raises(ValueError, match="Unknown role"):
            factory.create_agent("Unknown Role")


# ============================================================================
# Test TeamBuilder
# ============================================================================

class TestTeamBuilder:
    """测试团队构建器"""
    
    @pytest.mark.asyncio
    async def test_build_team(self):
        """测试团队构建"""
        builder = TeamBuilder()
        
        result = await builder.build("开发简单网站")
        
        assert result.success == True
        assert len(result.team) >= 2  # 至少 PM + Tech Lead
        assert result.analysis is not None
    
    @pytest.mark.asyncio
    async def test_build_with_config(self):
        """测试带配置的团队构建"""
        config = TeamConfig(max_team_size=5)
        builder = TeamBuilder(config=config)
        
        result = await builder.build("开发电商网站")
        
        assert result.success == True
        assert len(result.team) <= 5
    
    @pytest.mark.asyncio
    async def test_build_empty_description(self):
        """测试空描述"""
        builder = TeamBuilder()
        
        result = await builder.build("")
        
        assert result.success == False
        assert "错误" in result.error


# ============================================================================
# Test Integration
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        builder = TeamBuilder()
        
        # 1. 构建团队
        result = await builder.build("开发电商网站")
        assert result.success
        
        # 2. 验证团队组成
        roles = [a.role for a in result.team]
        assert "Product Manager" in roles
        assert "Frontend Developer" in roles
        
        # 3. 验证依赖注入
        for agent in result.team:
            assert agent.document_hub is not None
            assert agent.request_board is not None


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
