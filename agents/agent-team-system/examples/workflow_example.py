"""工作流引擎使用示例."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from workflow.engine import WorkflowEngine
from workflow.config import WorkflowConfig


async def main():
    """主函数 - 演示工作流引擎使用"""
    print("=" * 60)
    print("Phase 4: 工作流引擎示例")
    print("=" * 60)
    
    # 1. 创建工作流配置
    config = WorkflowConfig(
        quality_passing_score=0.7,
        require_manual_review=False,
    )
    
    # 2. 创建工作流引擎
    engine = WorkflowEngine(config=config)
    
    print(f"\n工作流引擎已创建")
    print(f"质量通过分数：{config.quality_passing_score}")
    print(f"需要人工审核：{config.require_manual_review}")
    
    # 3. 准备团队和依赖 (这里使用模拟对象)
    class MockDocumentStore:
        async def list_documents(self, **kwargs):
            return []
        async def save(self, doc):
            pass
    
    class MockRequestBoard:
        async def get_all_requests(self):
            return []
        async def create_request(self, req):
            pass
    
    # 4. 启动工作流 (需要实际的 Agent 团队)
    print("\n注意：完整工作流需要实际的 Agent 团队")
    print("这里仅演示引擎创建和配置")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
