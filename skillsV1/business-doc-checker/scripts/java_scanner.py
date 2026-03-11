#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java项目扫描器
扫描Java项目并提取核心业务模块、流程、API和数据表信息
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict


class JavaProjectScanner:
    """Java项目扫描器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.source_root = self.project_root / "src" / "main" / "java"
        self.results = {
            'modules': [],
            'flows': [],
            'apis': [],
            'tables': []
        }

    def scan_modules(self) -> List[Dict]:
        """
        扫描核心模块（Service层）
        返回: 模块列表，包含模块名和类路径
        """
        modules = []

        # 模式1: *Service.java
        service_files = list(self.source_root.rglob("*Service.java"))
        for file in service_files:
            # 提取模块名（去掉Service后缀）
            filename = file.stem
            if filename.endswith('Service'):
                module_name = filename[:-7]  # 去掉Service
            else:
                module_name = filename

            # 读取文件内容获取注释
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 尝试提取类注释
                    comment_match = re.search(r'/\*\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/', content)
                    comment = comment_match.group(0) if comment_match else ""
            except Exception:
                comment = ""

            modules.append({
                'name': module_name,
                'class_name': filename,
                'path': str(file.relative_to(self.source_root)),
                'comment': comment
            })

        # 模式2: *Manager.java
        manager_files = list(self.source_root.rglob("*Manager.java"))
        for file in manager_files:
            filename = file.stem
            if filename.endswith('Manager'):
                module_name = filename[:-7]
            else:
                module_name = filename

            modules.append({
                'name': module_name,
                'class_name': filename,
                'path': str(file.relative_to(self.source_root)),
                'comment': ''
            })

        # 去重
        unique_modules = []
        seen = set()
        for m in modules:
            if m['class_name'] not in seen:
                seen.add(m['class_name'])
                unique_modules.append(m)

        return sorted(unique_modules, key=lambda x: x['name'])

    def scan_flows(self) -> List[Dict]:
        """
        扫描业务流程（Service层的公共方法）
        返回: 流程列表
        """
        flows = []

        service_files = list(self.source_root.rglob("*Service.java"))
        flow_keywords = ['create', 'save', 'update', 'delete', 'process', 'handle',
                         'submit', 'approve', 'cancel', 'complete']

        for file in service_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找公共方法
                method_pattern = r'public\s+(?:[\w<>]+\s+)?(\w+)\s*\('
                matches = re.findall(method_pattern, content)

                for method_name in matches:
                    # 过滤掉getter/setter和简单的方法
                    if method_name.startswith('get') or method_name.startswith('set'):
                        continue
                    if method_name.startswith('is') or method_name.startswith('has'):
                        continue
                    if len(method_name) < 4:
                        continue

                    # 检查是否包含流程关键词
                    if any(keyword in method_name.lower() for keyword in flow_keywords):
                        flows.append({
                            'name': method_name,
                            'service': file.stem,
                            'path': str(file.relative_to(self.source_root))
                        })

            except Exception as e:
                print(f"警告: 读取文件 {file} 失败: {e}")

        # 去重
        unique_flows = []
        seen = set()
        for f in flows:
            key = f"{f['service']}.{f['name']}"
            if key not in seen:
                seen.add(key)
                unique_flows.append(f)

        return sorted(unique_flows, key=lambda x: x['name'])

    def scan_apis(self) -> List[Dict]:
        """
        扫描API接口（Controller层）
        返回: API列表，包含HTTP方法、路径和控制器
        """
        apis = []

        controller_files = list(self.source_root.rglob("*Controller.java"))
        for file in controller_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取类级别的@RequestMapping
                class_mapping = None
                class_match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
                if class_match:
                    class_mapping = class_match.group(1)

                # 提取方法级别的映射
                method_pattern = r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*["\']([^"\']+)["\']'
                method_matches = re.findall(method_pattern, content)

                for http_method, path in method_matches:
                    # 组合完整路径
                    if class_mapping:
                        full_path = f"{class_mapping}{path}"
                    else:
                        full_path = path

                    # 标准化路径
                    full_path = full_path.replace("//", "/")

                    apis.append({
                        'http_method': http_method.replace('Mapping', ''),
                        'path': full_path,
                        'controller': file.stem,
                        'path_obj': str(file.relative_to(self.source_root))
                    })

            except Exception as e:
                print(f"警告: 读取文件 {file} 失败: {e}")

        # 去重
        unique_apis = []
        seen = set()
        for api in apis:
            key = f"{api['http_method']}:{api['path']}"
            if key not in seen:
                seen.add(key)
                unique_apis.append(api)

        return sorted(unique_apis, key=lambda x: (x['controller'], x['path']))

    def scan_tables(self) -> List[Dict]:
        """
        扫描数据表（Entity/Model/DO层）
        返回: 数据表列表
        """
        tables = []

        # 扫描常见实体目录
        entity_dirs = ['entity', 'model', 'domain', 'pojo', 'dto', 'do']
        for entity_dir in entity_dirs:
            entity_files = list(self.source_root.rglob(f"**/{entity_dir}/*.java"))
            for file in entity_files:
                table_name = file.stem

                # 读取@Table或@Entity注解
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 查找@Table注解
                    table_match = re.search(r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', content)
                    db_table_name = table_match.group(1) if table_match else table_name

                    # 查找主键字段
                    id_fields = re.findall(r'@Id.*\n.*\s+(\w+)\s+(\w+);', content)

                except Exception:
                    db_table_name = table_name
                    id_fields = []

                tables.append({
                    'name': table_name,
                    'db_name': db_table_name,
                    'path': str(file.relative_to(self.source_root))
                })

        # 去重
        unique_tables = []
        seen = set()
        for t in tables:
            if t['name'] not in seen:
                seen.add(t['name'])
                unique_tables.append(t)

        return sorted(unique_tables, key=lambda x: x['name'])

    def scan_all(self) -> Dict:
        """扫描所有内容"""
        print(f"🔍 开始扫描项目: {self.project_root}")

        if not self.source_root.exists():
            print(f"❌ 源码目录不存在: {self.source_root}")
            return self.results

        print("  扫描模块...")
        self.results['modules'] = self.scan_modules()
        print(f"  ✓ 找到 {len(self.results['modules'])} 个模块")

        print("  扫描业务流程...")
        self.results['flows'] = self.scan_flows()
        print(f"  ✓ 找到 {len(self.results['flows'])} 个业务流程")

        print("  扫描API接口...")
        self.results['apis'] = self.scan_apis()
        print(f"  ✓ 找到 {len(self.results['apis'])} 个API接口")

        print("  扫描数据表...")
        self.results['tables'] = self.scan_tables()
        print(f"  ✓ 找到 {len(self.results['tables'])} 个数据表")

        print(f"✅ 扫描完成!")
        return self.results

    def print_summary(self):
        """打印扫描摘要"""
        print("\n" + "=" * 60)
        print("Java项目扫描结果摘要")
        print("=" * 60)

        print(f"\n模块 ({len(self.results['modules'])}个):")
        for m in self.results['modules'][:10]:  # 只显示前10个
            print(f"  - {m['name']} ({m['class_name']})")

        if len(self.results['modules']) > 10:
            print(f"  ... 还有 {len(self.results['modules']) - 10} 个模块")

        print(f"\n业务流程 ({len(self.results['flows'])}个):")
        for f in self.results['flows'][:10]:
            print(f"  - {f['service']}.{f['name']}()")

        if len(self.results['flows']) > 10:
            print(f"  ... 还有 {len(self.results['flows']) - 10} 个流程")

        print(f"\nAPI接口 ({len(self.results['apis'])}个):")
        for api in self.results['apis'][:10]:
            print(f"  - {api['http_method']} {api['path']} ({api['controller']})")

        if len(self.results['apis']) > 10:
            print(f"  ... 还有 {len(self.results['apis']) - 10} 个接口")

        print(f"\n数据表 ({len(self.results['tables'])}个):")
        for t in self.results['tables'][:10]:
            print(f"  - {t['name']} (DB: {t['db_name']})")

        if len(self.results['tables']) > 10:
            print(f"  ... 还有 {len(self.results['tables']) - 10} 个表")

        print("=" * 60)


def main():
    """命令行使用"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python java_scanner.py <项目路径>")
        print("示例: python java_scanner.py ./my-project")
        sys.exit(1)

    project_path = sys.argv[1]
    scanner = JavaProjectScanner(project_path)
    scanner.scan_all()
    scanner.print_summary()


if __name__ == '__main__':
    main()
