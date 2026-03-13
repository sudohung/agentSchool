"""团队组建示例."""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from team.builder import TeamBuilder
from team.config import TeamConfig


async def main():
    """主函数"""
    print("=" * 60)
    print("Phase 3: 团队组建示例")
    print("=" * 60)
    
    # 示例 1: 简单使用
    print("\n【示例 1】简单团队构建")
    print("-" * 60)
    
    builder = TeamBuilder()
    
    task = "开发一个电商网站，包含商品展示、购物车、支付功能"
    print(f"任务描述：{task}")
    
    result = await builder.build(task)
    
    if result.success:
        print(f"✅ 团队构建成功")
        print(f"📊 任务类型：{result.analysis.task_type.value}")
        print(f"📈 复杂度：{result.analysis.complexity.value}")
        print(f"👥 团队成员 ({len(result.team)}人):")
        for agent in result.team:
            print(f"  - {agent.role}")
        print(f"🔧 技术需求:")
        print(f"  - 前端：{result.analysis.frontend_required}")
        print(f"  - 后端：{result.analysis.backend_required}")
        print(f"  - 数据库：{result.analysis.database_required}")
    else:
        print(f"❌ 构建失败：{result.error}")
    
    # 示例 2: 自定义配置
    print("\n【示例 2】自定义配置")
    print("-" * 60)
    
    config = TeamConfig(
        max_team_size=8,
        enable_ai_analysis=True,
        storage_base_path="./my_storage",
    )
    
    builder2 = TeamBuilder(config=config)
    result2 = await builder2.build("开发简单 API")
    
    if result2.success:
        print(f"团队规模：{len(result2.team)}")
        print(f"角色：{[a.role for a in result2.team]}")
    
    # 示例 3: 不同任务类型
    print("\n【示例 3】不同任务类型")
    print("-" * 60)
    
    tasks = [
        ("开发移动 App", "mobile"),
        ("编写技术文档", "documentation"),
        ("部署系统", "devops"),
        ("安全审计", "security"),
    ]
    
    for task_desc, task_type in tasks:
        result = await builder.build(task_desc)
        if result.success:
            print(f"{task_type:15s}: {len(result.team)}人 - {', '.join([a.role for a in result.team])}")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
