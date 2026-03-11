#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务文档完整性快速检查脚本
自动化检查文档是否覆盖了代码中的业务内容
"""

import sys
import re
from pathlib import Path


class DocCompletenessChecker:
    """文档完整性检查器"""

    def __init__(self, doc_path: str, project_root: str = "."):
        self.doc_path = Path(doc_path)
        self.project_root = Path(project_root)
        self.doc_content = ""
        self.scan_results = {}
        self.check_results = {}

    def load_document(self):
        """加载文档内容"""
        if not self.doc_path.exists():
            print(f"❌ 文档不存在: {self.doc_path}")
            sys.exit(1)

        with open(self.doc_path, 'r', encoding='utf-8') as f:
            self.doc_content = f.read()

        print(f"✅ 已加载文档: {self.doc_path}")

    def contains_keyword(self, keyword: str) -> bool:
        """检查文档是否包含关键词（不区分大小写）"""
        return re.search(re.escape(keyword), self.doc_content, re.IGNORECASE) is not None

    def check_module_coverage(self, modules):
        """
        检查模块覆盖情况

        Args:
            modules: 模块列表 [{'name': 'User', 'class_name': 'UserService'}, ...]

        Returns:
            (covered, missing) - 已覆盖和缺失的模块列表
        """
        covered = []
        missing = []

        for module in modules:
            module_name = module['name']
            class_name = module['class_name']

            # 检查策略：
            # 1. 检查模块名
            # 2. 检查类名
            # 3. 检查小写版本

            found = False

            # 策略1: 检查模块名
            if self.contains_keyword(module_name):
                found = True
            # 策略2: 检查类名
            elif self.contains_keyword(class_name):
                found = True
            # 策略3: 检查中文翻译（如果有）
            elif module_name.lower() in ['user', 'order', 'product', 'payment']:
                # 常见模块的中文关键词
                translations = {
                    'user': ['用户', '用户管理'],
                    'order': ['订单', '订单管理'],
                    'product': ['商品', '产品', '商品管理'],
                    'payment': ['支付', '付款'],
                    'cart': ['购物车', '车'],
                    'inventory': ['库存', '库存管理'],
                    'logistics': ['物流', '配送'],
                    'coupon': ['优惠券'],
                    'address': ['地址']
                }
                for trans in translations.get(module_name.lower(), []):
                    if self.contains_keyword(trans):
                        found = True
                        break

            if found:
                covered.append((module_name, class_name, "文档中有相关描述"))
            else:
                missing.append((module_name, class_name, "文档未提及"))

        return covered, missing

    def check_api_coverage(self, apis):
        """检查API覆盖情况"""
        covered = []
        missing = []

        for api in apis:
            http_method = api['http_method']
            path = api['path']
            controller = api['controller']

            # 检查路径
            found = False

            # 策略1: 检查完整路径
            if self.contains_keyword(path):
                found = True
            # 策略2: 检查控制器名
            elif self.contains_keyword(controller):
                found = True
            # 策略3: 检查路径的关键部分
            elif len(path.split('/')) > 2:
                # 检查路径的最后部分
                last_part = path.split('/')[-1]
                if last_part and last_part != '{id}':
                    if self.contains_keyword(last_part):
                        found = True

            if found:
                covered.append((f"{http_method} {path}", controller, "文档中有接口说明"))
            else:
                missing.append((f"{http_method} {path}", controller, "文档未记录"))

        return covered, missing

    def check_table_coverage(self, tables):
        """检查数据表覆盖情况"""
        covered = []
        missing = []

        for table in tables:
            table_name = table['name']
            db_name = table['db_name']

            found = False

            # 策略1: 检查表名
            if self.contains_keyword(table_name):
                found = True
            # 策略2: 检查DB表名
            elif self.contains_keyword(db_name):
                found = True
            # 策略3: 检查"表"关键字
            elif self.contains_keyword(f"{table_name}表"):
                found = True

            if found:
                covered.append((table_name, db_name, "文档中有表结构说明"))
            else:
                missing.append((table_name, db_name, "文档未提及"))

        return covered, missing

    def generate_report(self, output_file: str = None):
        """生成检查报告"""
        from scripts.report_generator import generate_report

        # 准备数据
        modules_result = self.check_results.get('modules', ([], []))
        flows_result = self.check_results.get('flows', ([], []))
        apis_result = self.check_results.get('apis', ([], []))
        tables_result = self.check_results.get('tables', ([], []))

        # 生成报告
        generate_report(
            doc_path=str(self.doc_path),
            project_path=str(self.project_root),
            modules=modules_result,
            flows=flows_result,
            apis=apis_result,
            tables=tables_result,
            output_file=output_file
        )

        print(f"✅ 检查报告已生成: {output_file}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python quick_check.py <文档路径> [项目路径]")
        print("示例: python quick_check.py docs/业务文档.md ./my-project")
        sys.exit(1)

    doc_path = sys.argv[1]
    project_path = sys.argv[2] if len(sys.argv) > 2 else "."

    print("=" * 60)
    print("📝 业务文档完整性快速检查")
    print("=" * 60)
    print()

    # 创建检查器
    checker = DocCompletenessChecker(doc_path, project_path)
    checker.load_document()

    # 扫描项目
    from scripts.java_scanner import JavaProjectScanner
    print("\n🔍 扫描Java项目...")
    scanner = JavaProjectScanner(project_path)
    scan_results = scanner.scan_all()

    # 检查覆盖情况
    print("\n✅ 开始检查文档覆盖情况...")

    checker.check_results['modules'] = checker.check_module_coverage(scan_results['modules'])
    checker.check_results['apis'] = checker.check_api_coverage(scan_results['apis'])
    checker.check_results['tables'] = checker.check_table_coverage(scan_results['tables'])
    # 流程检查暂时使用简单策略
    checker.check_results['flows'] = ([], [])

    # 生成报告
    output_file = str(Path(doc_path).parent / "文档完整性检查报告.md")
    checker.generate_report(output_file)

    print("\n" + "=" * 60)
    print("✅ 检查完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
