"""Phase 3 深度测试 - 边界情况和潜在问题."""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import agent.roles
from team.builder import TeamBuilder
from team.config import TaskType, ComplexityLevel, TeamConfig
from team.factory import AgentFactory


class TestDeepEdgeCases:
    """深度边界测试"""
    
    @pytest.mark.asyncio
    async def test_empty_descriptions(self):
        """测试空描述"""
        builder = TeamBuilder()
        
        result = await builder.build('')
        assert result.success == False
        assert '任务描述不能为空' in result.error
        
        result = await builder.build('   ')
        assert result.success == False
    
    @pytest.mark.asyncio
    async def test_long_descriptions(self):
        """测试超长描述"""
        builder = TeamBuilder()
        
        long_desc = '开发网站，' * 1000
        result = await builder.build(long_desc)
        assert result.success == True
        assert len(result.team) <= 10
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """测试特殊字符"""
        builder = TeamBuilder()
        
        special_cases = [
            '开发网站!@#$%^&*()',
            '开发\n网站\t包含换行',
            '开发网站<img>xss</img>',
            "开发网站'; DROP TABLE users;--",
            '{"task": "开发网站"}',
        ]
        
        for desc in special_cases:
            result = await builder.build(desc)
            assert result.success == True
    
    @pytest.mark.asyncio
    async def test_all_task_types(self):
        """测试所有任务类型"""
        builder = TeamBuilder()
        
        task_cases = [
            ('开发电商网站', TaskType.WEB_DEVELOPMENT),
            ('开发移动 app 应用', TaskType.MOBILE_DEVELOPMENT),
            ('开发 REST API 接口', TaskType.API_DEVELOPMENT),
            ('数据分析报表', TaskType.DATA_ANALYSIS),
            ('编写技术文档', TaskType.DOCUMENTATION),
            ('部署系统到生产环境', TaskType.DEVOPS),
            ('进行安全审计', TaskType.SECURITY_AUDIT),
            ('做一个早餐', TaskType.OTHER),
        ]
        
        for desc, expected in task_cases:
            result = await builder.build(desc)
            assert result.success == True
            assert result.analysis.task_type == expected
    
    @pytest.mark.asyncio
    async def test_complexity_levels(self):
        """测试复杂度等级"""
        builder = TeamBuilder()
        
        complexity_cases = [
            ('简单 demo', ComplexityLevel.SIMPLE),
            ('标准功能开发', ComplexityLevel.MEDIUM),
            ('复杂企业级系统', ComplexityLevel.COMPLEX),
            ('大型分布式高并发系统', ComplexityLevel.ENTERPRISE),
        ]
        
        for desc, expected in complexity_cases:
            result = await builder.build(desc)
            assert result.success == True
            assert result.analysis.complexity == expected
    
    @pytest.mark.asyncio
    async def test_team_size_limits(self):
        """测试团队规模限制"""
        # 测试最大规模
        config = TeamConfig(max_team_size=15)
        builder = TeamBuilder(config=config)
        
        result = await builder.build('开发大型分布式高并发企业级复杂系统')
        assert result.success == True
        assert len(result.team) <= 15
        
        # 测试小规模限制
        config = TeamConfig(max_team_size=3)
        builder = TeamBuilder(config=config)
        
        result = await builder.build('开发复杂网站')
        assert result.success == True
        assert len(result.team) <= 3
        
        # 测试极小规模
        config = TeamConfig(max_team_size=2)
        builder = TeamBuilder(config=config)
        
        result = await builder.build('开发简单网站')
        assert result.success == True
        assert len(result.team) <= 2
    
    @pytest.mark.asyncio
    async def test_concurrent_building(self):
        """测试并发构建"""
        builder = TeamBuilder()
        
        tasks = [builder.build(f'开发项目{i}') for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r.success)
        assert success_count == 10
        
        # 检查是否有资源竞争问题
        for r in results:
            assert len(r.team) > 0
    
    @pytest.mark.asyncio
    async def test_role_availability(self):
        """测试角色可用性"""
        builder = TeamBuilder()
        
        result = await builder.build('开发大型电商网站，包含移动端、数据分析、安全审计')
        assert result.success == True
        
        # 检查是否有重复角色
        roles = [a.role for a in result.team]
        assert len(roles) == len(set(roles))
    
    @pytest.mark.asyncio
    async def test_tech_requirements(self):
        """测试技术需求推断"""
        builder = TeamBuilder()
        
        test_cases = [
            ('开发网站界面', 'frontend_required', True),
            ('开发 API 服务', 'backend_required', True),
            ('存储用户数据', 'database_required', True),
            ('部署到服务器', 'devops_required', True),
            ('权限安全控制', 'security_required', True),
        ]
        
        for desc, attr, expected in test_cases:
            result = await builder.build(desc)
            assert result.success == True
            actual = getattr(result.analysis, attr, False)
            assert actual == expected
    
    @pytest.mark.asyncio
    async def test_factory_errors(self):
        """测试工厂错误处理"""
        factory = AgentFactory()
        
        # 测试未知角色
        with pytest.raises(ValueError, match="Unknown role"):
            factory.create_agent("Unknown Role")
        
        # 测试空角色名
        with pytest.raises(ValueError, match="Unknown role"):
            factory.create_agent("")
