#!/usr/bin/env python3
"""
代码执行验证模块
负责代码生成后的执行、测试和验证
"""
import asyncio
import os
import json
import tempfile
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration: float = 0.0
    error: Optional[str] = None


@dataclass
class TestCase:
    """测试用例"""
    name: str
    input_data: str = ""
    expected_output: str = ""
    test_code: str = ""  # 独立的测试代码


@dataclass
class TestResult:
    """测试结果"""
    status: TestStatus
    test_name: str
    duration: float = 0.0
    message: str = ""
    actual_output: str = ""
    expected_output: str = ""


@dataclass
class ValidationReport:
    """验证报告"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)
    code_execution: Optional[ExecutionResult] = None
    summary: str = ""


class CodeExecutor:
    """代码执行器"""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="agent_workspace_")
        self.current_project_dir = None
        print(f"[Executor] Workspace: {self.workspace_dir}")
    
    def create_project(self, project_name: str, language: Language) -> str:
        """创建项目目录"""
        project_dir = os.path.join(self.workspace_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        self.current_project_dir = project_dir
        
        # 根据语言创建项目结构
        if language == Language.PYTHON:
            self._create_python_project(project_dir)
        elif language == Language.JAVASCRIPT:
            self._create_js_project(project_dir)
        
        print(f"[Executor] Created project: {project_dir}")
        return project_dir
    
    def _create_python_project(self, project_dir: str):
        """创建Python项目结构"""
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
        
        # 创建 __init__.py
        Path(os.path.join(project_dir, "src", "__init__.py")).touch()
        Path(os.path.join(project_dir, "tests", "__init__.py")).touch()
        
        # 创建 requirements.txt
        with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
            f.write("# Add dependencies here\n")
    
    def _create_js_project(self, project_dir: str):
        """创建JS项目结构"""
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
        
        # 创建 package.json
        package_json = {
            "name": "agent-project",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "test": "node --test tests/"
            }
        }
        with open(os.path.join(project_dir, "package.json"), "w") as f:
            json.dump(package_json, f, indent=2)
    
    def write_code(self, filename: str, content: str) -> str:
        """写入代码文件"""
        if not self.current_project_dir:
            raise ValueError("No project created. Call create_project() first.")
        
        filepath = os.path.join(self.current_project_dir, filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"[Executor] Written: {filename} ({len(content)} bytes)")
        return filepath
    
    def execute_code(self, filename: str, language: Language, args: list[str] = None) -> ExecutionResult:
        """执行代码"""
        if not self.current_project_dir:
            return ExecutionResult(success=False, error="No project created")
        
        import time
        start_time = time.time()
        
        filepath = os.path.join(self.current_project_dir, filename)
        
        try:
            if language == Language.PYTHON:
                cmd = ["python3", filepath] + (args or [])
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.current_project_dir
                )
            elif language == Language.JAVASCRIPT:
                cmd = ["node", filepath] + (args or [])
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.current_project_dir
                )
            else:
                return ExecutionResult(success=False, error=f"Unsupported language: {language.value}")
            
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration=duration
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(success=False, error="Execution timeout (60s)", duration=60.0)
        except Exception as e:
            return ExecutionResult(success=False, error=str(e), duration=time.time() - start_time)
    
    def run_tests(self, language: Language, test_framework: str = "auto") -> ValidationReport:
        """运行测试"""
        if not self.current_project_dir:
            return ValidationReport(summary="No project created")
        
        import time
        start_time = time.time()
        
        report = ValidationReport()
        
        try:
            if language == Language.PYTHON:
                report = self._run_python_tests(test_framework)
            elif language == Language.JAVASCRIPT:
                report = self._run_js_tests()
            else:
                report.summary = f"Unsupported language: {language.value}"
                
        except Exception as e:
            report.summary = f"Test execution error: {str(e)}"
        
        report.duration = time.time() - start_time
        return report
    
    def _run_python_tests(self, framework: str) -> ValidationReport:
        """运行Python测试"""
        report = ValidationReport()
        
        # 尝试使用pytest
        test_files = list(Path(self.current_project_dir).rglob("test_*.py"))
        test_files.extend(Path(self.current_project_dir).rglob("*_test.py"))
        
        if not test_files:
            report.summary = "No test files found"
            return report
        
        cmd = ["python3", "-m", "pytest", "-v", "--tb=short"]
        cmd.extend([str(f) for f in test_files])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.current_project_dir
            )
            
            report.code_execution = ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
            
            # 解析pytest输出
            if "passed" in result.stdout or "PASSED" in result.stdout:
                report.passed = 1
                report.passed = max(report.passed, 
                    sum(1 for line in result.stdout.split('\n') if 'PASSED' in line))
            if "failed" in result.stdout or "FAILED" in result.stdout:
                report.failed = max(report.failed,
                    sum(1 for line in result.stdout.split('\n') if 'FAILED' in line))
            
            report.total_tests = report.passed + report.failed
            report.summary = f"Pytest: {report.passed} passed, {report.failed} failed"
            
        except FileNotFoundError:
            # pytest not installed, try unittest
            cmd = ["python3", "-m", "unittest", "discover", "-s", "tests"]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.current_project_dir
                )
                report.code_execution = ExecutionResult(
                    success=result.returncode == 0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode
                )
                report.summary = f"Unittest: exit code {result.returncode}"
            except Exception as e:
                report.summary = f"No test framework found: {str(e)}"
        except Exception as e:
            report.summary = f"Test error: {str(e)}"
        
        return report
    
    def _run_js_tests(self) -> ValidationReport:
        """运行JavaScript测试"""
        report = ValidationReport()
        
        # 检查是否有测试文件
        test_files = list(Path(self.current_project_dir).rglob("*.test.js"))
        test_files.extend(Path(self.current_project_dir).rglob("*.spec.js"))
        
        if not test_files:
            report.summary = "No test files found"
            return report
        
        # 尝试运行node test
        cmd = ["node", "--test"] + [str(f) for f in test_files]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.current_project_dir
            )
            
            report.code_execution = ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
            
            report.summary = f"Node test: exit code {result.returncode}"
            
        except Exception as e:
            report.summary = f"Test error: {str(e)}"
        
        return report
    
    def cleanup(self):
        """清理工作区"""
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)
            print(f"[Executor] Cleaned up: {self.workspace_dir}")


# ============== 便捷函数 ==============

async def execute_and_validate(code: str, language: Language, test_cases: list[TestCase] = None) -> ValidationReport:
    """
    执行代码并验证
    """
    executor = CodeExecutor()
    
    try:
        # 创建项目
        project_name = "temp_project"
        executor.create_project(project_name, language)
        
        # 根据语言确定文件名
        if language == Language.PYTHON:
            main_file = "src/main.py"
        elif language == Language.JAVASCRIPT:
            main_file = "src/main.js"
        else:
            main_file = "src/main"
        
        # 写入代码
        executor.write_code(main_file, code)
        
        # 执行代码
        exec_result = executor.execute_code(main_file, language)
        
        # 创建报告
        report = ValidationReport()
        report.code_execution = exec_result
        report.total_tests = 1
        report.passed = 1 if exec_result.success else 0
        report.failed = 0 if exec_result.success else 1
        report.summary = f"Execution: {'Success' if exec_result.success else 'Failed'}"
        
        if test_cases:
            # 运行测试用例
            for tc in test_cases:
                # 写入测试文件
                if language == Language.PYTHON:
                    test_file = f"tests/test_{tc.name}.py"
                    test_code = f"""
import {tc.name}

def test_{tc.name}():
    result = {tc.name}.run({tc.input_data!r})
    expected = {tc.expected_output!r}
    assert result == expected, f"Expected {{expected}}, got {{result}}"
"""
                else:
                    test_file = f"tests/{tc.name}.test.js"
                    test_code = f"""
import {{ run }} from '../src/main.js';
import assert from 'assert';

const result = run({tc.input_data});
assert.strictEqual(result, {tc.expected_output!r});
"""
                
                executor.write_code(test_file, test_code)
            
            # 运行测试
            test_report = executor.run_tests(language)
            report.test_results = test_report.test_results
            report.total_tests = test_report.total_tests
            report.passed = test_report.passed
            report.failed = test_report.failed
        
        return report
        
    finally:
        executor.cleanup()


if __name__ == "__main__":
    # 简单测试
    async def test():
        code = '''
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(2, 3))
'''
        result = await execute_and_validate(code, Language.PYTHON)
        print(f"Result: {result.summary}")
        print(f"Execution: {result.code_execution}")
    
    asyncio.run(test())
