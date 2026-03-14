"""交付打包器 - 打包交付物."""

from __future__ import annotations

import asyncio
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time

from .integrator import DeliveryPackage


@dataclass
class DeliveryArtifact:
    """交付产物"""
    
    # 交付包
    package: DeliveryPackage
    
    # 交付方式
    delivery_method: str = "local"
    
    # 本地路径
    local_path: Optional[str] = None
    
    # ZIP 路径
    zip_path: Optional[str] = None
    
    # Git 信息
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    
    # S3 信息
    s3_key: Optional[str] = None
    s3_url: Optional[str] = None
    
    # 元数据
    created_at: int = field(default_factory=lambda: int(time.time()))
    size_bytes: int = 0
    
    @property
    def size_mb(self) -> float:
        """大小（MB）"""
        return self.size_bytes / (1024 * 1024)


class DeliveryPackager:
    """
    交付打包器
    
    负责将交付包打包为各种格式
    """
    
    def __init__(self, base_path: str = "./deliveries"):
        """
        初始化打包器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def package(
        self,
        delivery_package: DeliveryPackage,
        create_zip: bool = True,
        compression: int = 8,
    ) -> DeliveryArtifact:
        """
        打包交付物
        
        Args:
            delivery_package: 交付包
            create_zip: 是否创建 ZIP
            compression: ZIP 压缩级别 (1-9)
            
        Returns:
            交付产物
        """
        artifact = DeliveryArtifact(package=delivery_package)
        
        # 1. 创建目录结构
        package_dir = await self._create_directory_structure(delivery_package)
        
        # 2. 写入所有文件
        await self._write_files(package_dir, delivery_package)
        
        # 3. 创建 ZIP
        if create_zip:
            zip_path = await self._create_zip(package_dir, compression)
            artifact.zip_path = str(zip_path)
            artifact.size_bytes = zip_path.stat().st_size
        else:
            artifact.local_path = str(package_dir)
            artifact.size_bytes = self._get_directory_size(package_dir)
        
        artifact.delivery_method = "zip" if create_zip else "local"
        
        return artifact
    
    async def _create_directory_structure(
        self,
        package: DeliveryPackage,
    ) -> Path:
        """创建目录结构"""
        # 创建项目目录
        safe_name = self._safe_filename(package.project_name)
        package_dir = self.base_path / f"{safe_name}_{package.created_at}"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (package_dir / "docs").mkdir(exist_ok=True)
        (package_dir / "src").mkdir(exist_ok=True)
        (package_dir / "tests").mkdir(exist_ok=True)
        (package_dir / "deployment").mkdir(exist_ok=True)
        (package_dir / "reports").mkdir(exist_ok=True)
        
        return package_dir
    
    async def _write_files(self, package_dir: Path, package: DeliveryPackage):
        """写入所有文件"""
        # 1. 写入文档
        for doc in package.documents:
            doc_path = package_dir / "docs" / self._safe_filename(
                getattr(doc.metadata, 'title', doc.id) + ".md"
            )
            content = getattr(doc.content, 'content', '') if hasattr(doc, 'content') else ''
            doc_path.write_text(content, encoding='utf-8')
        
        # 2. 写入代码
        for path, content in package.source_code.items():
            code_path = package_dir / "src" / path
            code_path.parent.mkdir(parents=True, exist_ok=True)
            code_path.write_text(content, encoding='utf-8')
        
        # 3. 写入测试
        for test in package.test_cases:
            test_path = package_dir / "tests" / self._safe_filename(
                getattr(test.metadata, 'title', test.id) + ".md"
            )
            content = getattr(test.content, 'content', '') if hasattr(test, 'content') else ''
            test_path.write_text(content, encoding='utf-8')
        
        # 4. 写入测试报告
        for report in package.test_reports:
            report_path = package_dir / "reports" / self._safe_filename(
                getattr(report.metadata, 'title', report.id) + ".md"
            )
            content = getattr(report.content, 'content', '') if hasattr(report, 'content') else ''
            report_path.write_text(content, encoding='utf-8')
        
        # 5. 写入部署配置
        for path, content in package.deployment_configs.items():
            config_path = package_dir / "deployment" / path
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(content, encoding='utf-8')
        
        # 6. 写入交付清单
        if package.manifest:
            manifest_path = package_dir / "DELIVERY_MANIFEST.md"
            manifest_path.write_text(package.manifest, encoding='utf-8')
        
        # 7. 写入 README
        readme_content = self._generate_readme(package)
        readme_path = package_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
    
    async def _create_zip(self, package_dir: Path, compression: int) -> Path:
        """创建 ZIP 文件"""
        zip_path = package_dir.parent / f"{package_dir.name}.zip"
        
        # 压缩级别
        compresslevel = min(9, max(1, compression))
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir.parent)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _safe_filename(self, filename: str) -> str:
        """生成安全的文件名"""
        # 移除非法字符
        unsafe_chars = '<>:"/\\|？*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    def _get_directory_size(self, path: Path) -> int:
        """获取目录大小"""
        total = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
    
    def _generate_readme(self, package: DeliveryPackage) -> str:
        """生成 README"""
        return f"""# {package.project_name}

> 由 Agent Team System 自动生成

## 项目信息

- **创建时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(package.created_at))}
- **文档数量**: {package.total_documents}
- **代码文件**: {package.total_code_files}
- **测试文件**: {package.total_tests}

## 目录结构

```
{package.project_name}/
├── README.md
├── DELIVERY_MANIFEST.md
├── docs/           # 文档
├── src/            # 源代码
├── tests/          # 测试
├── deployment/     # 部署配置
└── reports/        # 报告
```

## 快速开始

请参考 `DELIVERY_MANIFEST.md` 获取详细信息。

## 质量指标

- 迭代次数：{package.metadata.get('iteration_count', 0)}
- 质量分数：{package.metadata.get('quality_score', 0.0):.2f}

---
*此项目由 Agent Team System 自动生成*
"""
