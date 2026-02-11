#!/bin/bash
# 业务文档完整性检查辅助脚本
# 用于生成检查报告的统计信息

echo "业务文档完整性检查辅助工具"
echo "================================"

# 用法提示
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "用法: ./check_helper.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --stats <总数量> <已覆盖>    计算覆盖率"
    echo "  --summary                  显示检查概览模板"
    echo "  --help                     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./check_helper.sh --stats 10 8"
    echo "    => 覆盖率: 80%"
    exit 0
fi

# 计算覆盖率
if [ "$1" == "--stats" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "错误: 需要提供总数量和已覆盖数量"
        echo "示例: ./check_helper.sh --stats 10 8"
        exit 1
    fi

    total=$2
    covered=$3

    if [ "$total" -eq 0 ]; then
        echo "错误: 总数量不能为0"
        exit 1
    fi

    percentage=$((covered * 100 / total))

    echo "总数: $total"
    echo "已覆盖: $covered"
    echo "覆盖率: ${percentage}%"
    echo "缺失: $((total - covered))"

    exit 0
fi

# 显示概览模板
if [ "$1" == "--summary" ]; then
    cat <<'EOF'
# 检查概览模板

## 统计概览

| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | ${MODULE_TOTAL} | ${MODULE_COVERED} | ${MODULE_PERCENT}% | ${MODULE_MISSING} |
| 业务流程 | ${FLOW_TOTAL} | ${FLOW_COVERED} | ${FLOW_PERCENT}% | ${FLOW_MISSING} |
| API接口 | ${API_TOTAL} | ${API_COVERED} | ${API_PERCENT}% | ${API_MISSING} |
| 数据表 | ${TABLE_TOTAL} | ${TABLE_COVERED} | ${TABLE_PERCENT}% | ${TABLE_MISSING} |
| **总计** | ${TOTAL} | ${COVERED} | ${OVERALL_PERCENT}% | ${MISSING} |

EOF
    exit 0
fi

echo "错误: 未知的选项"
echo "使用 --help 查看帮助信息"
exit 1
