#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务文档完整性检查报告使用示例
展示如何使用report_generator生成检查报告
"""

from scripts.report_generator import generate_report


def example_usage():
    """示例：生成完整的检查报告"""

    # 文档和项目信息
    doc_path = "docs/业务文档.md"
    project_path = "./my-project"

    # 模块划分检查结果
    module_covered = [
        ("用户管理模块", "UserService", "文档第3章有详细的功能说明"),
        ("订单管理模块", "OrderService", "文档第4章有模块职责描述"),
        ("支付模块", "PaymentService", "文档第5章有支付流程说明"),
        ("商品模块", "ProductService", "文档第2章有商品管理介绍"),
    ]
    module_missing = [
        ("库存管理模块", "InventoryService", "文档未提及"),
        ("物流模块", "LogisticsService", "文档未提及"),
    ]

    # 业务流程检查结果
    flow_covered = [
        ("用户注册流程", "文档第3.2节有流程图和步骤说明"),
        ("订单创建流程", "文档第4.3节有完整流程描述"),
        ("订单支付流程", "文档第5.2节有支付流程说明"),
    ]
    flow_missing = [
        ("库存扣减流程", "文档未描述"),
        ("订单取消流程", "文档未描述"),
    ]

    # API接口检查结果
    api_covered = [
        ("GET /api/users/{id}", "UserController", "文档第8.1节有接口说明"),
        ("POST /api/users", "UserController", "文档第8.2节有接口说明"),
        ("GET /api/orders", "OrderController", "文档第9.1节有接口说明"),
        ("POST /api/orders", "OrderController", "文档第9.2节有接口说明"),
        ("GET /api/orders/{id}", "OrderController", "文档第9.3节有接口说明"),
    ]
    api_missing = [
        ("PUT /api/orders/{id}", "OrderController", "文档未记录"),
        ("DELETE /api/orders/{id}", "OrderController", "文档未记录"),
    ]

    # 数据表检查结果
    table_covered = [
        ("user", "文档第13.1节有表结构说明和字段含义"),
        ("order", "文档第13.2节有表结构说明和字段含义"),
        ("product", "文档第13.3节有表结构说明和字段含义"),
    ]
    table_missing = [
        ("inventory", "文档未提及"),
        ("order_log", "文档未提及"),
    ]

    # 生成报告
    generate_report(
        doc_path=doc_path,
        project_path=project_path,
        modules=(module_covered, module_missing),
        flows=(flow_covered, flow_missing),
        apis=(api_covered, api_missing),
        tables=(table_covered, table_missing),
        output_file="docs/文档完整性检查报告.md"
    )


if __name__ == '__main__':
    example_usage()
    print("\n✅ 示例报告已生成到 docs/文档完整性检查报告.md")
