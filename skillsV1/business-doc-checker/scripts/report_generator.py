#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务文档完整性检查报告生成器
用于生成标准化的检查报告
"""

import sys
from datetime import datetime


def calculate_coverage(total, covered):
    """计算覆盖率"""
    if total == 0:
        return 0
    return round(covered * 100 / total, 1)


def generate_summary(modules, flows, apis, tables):
    """
    生成统计概览表格

    Args:
        modules: (总数, 已覆盖数)
        flows: (总数, 已覆盖数)
        apis: (总数, 已覆盖数)
        tables: (总数, 已覆盖数)
    """
    module_total, module_covered = modules
    flow_total, flow_covered = flows
    api_total, api_covered = apis
    table_total, table_covered = tables

    # 计算各项覆盖率
    module_percent = calculate_coverage(module_total, module_covered)
    flow_percent = calculate_coverage(flow_total, flow_covered)
    api_percent = calculate_coverage(api_total, api_covered)
    table_percent = calculate_coverage(table_total, table_covered)

    # 计算总计
    total = module_total + flow_total + api_total + table_total
    covered = module_covered + flow_covered + api_covered + table_covered
    overall_percent = calculate_coverage(total, covered)

    # 生成Markdown表格
    report = f"""
## 统计概览

| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | {module_total} | {module_covered} | {module_percent}% | {module_total - module_covered} |
| 业务流程 | {flow_total} | {flow_covered} | {flow_percent}% | {flow_total - flow_covered} |
| API接口 | {api_total} | {api_covered} | {api_percent}% | {api_total - api_covered} |
| 数据表 | {table_total} | {table_covered} | {table_percent}% | {table_total - table_covered} |
| **总计** | {total} | {covered} | {overall_percent}% | {total - covered} |
"""
    return report


def generate_item_list(items, covered=True):
    """
    生成项目列表

    Args:
        items: [(名称, 类名, 描述), ...]
        covered: 是否为已覆盖项
    """
    icon = "✅" if covered else "❌"
    lines = []
    for item in items:
        if len(item) == 3:
            name, class_name, desc = item
            lines.append(f"- {icon} {name} ({class_name}) - {desc}")
        elif len(item) == 2:
            name, desc = item
            lines.append(f"- {icon} {name} - {desc}")
        else:
            lines.append(f"- {icon} {item}")
    return "\n".join(lines)


def generate_report(doc_path, project_path,
                    modules, flows, apis, tables,
                    output_file=None):
    """
    生成完整的检查报告

    Args:
        doc_path: 文档路径
        project_path: 项目路径
        modules: (已覆盖列表, 缺失列表)
        flows: (已覆盖列表, 缺失列表)
        apis: (已覆盖列表, 缺失列表)
        tables: (已覆盖列表, 缺失列表)
        output_file: 输出文件路径，如果为None则输出到控制台
    """
    # 提取统计数据
    module_covered_list, module_missing_list = modules
    flow_covered_list, flow_missing_list = flows
    api_covered_list, api_missing_list = apis
    table_covered_list, table_missing_list = tables

    module_total = len(module_covered_list) + len(module_missing_list)
    flow_total = len(flow_covered_list) + len(flow_missing_list)
    api_total = len(api_covered_list) + len(api_missing_list)
    table_total = len(table_covered_list) + len(table_missing_list)

    # 生成报告
    report = f"""# 业务文档完整性检查报告

## 检查概述

- **检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **文档路径**: {doc_path}
- **项目路径**: {project_path}

{generate_summary(
    (module_total, len(module_covered_list)),
    (flow_total, len(flow_covered_list)),
    (api_total, len(api_covered_list)),
    (table_total, len(table_covered_list))
)}

## 详细检查结果

### 1. 模块划分 ✅覆盖率: {calculate_coverage(module_total, len(module_covered_list))}%

#### 已覆盖的模块 ({len(module_covered_list)}/{module_total})
{generate_item_list(module_covered_list, covered=True) if module_covered_list else '无'}

#### 缺失的模块 ({len(module_missing_list)}/{module_total})
{generate_item_list(module_missing_list, covered=False) if module_missing_list else '无'}

---

### 2. 业务流程 ✅覆盖率: {calculate_coverage(flow_total, len(flow_covered_list))}%

#### 已覆盖的流程 ({len(flow_covered_list)}/{flow_total})
{generate_item_list(flow_covered_list, covered=True) if flow_covered_list else '无'}

#### 缺失的流程 ({len(flow_missing_list)}/{flow_total})
{generate_item_list(flow_missing_list, covered=False) if flow_missing_list else '无'}

---

### 3. API接口 ✅覆盖率: {calculate_coverage(api_total, len(api_covered_list))}%

#### 已覆盖的接口 ({len(api_covered_list)}/{api_total})
{generate_item_list(api_covered_list, covered=True) if api_covered_list else '无'}

#### 缺失的接口 ({len(api_missing_list)}/{api_total})
{generate_item_list(api_missing_list, covered=False) if api_missing_list else '无'}

---

### 4. 数据表 ✅覆盖率: {calculate_coverage(table_total, len(table_covered_list))}%

#### 已覆盖的数据表 ({len(table_covered_list)}/{table_total})
{generate_item_list(table_covered_list, covered=True) if table_covered_list else '无'}

#### 缺失的数据表 ({len(table_missing_list)}/{table_total})
{generate_item_list(table_missing_list, covered=False) if table_missing_list else '无'}

---

## 检查说明

- **检查范围**: 本次检查为广度优先检查，关注业务范围的覆盖度，不深入检查实现细节
- **检查方法**: 通过代码扫描识别核心业务元素，与文档内容进行关键词匹配
- **匹配规则**: 使用精确匹配和语义匹配相结合的方式
- **覆盖标准**: 文档中对该元素有实质性描述即视为已覆盖
"""

    # 输出报告
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已生成: {output_file}")
    else:
        print(report)

    return report


def main():
    """命令行使用示例"""
    print("业务文档完整性检查报告生成器")
    print("=" * 50)
    print()
    print("用法:")
    print("  python report_generator.py --help")
    print()
    print("示例:")
    print("  # 交互式生成报告")
    print("  python report_generator.py --interactive")
    print()
    print("  # 使用参数生成报告")
    print("  python report_generator.py --doc README.md --project ./myproject")
    print()

    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("选项:")
        print("  --help, -h              显示帮助信息")
        print("  --interactive           交互式生成报告")
        print("  --doc <path>            指定文档路径")
        print("  --project <path>        指定项目路径")
        print("  --output <path>         指定输出文件路径")


if __name__ == '__main__':
    main()
