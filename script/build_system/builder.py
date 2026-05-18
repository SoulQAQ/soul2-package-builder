"""
Installer Builder - 构建器
高层接口，负责协调整个构建流程
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

from .manifest import Manifest
from .pipeline import Pipeline
from .task_runner import TaskRunner


class Builder:
    """安装包构建器"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.pipeline: Optional[Pipeline] = None
        self.log: list = []
        self.is_building = False

        # 回调
        self.on_log: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None

    def build(self, project: dict) -> Dict:
        """构建安装包"""
        if self.is_building:
            return {"success": False, "error": "已有构建任务在运行"}

        self.is_building = True
        self.log.clear()

        start_time = time.time()
        result = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": 0,
            "log": [],
            "output_file": None,
            "error": None,
        }

        try:
            # 创建清单
            self._log("info", "创建构建清单...")
            manifest = Manifest.from_project(project)

            # 验证清单
            valid, errors, warnings = manifest.validate()
            for e in errors:
                self._log("error", e)
            for w in warnings:
                self._log("warn", w)

            if not valid:
                result["error"] = "配置验证失败"
                result["log"] = self.log
                return result

            # 配置管线
            self._log("info", "配置构建管线...")
            self.pipeline = Pipeline(str(self.output_dir))
            self.pipeline.on_log = lambda m: self._log_entry(m)
            self.pipeline.on_progress = lambda c, t, m: self._progress(c, t, m)
            self.pipeline.configure(manifest)

            # 设置任务
            self._setup_tasks(manifest)

            # 执行构建
            self._log("info", "开始构建...")
            build_result = self.pipeline.run()

            result["success"] = build_result["success"]
            result["log"] = self.log
            result["output_file"] = build_result.get("output_file")

            if result["success"]:
                self._log("success", "构建完成！")
                result["manifest"] = manifest.to_dict()

        except Exception as e:
            self._log("error", f"构建异常: {e}")
            result["error"] = str(e)
            result["log"] = self.log

        finally:
            self.is_building = False
            result["end_time"] = datetime.now().isoformat()
            result["duration"] = time.time() - start_time

        return result

    def _setup_tasks(self, manifest: Manifest):
        """设置构建任务"""
        runner = self.pipeline.runner

        # 任务1：验证配置
        runner.add_task("验证配置", lambda: self._task_validate(manifest))

        # 任务2：扫描文件
        runner.add_task("扫描源文件", lambda: self._task_scan(manifest))

        # 任务3：生成清单
        runner.add_task("生成构建清单", lambda: self._task_manifest(manifest))

        # 任务4：准备输出
        runner.add_task("准备输出目录", lambda: self._task_prepare())

        # 任务5：构建
        runner.add_task("构建安装包", lambda: self._task_build(manifest))

        # 任务6：完成
        runner.add_task("完成构建", lambda: self._task_finalize(manifest))

    def _task_validate(self, manifest: Manifest) -> bool:
        """验证任务"""
        return True

    def _task_scan(self, manifest: Manifest) -> bool:
        """扫描任务"""
        self._log("info", f"扫描目录: {manifest.source_dir or '未设置'}")
        return True

    def _task_manifest(self, manifest: Manifest) -> bool:
        """清单任务"""
        manifest_file = self.output_dir / f"{manifest.app_name}_manifest.json"
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest.save(str(manifest_file))
        self._log("info", f"清单已保存: {manifest_file}")
        return True

    def _task_prepare(self) -> bool:
        """准备任务"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return True

    def _task_build(self, manifest: Manifest) -> bool:
        """构建任务"""
        self._log("info", f"构建目标: {manifest.app_name} v{manifest.app_version}")
        time.sleep(0.3)  # 模拟构建时间
        return True

    def _task_finalize(self, manifest: Manifest) -> bool:
        """完成任务"""
        safe_name = "".join(c for c in manifest.app_name
                           if c.isalnum() or c in " -_").strip() or "setup"
        output_file = self.output_dir / f"{safe_name}_setup.exe"

        # 模拟输出
        with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump({
                "type": "installer_stub",
                "app_name": manifest.app_name,
                "app_version": manifest.app_version,
                "publisher": manifest.publisher,
                "built": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

        self._log("success", f"输出文件: {output_file}")
        return True

    def _log(self, level: str, message: str):
        """记录日志"""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{level.upper()}] {message}"
        self.log.append(entry)
        if self.on_log:
            self.on_log(entry)

    def _log_entry(self, entry: str):
        """处理日志条目"""
        self.log.append(entry)
        if self.on_log:
            self.on_log(entry)

    def _progress(self, current: int, total: int, message: str):
        """处理进度"""
        if self.on_progress:
            self.on_progress(current, total, message)
