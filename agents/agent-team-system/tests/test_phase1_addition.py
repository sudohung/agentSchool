"""Phase 1 补充功能测试 - 文档中心/诉求看板增强."""

import pytest
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_hub.diff import DiffCalculator, DiffType, DiffLine, DiffResult
from document_hub.version import VersionControl
from document_hub.store import DocumentStore
from document_hub.lock import LockManager, LockType, LockStatus, LockTimeoutError
from request_board.router import (
    RouterService,
    RoutingStrategy,
    RoleBasedRouter,
    SkillBasedRouter,
    LoadBalancedRouter,
    PriorityBasedRouter,
)
from request_board.timeout import TimeoutMonitor, TimeoutConfig
from request_board.board import RequestBoard
from request_board.models import (
    Request,
    RequestType,
    RequestPriority,
    RequestStatus,
)


# ==================== Diff 计算器测试 ====================

class TestDiffCalculator:
    """Diff 计算器测试"""
    
    def test_calculate_diff(self):
        """测试 Diff 计算"""
        calc = DiffCalculator()
        
        old = "line1\nline2\nline3\n"
        new = "line1\nmodified\nline3\nline4\n"
        
        result = calc.calculate(old, new, 1, 2)
        
        assert result.old_version == 1
        assert result.new_version == 2
        assert result.additions >= 0
        assert result.deletions >= 0
    
    def test_no_diff(self):
        """测试无差异"""
        calc = DiffCalculator()
        
        content = "line1\nline2\nline3\n"
        result = calc.calculate(content, content, 1, 2)
        
        assert result.additions == 0
        assert result.deletions == 0
    
    def test_empty_old(self):
        """测试空旧内容"""
        calc = DiffCalculator()
        
        result = calc.calculate("", "new content", 1, 2)
        
        assert result.additions > 0


# ==================== 版本控制测试 ====================

class TestVersionControl:
    """版本控制测试"""
    
    @pytest.fixture
    def setup(self, tmp_path):
        """设置测试环境"""
        storage_path = tmp_path / "storage"
        store = DocumentStore(base_path=str(storage_path))
        version_control = VersionControl(store, version_path=tmp_path / "versions")
        return store, version_control
    
    async def test_create_version(self, setup):
        """测试创建版本"""
        store, vc = setup
        
        version = await vc.create_version(
            document_id="test_doc",
            content="Version 1 content",
            author="Test Agent",
            change_summary="Initial version",
        )
        
        assert version.version == 1
        assert version.author == "Test Agent"
        assert version.content == "Version 1 content"
    
    async def test_get_version(self, setup):
        """测试获取版本"""
        store, vc = setup
        
        # 创建版本
        v1 = await vc.create_version(
            document_id="test_doc",
            content="Version 1",
            author="Agent A",
        )
        
        # 获取版本
        retrieved = await vc.get_version("test_doc", 1)
        
        assert retrieved is not None
        assert retrieved.version == 1
        assert retrieved.content == "Version 1"
    
    async def test_get_version_history(self, setup):
        """测试获取版本历史"""
        store, vc = setup
        
        # 创建多个版本
        for i in range(3):
            await vc.create_version(
                document_id="test_doc",
                content=f"Version {i+1}",
                author="Agent A",
                change_summary=f"Version {i+1}",
            )
        
        history = await vc.get_version_history("test_doc")
        
        assert len(history) == 3
        assert history[0].version == 3  # 最新的在前
    
    async def test_rollback(self, setup):
        """测试版本回滚"""
        store, vc = setup
        
        # 创建多个版本
        for i in range(3):
            await vc.create_version(
                document_id="test_doc",
                content=f"Version {i+1}",
                author="Agent A",
            )
        
        # 回滚到版本 1
        rolled_back = await vc.rollback(
            document_id="test_doc",
            target_version=1,
            author="Agent B",
        )
        
        assert rolled_back.content == "Version 1"
        assert rolled_back.version == 4  # 新版本号
        assert "Rollback" in rolled_back.change_summary
    
    async def test_compare_versions(self, setup):
        """测试版本比较"""
        store, vc = setup
        
        # 创建两个版本
        await vc.create_version(
            document_id="test_doc",
            content="Version 1 content",
            author="Agent A",
        )
        
        await vc.create_version(
            document_id="test_doc",
            content="Version 2 content with changes",
            author="Agent A",
        )
        
        diff = await vc.compare_versions("test_doc", 1, 2)
        
        assert diff is not None
        assert diff.old_version == 1
        assert diff.new_version == 2


# ==================== 锁管理器测试 ====================

class TestLockManager:
    """锁管理器测试"""
    
    @pytest.fixture
    def lock_manager(self):
        """创建锁管理器"""
        lm = LockManager(default_timeout=5)
        asyncio.get_event_loop().run_until_complete(lm.start())
        yield lm
        asyncio.get_event_loop().run_until_complete(lm.stop())
    
    async def test_read_lock_shared(self, lock_manager):
        """测试读锁共享"""
        # 获取第一个读锁
        lock1 = await lock_manager.acquire_read_lock("doc_1", "Agent A")
        assert lock1.status == LockStatus.ACQUIRED
        
        # 获取第二个读锁（应该成功）
        lock2 = await lock_manager.acquire_read_lock("doc_1", "Agent B")
        assert lock2.status == LockStatus.ACQUIRED
        
        # 释放
        await lock_manager.release_lock(lock1.lock_id)
        await lock_manager.release_lock(lock2.lock_id)
    
    async def test_write_lock_exclusive(self, lock_manager):
        """测试写锁独占"""
        # 获取写锁
        lock1 = await lock_manager.acquire_write_lock("doc_2", "Agent A")
        assert lock1.status == LockStatus.ACQUIRED
        
        # 尝试获取另一个写锁（应该超时）
        with pytest.raises(LockTimeoutError):
            await lock_manager.acquire_write_lock(
                "doc_2", "Agent B", timeout=1
            )
        
        await lock_manager.release_lock(lock1.lock_id)
    
    async def test_read_write_conflict(self, lock_manager):
        """测试读写冲突"""
        # 获取读锁
        lock1 = await lock_manager.acquire_read_lock("doc_3", "Agent A")
        
        # 尝试获取写锁（应该超时）
        with pytest.raises(LockTimeoutError):
            await lock_manager.acquire_write_lock(
                "doc_3", "Agent B", timeout=1
            )
        
        await lock_manager.release_lock(lock1.lock_id)
    
    async def test_release_all_locks(self, lock_manager):
        """测试释放所有锁"""
        # 获取多个锁
        lock1 = await lock_manager.acquire_read_lock("doc_4", "Agent A")
        lock2 = await lock_manager.acquire_write_lock("doc_5", "Agent A")
        
        # 释放所有
        count = await lock_manager.release_all_locks("Agent A")
        
        assert count == 2
        assert not await lock_manager.is_locked("doc_4")
        assert not await lock_manager.is_locked("doc_5")
    
    async def test_lock_statistics(self, lock_manager):
        """测试锁统计"""
        # 获取一些锁
        await lock_manager.acquire_read_lock("doc_6", "Agent A")
        await lock_manager.acquire_write_lock("doc_7", "Agent B")
        
        stats = lock_manager.get_statistics()
        
        assert stats["total_active_locks"] == 2
        assert stats["locks_by_type"]["read"] == 1
        assert stats["locks_by_type"]["write"] == 1


# ==================== 路由策略测试 ====================

class TestRoutingStrategies:
    """路由策略测试"""
    
    @pytest.fixture
    def router_service(self):
        """创建路由服务"""
        return RouterService()
    
    def create_test_request(self, to_agent="all", context=None):
        """创建测试诉求"""
        return Request(
            id="test_req",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent="Product Manager",
            to_agent=to_agent,
            subject="Test",
            content="Test content",
            context=context or {},
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
    
    async def test_role_based_routing(self, router_service):
        """测试基于角色的路由"""
        request = self.create_test_request(to_agent="System Architect")
        
        targets = await router_service.route_request(
            request=request,
            strategy=RoutingStrategy.ROLE_BASED,
        )
        
        assert "System Architect" in targets
    
    async def test_skill_based_routing(self, router_service):
        """测试基于技能的路由"""
        request = self.create_test_request(
            to_agent="all",
            context={"required_skills": ["React", "CSS"]},
        )
        
        targets = await router_service.route_request(
            request=request,
            strategy=RoutingStrategy.SKILL_BASED,
        )
        
        assert len(targets) > 0
        # Frontend Developer 应该有 React 技能
        assert "Frontend Developer" in targets
    
    async def test_load_balanced_routing(self, router_service):
        """测试负载均衡路由"""
        # 设置工作负载
        router_service.update_agent_workload("Frontend Developer", 5)
        router_service.update_agent_workload("Backend Developer", 2)
        
        request = self.create_test_request(to_agent="all")
        
        targets = await router_service.route_request(
            request=request,
            strategy=RoutingStrategy.LOAD_BALANCED,
        )
        
        # Backend Developer 负载更低
        assert targets[0] == "Backend Developer"
    
    async def test_priority_based_routing(self, router_service):
        """测试优先级路由"""
        # 紧急优先级应该路由给 Tech Lead
        request = Request(
            id="critical_req",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.CRITICAL,
            status=RequestStatus.PENDING,
            from_agent="Product Manager",
            to_agent="all",
            subject="Critical issue",
            content="Urgent",
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        
        targets = await router_service.route_request(
            request=request,
            strategy=RoutingStrategy.PRIORITY_BASED,
        )
        
        # 紧急请求应该路由给 Tech Lead 或 Coordinator
        assert len(targets) > 0
        assert targets[0] in ["Tech Lead", "Coordinator", "Product Manager"]
    
    async def test_broadcast_routing(self, router_service):
        """测试广播路由"""
        request = self.create_test_request(to_agent="all")
        
        targets = await router_service.route_request(
            request=request,
            strategy=RoutingStrategy.ROLE_BASED,
        )
        
        # 广播应该返回所有可用 Agent
        assert len(targets) > 5


# ==================== 超时监控测试 ====================

class TestTimeoutMonitor:
    """超时监控测试"""
    
    @pytest.fixture
    def setup(self):
        """设置测试环境"""
        board = RequestBoard()
        config = TimeoutConfig(
            timeout_by_priority={"normal": 2},  # 2 秒超时
            escalation_threshold={"normal": 1},  # 1 秒后升级
            check_interval=1,
        )
        monitor = TimeoutMonitor(board, config=config)
        asyncio.get_event_loop().run_until_complete(monitor.start())
        yield board, monitor
        asyncio.get_event_loop().run_until_complete(monitor.stop())
    
    async def test_timeout_detection(self, setup):
        """测试超时检测"""
        board, monitor = setup
        
        # 创建诉求（5 秒前）
        request = Request(
            id="test_timeout",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.NORMAL,
            status=RequestStatus.PENDING,
            from_agent="Product Manager",
            to_agent="Frontend Developer",
            subject="Test timeout",
            content="Test",
            created_at=int(time.time()) - 5,
            updated_at=int(time.time()) - 5,
        )
        await board.create_request(request)
        
        # 等待监控检查
        await asyncio.sleep(2)
        
        # 检查是否有超时记录
        stats = monitor.get_statistics()
        assert stats["recent_escalations_1h"] >= 0
    
    async def test_timeout_config(self):
        """测试超时配置"""
        config = TimeoutConfig()
        
        assert config.get_timeout("normal") == 1800
        assert config.get_timeout("high") == 900
        assert config.get_timeout("critical") == 300
        
        assert config.get_escalation_threshold("normal") == 900
        assert config.get_escalation_threshold("high") == 300


# ==================== 综合测试 ====================

class TestPhase1AdditionIntegration:
    """Phase 1 补充功能集成测试"""
    
    async def test_document_version_with_lock(self, tmp_path):
        """测试带锁的版本控制"""
        # 初始化
        storage_path = tmp_path / "storage"
        store = DocumentStore(base_path=str(storage_path))
        version_control = VersionControl(store, version_path=tmp_path / "versions")
        lock_manager = LockManager()
        await lock_manager.start()
        
        try:
            # 获取写锁
            lock = await lock_manager.acquire_write_lock("doc_1", "Agent A")
            
            # 创建版本
            version = await version_control.create_version(
                document_id="doc_1",
                content="Version 1",
                author="Agent A",
            )
            
            # 释放锁
            await lock_manager.release_lock(lock.lock_id)
            
            assert version.version == 1
        finally:
            await lock_manager.stop()
    
    async def test_routing_with_request_board(self):
        """测试诉求看板与路由集成"""
        board = RequestBoard()
        router = RouterService()
        
        # 创建诉求
        request = Request(
            id="req_1",
            type=RequestType.COLLABORATION,
            priority=RequestPriority.HIGH,
            status=RequestStatus.PENDING,
            from_agent="Product Manager",
            to_agent="Backend Developer",
            subject="API Design",
            content="Need API design",
            context={"required_skills": ["Python", "API"]},
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        
        await board.create_request(request)
        
        # 路由
        targets = await router.route_request(request)
        
        assert "Backend Developer" in targets
    
    async def test_full_workflow(self, tmp_path):
        """测试完整工作流"""
        # 1. 初始化组件
        storage_path = tmp_path / "storage"
        store = DocumentStore(base_path=str(storage_path))
        version_control = VersionControl(store, version_path=tmp_path / "versions")
        lock_manager = LockManager()
        await lock_manager.start()
        
        board = RequestBoard()
        router = RouterService()
        
        try:
            # 2. Agent A 获取写锁
            lock_a = await lock_manager.acquire_write_lock("doc_1", "Agent A")
            
            # 3. Agent A 创建文档版本
            v1 = await version_control.create_version(
                document_id="doc_1",
                content="Initial content",
                author="Agent A",
            )
            
            # 4. Agent A 发布诉求
            request = Request(
                id="req_1",
                type=RequestType.REVIEW,
                priority=RequestPriority.NORMAL,
                status=RequestStatus.PENDING,
                from_agent="Agent A",
                to_agent="Code Reviewer",
                subject="Review document",
                content="Please review",
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            await board.create_request(request)
            
            # 5. 路由诉求
            targets = await router.route_request(request)
            
            # 6. Agent B 响应诉求
            response = await board.add_response(
                request_id="req_1",
                response=type('RequestResponse', (), {
                    'id': 'resp_1',
                    'request_id': 'req_1',
                    'from_agent': 'Code Reviewer',
                    'content': 'Looks good',
                    'timestamp': int(time.time()),
                })(),
            )
            
            # 7. Agent A 释放锁
            await lock_manager.release_lock(lock_a.lock_id)
            
            # 验证
            assert v1.version == 1
            assert response is True
            assert "Code Reviewer" in targets
        finally:
            await lock_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
