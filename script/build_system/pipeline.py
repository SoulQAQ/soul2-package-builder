"""
Installer Builder - 构建管线
负责组织和协调构建流程的各个阶段
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from .task_runner import TaskRunner, TaskStatus
from .manifest import Manifest


class PipelineStage:
    """构建阶段"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description or name
        self.tasks: List[Callable] = []
        self.status = TaskStatus.PENDING


class Pipeline:
    """构建管线"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.stages: List[PipelineStage] = []
        self.runner = TaskRunner()
        self.log: List[str] = []
        self.manifest: Optional[Manifest] = None

        # 回调
        self.on_stage_start: Optional[Callable] = None
        self.on_stage_end: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None

        # 设置回调
        self.runner.on_log = self._handle_log
        self.runner.on_progress = self._handle_progress

    def _handle_log(self, message: str):
        """处理日志"""
        self.log.append(message)
        if self.on_log:
            self.on_log(message)

    def _handle_progress(self, current: int, total: int, message: str):
        """处理进度"""
        if self.on_progress:
            self.on_progress(current, total, message)

    def add_stage(self, name: str, description: str = "") -> PipelineStage:
        """添加构建阶段"""
        stage = PipelineStage(name, description)
        self.stages.append(stage)
        return stage

    def setup_default_stages(self):
        """设置默认构建阶段"""
        self.add_stage("validate", "验证配置")
        self.add_stage("scan", "扫描文件")
        self.add_stage("manifest", "生成清单")
        self.add_stage("prepare", "准备输出")
        self.add_stage("build", "构建安装包")
        self.add_stage("finalize", "完成输出")

    def configure(self, manifest: Manifest):
        """配置管线"""
        self.manifest = manifest
        self.output_dir = Path(manifest.output_dir or "output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        """执行构建管线"""
        start_time = time.time()
        result = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": 0,
            "log": self.log,
            "output_file": None,
            "error": None,
        }

        try:
            # 执行所有任务
            success = self.runner.run_all()
            result["success"] = success

            if success:
                # 生成输出文件
                output_file = self._generate_output()
                result["output_file"] = str(output_file)

        except Exception as e:
            result["error"] = str(e)
            self.log.append(f"[错误] {e}")

        result["end_time"] = datetime.now().isoformat()
        result["duration"] = time.time() - start_time
        result["summary"] = self.runner.get_summary()

        return result

    def _generate_output(self) -> Path:
        """生成输出文件（当前为模拟）"""
        if not self.manifest:
            raise ValueError("清单未配置")

        safe_name = "".join(c for c in self.manifest.app_name
                           if c.isalnum() or c in " -_").strip() or "setup"
        output_file = self.output_dir / f"{safe_name}_setup.exe"

        # 模拟输出（实际项目中会调用真正的安装器引擎）
        with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump({
                "type": "installer_stub",
                "app_name": self.manifest.app_name,
                "app_version": self.manifest.app_version,
                "publisher": self.manifest.publisher,
                "built": datetime.now().isoformat(),
                "manifest": self.manifest.to_dict(),
            }, f, indent=2, ensure_ascii=False)

        # 创建一个空的 exe 占位符
        with open(output_file, "wb") as f:
            f.write(b"")

        return output_file

    def get_log(self) -> List[str]:
        """获取日志"""
        return self.log.copy()
