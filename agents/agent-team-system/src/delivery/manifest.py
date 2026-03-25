"""交付清单生成器."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .models import DeliveryPackage, DeliveryArtifact, QualityLevel

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """
    交付清单生成器
    
    职责：
    1. 生成交付清单
    2. 包含所有交付物信息
    3. 支持多种格式（Markdown/JSON/YAML）
    """
    
    def __init__(self, format: str = "markdown"):
        self.format = format
        self._templates = {
            "markdown": self._generate_markdown,
            "json": self._generate_json,
        }
    
    async def generate(
        self,
        package: DeliveryPackage,
        artifacts: Optional[List[DeliveryArtifact]] = None,
        participating_agents: Optional[List[str]] = None,
        iterations: int = 1,
        total_time: float = 0.0,
    ) -> str:
        """
        生成交付清单
        
        Args:
            package: 交付包
            artifacts: 交付物列表（可选）
            participating_agents: 参与的 Agent 列表
            iterations: 迭代次数
            total_time: 总耗时（小时）
        
        Returns:
            str: 交付清单内容
        """
        logger.info(f"Generating manifest in {self.format} format")
        
        generator = self._templates.get(self.format, self._generate_markdown)
        
        manifest = generator(
            package=package,
            artifacts=artifacts or package.artifacts,
            participating_agents=participating_agents or [],
            iterations=iterations,
            total_time=total_time,
        )
        
        logger.info(f"Manifest generated: {len(manifest)} characters")
        
        return manifest
    
    def _generate_markdown(
        self,
        package: DeliveryPackage,
        artifacts: List[DeliveryArtifact],
        participating_agents: List[str],
        iterations: int,
        total_time: float,
    ) -> str:
        """生成 Markdown 格式清单"""
        
        # 项目信息
        content = f"# 交付清单\n\n"
        content += f"## 项目信息\n\n"
        content += f"- **项目名称**: {package.name}\n"
        content += f"- **版本**: {package.version}\n"
        content += f"- **交付 ID**: {package.id}\n"
        content += f"- **交付时间**: {self._format_timestamp(package.created_at)}\n"
        content += f"- **交付状态**: {package.status.value}\n\n"
        
        # 质量报告
        content += f"## 质量报告\n\n"
        content += f"- **质量评分**: {package.quality_score:.1%}\n"
        content += f"- **质量等级**: {package.quality_level.value}\n"
        content += f"- **检查项数量**: {len(package.quality_checks)}\n\n"
        
        if package.quality_checks:
            content += "### 质量检查详情\n\n"
            for check in package.quality_checks:
                status_icon = "✅" if check.passed else "❌"
                content += f"- {status_icon} **{check.check_name}**: {check.score:.1%}\n"
                if not check.passed:
                    content += f"  > {check.message}\n"
            content += "\n"
        
        # 交付物列表
        content += f"## 交付物列表\n\n"
        content += f"总计：**{len(artifacts)}** 个文件\n\n"
        
        # 按类型分组
        by_type = {}
        for artifact in artifacts:
            artifact_type = artifact.type
            if artifact_type not in by_type:
                by_type[artifact_type] = []
            by_type[artifact_type].append(artifact)
        
        for artifact_type, type_artifacts in by_type.items():
            content += f"### {self._get_type_name(artifact_type)}\n\n"
            for artifact in type_artifacts:
                size_str = self._format_size(artifact.size)
                content += f"- `{artifact.path}` ({size_str})\n"
            content += "\n"
        
        # 参与 Agent
        if participating_agents:
            content += f"## 参与 Agent\n\n"
            for agent in participating_agents:
                content += f"- {agent}\n"
            content += "\n"
        
        # 迭代信息
        content += f"## 开发信息\n\n"
        content += f"- **迭代次数**: {iterations}\n"
        content += f"- **总耗时**: {total_time:.2f} 小时\n\n"
        
        # 部署说明
        content += f"## 部署说明\n\n"
        content += self._generate_deployment_instructions(package)
        content += "\n"
        
        # 联系方式
        content += f"## 联系方式\n\n"
        content += f"如有问题，请通过以下方式联系：\n\n"
        content += f"- 项目仓库：[GitHub](https://github.com/...)\n"
        content += f"- 问题反馈：[Issues](https://github.com/.../issues)\n"
        
        return content
    
    def _generate_json(
        self,
        package: DeliveryPackage,
        artifacts: List[DeliveryArtifact],
        participating_agents: List[str],
        iterations: int,
        total_time: float,
    ) -> str:
        """生成 JSON 格式清单"""
        import json
        
        data = {
            "project": {
                "name": package.name,
                "version": package.version,
                "delivery_id": package.id,
                "created_at": package.created_at,
                "status": package.status.value,
            },
            "quality": {
                "score": package.quality_score,
                "level": package.quality_level.value,
                "checks": [
                    {
                        "name": check.check_name,
                        "passed": check.passed,
                        "score": check.score,
                        "message": check.message,
                    }
                    for check in package.quality_checks
                ],
            },
            "artifacts": [
                {
                    "id": artifact.id,
                    "name": artifact.name,
                    "type": artifact.type,
                    "path": artifact.path,
                    "size": artifact.size,
                }
                for artifact in artifacts
            ],
            "development": {
                "participating_agents": participating_agents,
                "iterations": iterations,
                "total_time_hours": total_time,
            },
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _get_type_name(self, artifact_type: str) -> str:
        """获取类型名称"""
        type_names = {
            "document": "文档",
            "source_code": "源代码",
            "test": "测试",
            "config": "配置",
            "deployment": "部署",
            "other": "其他",
        }
        return type_names.get(artifact_type, artifact_type)
    
    def _format_timestamp(self, timestamp: int) -> str:
        """格式化时间戳"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _generate_deployment_instructions(self, package: DeliveryPackage) -> str:
        """生成部署说明"""
        instructions = ""
        
        # 根据项目类型生成不同的部署说明
        if "python" in package.name.lower() or "py" in package.metadata.get("language", ""):
            instructions = """### Python 项目部署

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 文件配置环境变量
```

3. 运行项目
```bash
python -m src
```

4. 运行测试
```bash
pytest
```
"""
        elif "javascript" in package.name.lower() or "js" in package.metadata.get("language", ""):
            instructions = """### JavaScript 项目部署

1. 安装依赖
```bash
npm install
```

2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 文件配置环境变量
```

3. 运行项目
```bash
npm run dev
```

4. 构建生产版本
```bash
npm run build
```

5. 运行测试
```bash
npm test
```
"""
        else:
            instructions = """### 通用部署步骤

1. 查看项目文档了解详细部署说明
2. 安装必要的依赖
3. 配置环境变量
4. 运行项目
5. 验证部署成功

详细部署说明请参考项目文档。
"""
        
        return instructions
    
    async def save_manifest(
        self,
        manifest: str,
        output_path: Path,
    ) -> Path:
        """
        保存交付清单到文件
        
        Args:
            manifest: 交付清单内容
            output_path: 输出路径
        
        Returns:
            Path: 保存的文件路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(manifest, encoding='utf-8')
        logger.info(f"Manifest saved to: {output_path}")
        return output_path
