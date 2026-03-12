"""Agent Team 使用示例."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.roles import (
    ProductManagerAgent,
    SystemArchitectAgent,
    TechLeadAgent,
    BackendDeveloperAgent,
    QAAgent,
)
from agent.opencode_integration import TeamRunner, OpenCodeIntegration


async def main():
    """运行 Agent 团队示例"""
    
    print("="*70)
    print("Agent Team System - 使用示例")
    print("="*70)
    print()
    
    # 1. 创建 Agent 团队
    agents = [
        ProductManagerAgent(),
        SystemArchitectAgent(),
        TechLeadAgent(),
        BackendDeveloperAgent(),
        QAAgent(),
    ]
    
    print(f"✓ 创建 {len(agents)} 个 Agent")
    for agent in agents:
        print(f"  - {agent.role}: {len(agent.expertise)} 技能")
    print()
    
    # 2. 创建团队运行器
    opencode = OpenCodeIntegration(base_url="http://localhost:4096")
    runner = TeamRunner(agents, opencode)
    
    # 3. 初始化
    await runner.initialize()
    print()
    
    # 4. 运行团队
    await runner.run(max_iterations=10)
    print()
    
    # 5. 关闭
    await runner.close()
    
    print()
    print("="*70)
    print("示例执行完成!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
