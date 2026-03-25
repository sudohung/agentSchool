"""Git 交付实现 - 支持将交付物推送到 Git 仓库."""

from __future__ import annotations

import asyncio
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import logging
import os
import tempfile

from delivery.models import DeliveryArtifact, DeliveryResult

logger = logging.getLogger(__name__)


@dataclass
class GitDeliveryConfig:
    """Git 交付配置"""
    
    repo_url: str
    branch: str = "main"
    commit_message: str = "Delivery: {timestamp}"
    author_name: str = "Agent Team System"
    author_email: str = "agent@example.com"
    target_dir: str = "deliveries"
    create_branch: bool = False
    branch_prefix: str = "delivery/"
    force_push: bool = False
    timeout: int = 300
    
    def get_commit_message(self) -> str:
        """获取格式化的提交消息"""
        return self.commit_message.format(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )


@dataclass
class GitExecutionResult:
    """Git 命令执行结果"""
    
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    command: str = ""
    
    def __bool__(self) -> bool:
        return self.success


class GitDeliveryExecutor:
    """
    Git 交付执行器
    
    职责：
    1. 克隆/拉取 Git 仓库
    2. 创建/切换分支
    3. 复制交付物到仓库
    4. 提交并推送更改
    """
    
    def __init__(
        self,
        work_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ):
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.gettempdir()) / "ats_git"
        self.progress_callback = progress_callback
        self._git_available: Optional[bool] = None
        
    async def _check_git_available(self) -> bool:
        """检查 Git 是否可用"""
        if self._git_available is not None:
            return self._git_available
            
        try:
            result = await self._run_git(["--version"])
            self._git_available = result.success
            return self._git_available
        except Exception:
            self._git_available = False
            return False
    
    async def _run_git(
        self,
        args: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> GitExecutionResult:
        """
        执行 Git 命令
        
        Args:
            args: Git 命令参数
            cwd: 工作目录
            env: 环境变量
            
        Returns:
            GitExecutionResult: 执行结果
        """
        cmd = ["git"] + args
        logger.debug(f"Running git command: {' '.join(args)}")
        
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )
            
            success = process.returncode == 0
            result = GitExecutionResult(
                success=success,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                return_code=process.returncode or 0,
                command=" ".join(args),
            )
            
            if not success:
                logger.warning(f"Git command failed: {result.stderr}")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Git command timed out: {' '.join(args)}")
            return GitExecutionResult(
                success=False,
                stderr="Command timed out",
                return_code=-1,
                command=" ".join(args),
            )
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return GitExecutionResult(
                success=False,
                stderr=str(e),
                return_code=-1,
                command=" ".join(args),
            )
    
    async def deliver(
        self,
        artifact: DeliveryArtifact,
        config: GitDeliveryConfig,
        local_path: Optional[Path] = None,
    ) -> DeliveryResult:
        """
        执行 Git 交付
        
        Args:
            artifact: 交付产物
            config: Git 配置
            local_path: 本地交付物路径
            
        Returns:
            DeliveryResult: 交付结果
        """
        delivery_id = f"git_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        self._report_progress(f"Starting Git delivery: {delivery_id}", 0)
        
        if not await self._check_git_available():
            return DeliveryResult(
                success=False,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="git",
                error="Git is not available on this system",
            )
        
        try:
            repo_path = await self._prepare_repo(config)
            if not repo_path:
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="git",
                    error="Failed to prepare repository",
                )
            
            self._report_progress("Repository prepared", 30)
            
            target_path = await self._copy_artifact(
                artifact, repo_path, config.target_dir, local_path
            )
            if not target_path:
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="git",
                    error="Failed to copy artifact",
                )
            
            self._report_progress("Artifact copied", 60)
            
            commit_success = await self._commit_and_push(repo_path, config)
            if not commit_success:
                return DeliveryResult(
                    success=False,
                    delivery_id=delivery_id,
                    artifact_id=artifact.id,
                    delivery_method="git",
                    error="Failed to commit and push changes",
                )
            
            self._report_progress("Delivery completed", 100)
            
            remote_url = config.repo_url
            if config.create_branch:
                branch_name = f"{config.branch_prefix}{int(time.time())}"
            else:
                branch_name = config.branch
            
            return DeliveryResult(
                success=True,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="git",
                delivery_path=f"{remote_url}/tree/{branch_name}/{config.target_dir}",
                verified=True,
            )
            
        except Exception as e:
            logger.error(f"Git delivery failed: {e}")
            return DeliveryResult(
                success=False,
                delivery_id=delivery_id,
                artifact_id=artifact.id,
                delivery_method="git",
                error=str(e),
            )
    
    async def _prepare_repo(self, config: GitDeliveryConfig) -> Optional[Path]:
        """准备仓库（克隆或拉取）"""
        repo_name = config.repo_url.split("/")[-1].replace(".git", "")
        repo_path = self.work_dir / repo_name
        
        if repo_path.exists():
            logger.info(f"Repository exists, pulling latest: {repo_path}")
            result = await self._run_git(["fetch", "--all"], cwd=repo_path)
            if not result.success:
                shutil.rmtree(repo_path)
                repo_path.mkdir(parents=True, exist_ok=True)
                return await self._clone_repo(config, repo_path)
            
            result = await self._run_git(
                ["checkout", config.branch],
                cwd=repo_path
            )
            if result.success:
                await self._run_git(["pull", "origin", config.branch], cwd=repo_path)
            else:
                if config.create_branch:
                    await self._run_git(
                        ["checkout", "-b", config.branch],
                        cwd=repo_path
                    )
            
            return repo_path
        else:
            repo_path.mkdir(parents=True, exist_ok=True)
            return await self._clone_repo(config, repo_path)
    
    async def _clone_repo(
        self,
        config: GitDeliveryConfig,
        repo_path: Path,
    ) -> Optional[Path]:
        """克隆仓库"""
        logger.info(f"Cloning repository: {config.repo_url}")
        
        result = await self._run_git(
            ["clone", "--branch", config.branch, config.repo_url, str(repo_path)],
        )
        
        if not result.success:
            logger.warning(f"Clone failed, trying without branch: {result.stderr}")
            result = await self._run_git(
                ["clone", config.repo_url, str(repo_path)],
            )
            
            if not result.success:
                logger.error(f"Clone failed: {result.stderr}")
                return None
            
            if config.create_branch:
                await self._run_git(
                    ["checkout", "-b", config.branch],
                    cwd=repo_path
                )
            else:
                await self._run_git(
                    ["checkout", config.branch],
                    cwd=repo_path
                )
        
        return repo_path
    
    async def _copy_artifact(
        self,
        artifact: DeliveryArtifact,
        repo_path: Path,
        target_dir: str,
        local_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """复制交付物到仓库"""
        target_path = repo_path / target_dir
        
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            
            if local_path and local_path.exists():
                if local_path.is_dir():
                    for item in local_path.iterdir():
                        dest = target_path / item.name
                        if item.is_dir():
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                else:
                    shutil.copy2(local_path, target_path)
            else:
                await self._create_readme(target_path, artifact)
            
            logger.info(f"Artifact copied to: {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Failed to copy artifact: {e}")
            return None
    
    async def _create_readme(self, target_path: Path, artifact: DeliveryArtifact):
        """创建 README 文件"""
        readme_content = f"""# Delivery

**Artifact ID**: {artifact.id}
**Name**: {artifact.name}
**Type**: {artifact.type}
**Delivered At**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Description

This delivery was automatically generated by Agent Team System.

## Contents

- Path: {artifact.path}
- Size: {artifact.size} bytes
"""
        readme_path = target_path / "README.md"
        readme_path.write_text(readme_content)
    
    async def _commit_and_push(
        self,
        repo_path: Path,
        config: GitDeliveryConfig,
    ) -> bool:
        """提交并推送更改"""
        logger.info("Committing and pushing changes")
        
        await self._run_git(["add", "."], cwd=repo_path)
        
        status_result = await self._run_git(
            ["status", "--porcelain"],
            cwd=repo_path
        )
        
        if not status_result.stdout.strip():
            logger.info("No changes to commit")
            return True
        
        env = {
            "GIT_AUTHOR_NAME": config.author_name,
            "GIT_AUTHOR_EMAIL": config.author_email,
            "GIT_COMMITTER_NAME": config.author_name,
            "GIT_COMMITTER_EMAIL": config.author_email,
        }
        
        commit_result = await self._run_git(
            ["commit", "-m", config.get_commit_message()],
            cwd=repo_path,
            env=env,
        )
        
        if not commit_result.success:
            logger.warning(f"Commit failed or nothing to commit: {commit_result.stderr}")
            return True
        
        push_args = ["push", "origin", config.branch]
        if config.force_push:
            push_args.insert(1, "--force")
        
        push_result = await self._run_git(push_args, cwd=repo_path)
        
        if not push_result.success:
            logger.error(f"Push failed: {push_result.stderr}")
            
            push_result = await self._run_git(
                ["push", "-u", "origin", config.branch],
                cwd=repo_path
            )
            
            return push_result.success
        
        return True
    
    def _report_progress(self, message: str, progress: int):
        """报告进度"""
        logger.info(f"Git delivery progress: {progress}% - {message}")
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    async def cleanup(self, max_age_hours: int = 24):
        """清理旧的工作目录"""
        if not self.work_dir.exists():
            return
        
        current_time = time.time()
        
        for item in self.work_dir.iterdir():
            if item.is_dir():
                stat = item.stat()
                age_hours = (current_time - stat.st_mtime) / 3600
                
                if age_hours > max_age_hours:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Cleaned up old repo: {item}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {item}: {e}")