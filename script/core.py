"""
Installer Builder - Core 业务逻辑
整合项目管理、版本管理和构建系统
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from project_manager import ProjectManager
from version_manager import VersionManager
from build_system import Builder


class Core:
    """核心业务逻辑。"""

    def __init__(self):
        self.project_manager = ProjectManager()
        self.builder = Builder(str(self.project_manager.base_dir / "output"))
        self.current_project: Optional[dict] = None

    # === 项目管理 ===

    def create_project(self, name: str, path: Optional[str] = None) -> dict:
        project = self.project_manager.create_project(name, path)
        self.current_project = project
        return project

    def _normalize_current_project(self):
        if self.current_project:
            path = self.current_project.get("path") or self.current_project.get("projectPath")
            if path:
                self.current_project = self.project_manager._normalize_project(
                    self.current_project, path=Path(path)
                )
            else:
                self.current_project = self.project_manager._normalize_project(self.current_project)

    def save_project(self, project: Optional[dict] = None) -> bool:
        if project is None:
            project = self.current_project
        if not project:
            return False
        self.current_project = project
        self._normalize_current_project()
        return self.project_manager.save_project(self.current_project)

    def save_project_as(self, new_path: str) -> dict:
        if not self.current_project:
            raise ValueError("没有当前项目")
        self._normalize_current_project()
        self.current_project = self.project_manager.save_project_as(self.current_project, new_path)
        return self.current_project

    def load_project(self, path: str) -> Optional[dict]:
        project = self.project_manager.load_project(path)
        if project:
            self.current_project = project
        return project

    def load_project_by_id(self, project_id: str) -> Optional[dict]:
        project = self.project_manager.load_project_by_id(project_id)
        if project:
            self.current_project = project
        return project

    def list_projects(self) -> List[dict]:
        return self.project_manager.list_projects()

    def get_recent_projects(self) -> List[dict]:
        return self.project_manager.get_recent_projects()

    def delete_project(self, path: str) -> bool:
        if self.current_project:
            current_path = self.current_project.get("path") or self.current_project.get("projectPath")
            if current_path and Path(current_path) == Path(path):
                self.current_project = None
        return self.project_manager.delete_project(path)

    def close_project(self):
        if self.current_project:
            self.save_project()
        self.current_project = None

    # === 版本管理 ===

    def get_version_info(self) -> dict:
        if not self.current_project:
            return VersionManager.get_version_info("1.0.0")
        version = self.current_project.get("config", {}).get("app_version", "1.0.0")
        return VersionManager.get_version_info(version)

    def set_version(self, version: str) -> bool:
        if not self.current_project:
            return False
        normalized = VersionManager.normalize(version)
        if not VersionManager.validate(normalized):
            return False
        self.current_project.setdefault("config", {})["app_version"] = normalized
        major, minor, patch = VersionManager.parse(normalized)
        self.current_project["version"] = {"major": major, "minor": minor, "patch": patch}
        self.current_project["versionString"] = normalized
        return True

    def set_auto_version_config(self, patch: bool = False, minor: bool = False, major: bool = False) -> dict:
        if not self.current_project:
            return {}

        normalized = VersionManager.normalize_auto_flags(
            increment_patch=patch,
            increment_minor=minor,
            increment_major=major,
        )
        self.current_project["auto_version"] = dict(normalized)
        self.current_project["autoVersion"] = {
            "patch": normalized["increment_patch"],
            "minor": normalized["increment_minor"],
            "major": normalized["increment_major"],
        }
        self.save_project()
        return self.current_project["auto_version"]

    def get_auto_version_config(self) -> dict:
        if not self.current_project:
            return {"increment_patch": False, "increment_minor": False, "increment_major": False}
        auto = self.current_project.get("auto_version", {})
        return VersionManager.normalize_auto_flags(
            increment_patch=auto.get("increment_patch", False),
            increment_minor=auto.get("increment_minor", False),
            increment_major=auto.get("increment_major", False),
        )

    def apply_version_increment_after_success(self) -> dict:
        """
        构建成功后推进版本号。
        """
        if not self.current_project:
            return {
                "changed": False,
                "old_version": "1.0.0",
                "new_version": "1.0.0",
                "strategy": "none",
                "next_auto_version": {"increment_patch": False, "increment_minor": False, "increment_major": False},
            }

        config = self.current_project.setdefault("config", {})
        current_version = VersionManager.normalize(config.get("app_version", "1.0.0"))
        auto = self.get_auto_version_config()
        increment_result = VersionManager.next_version_with_strategy(
            current_version,
            increment_patch=auto.get("increment_patch", False),
            increment_minor=auto.get("increment_minor", False),
            increment_major=auto.get("increment_major", False),
        )

        config["app_version"] = increment_result["new_version"]
        next_auto = increment_result["next_auto_version"]
        self.current_project["auto_version"] = dict(next_auto)
        self.current_project["autoVersion"] = {
            "patch": next_auto["increment_patch"],
            "minor": next_auto["increment_minor"],
            "major": next_auto["increment_major"],
        }
        major, minor, patch = VersionManager.parse(increment_result["new_version"])
        self.current_project["version"] = {"major": major, "minor": minor, "patch": patch}
        self.current_project["versionString"] = increment_result["new_version"]
        self.save_project()
        return increment_result

    # === 文件操作 ===

    def scan_directory(self, directory: str) -> dict:
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"files": [], "total_size": 0, "exe_files": [], "file_count": 0}

        files = []
        total_size = 0
        exe_files = []

        for f in dir_path.rglob("*"):
            if f.is_file():
                size = f.stat().st_size
                total_size += size
                rel_path = f.relative_to(dir_path)
                suffix = f.suffix.lower().lstrip(".")
                files.append(
                    {
                        "name": f.name,
                        "path": str(rel_path),
                        "relative_path": str(rel_path),
                        "size": size,
                        "size_formatted": self._format_size(size),
                        "type": suffix or "文件",
                    }
                )
                if f.suffix.lower() == ".exe":
                    exe_files.append(str(rel_path))

        files.sort(key=lambda item: item["path"].lower())

        if self.current_project:
            self.current_project.setdefault("config", {})["source_dir"] = str(dir_path)
            self.current_project["files"] = files
            self.current_project.setdefault("paths", {})["sourceDir"] = str(dir_path)

        return {
            "files": files,
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size),
            "exe_files": exe_files,
            "file_count": len(files),
            "source_dir": str(dir_path),
        }

    def _format_size(self, size: int) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    def get_file_info(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"exists": False}

        stat = path.stat()
        return {
            "exists": True,
            "name": path.name,
            "size": stat.st_size,
            "size_formatted": self._format_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_exe": path.suffix.lower() == ".exe",
        }

    # === 构建 ===

    def build(self, on_log=None, on_progress=None) -> dict:
        if not self.current_project:
            return {"success": False, "error": "没有当前项目"}

        self.builder.on_log = on_log
        self.builder.on_progress = on_progress

        result = self.builder.build(self.current_project)
        if not result.get("success"):
            result["version_increment"] = {
                "changed": False,
                "old_version": self.current_project.get("config", {}).get("app_version", "1.0.0"),
                "new_version": self.current_project.get("config", {}).get("app_version", "1.0.0"),
                "strategy": "none",
            }
            return result

        increment_result = self.apply_version_increment_after_success()
        build_info = self.current_project.setdefault("build", {})
        build_info["count"] = int(build_info.get("count") or 0) + 1
        build_info["lastBuildAt"] = datetime.now().isoformat()
        build_info["simulated"] = True
        self.current_project["build_count"] = build_info["count"]
        self.current_project["last_build"] = build_info["lastBuildAt"]
        self.save_project()

        result["version_increment"] = increment_result
        result["build_mode"] = "simulated"
        result["message"] = "当前为模拟构建流程，后续将接入真实安装包生成引擎。"
        return result

    def validate_project(self, project: Optional[dict] = None) -> dict:
        target = project or self.current_project
        if not target:
            return {"valid": False, "errors": ["没有项目"], "warnings": [], "field_errors": {}}

        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, str] = {}

        config = target.get("config", {})
        app_name = str(config.get("app_name") or "").strip()
        main_exe = str(config.get("main_exe") or "").strip()
        app_version = str(config.get("app_version") or "").strip()
        output_dir = str(config.get("output_dir") or "").strip()

        if not app_name:
            msg = "应用名称不能为空"
            errors.append(msg)
            field_errors["appName"] = msg

        if not main_exe:
            msg = "主程序不能为空"
            errors.append(msg)
            field_errors["mainExe"] = msg

        if not app_version:
            msg = "版本号不能为空"
            errors.append(msg)
            field_errors["verMajor"] = msg
        elif not VersionManager.validate(app_version):
            msg = "版本号必须为 a.b.c 且为非负整数"
            errors.append(msg)
            field_errors["verMajor"] = msg

        if not output_dir:
            warnings.append("未设置输出目录，将使用默认目录")

        source_dir = str(config.get("source_dir") or "").strip()
        if source_dir and not Path(source_dir).exists():
            warnings.append("源文件目录不存在，请重新选择")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "field_errors": field_errors,
        }

    # === 输出 ===

    def list_outputs(self) -> List[dict]:
        outputs = []
        output_dir = self.current_project.get("config", {}).get("output_dir") if self.current_project else None
        target_dir = Path(output_dir) if output_dir else Path(self.project_manager.base_dir / "output")
        if target_dir.exists():
            for file_path in target_dir.glob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    stat = file_path.stat()
                    suffix = file_path.suffix.lower()
                    if suffix not in {".exe", ".msi", ".zip", ".json"}:
                        continue
                    outputs.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path),
                            "size": stat.st_size,
                            "size_formatted": self._format_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "type": suffix.lstrip("."),
                        }
                    )
        outputs.sort(key=lambda item: item["modified"], reverse=True)
        return outputs

    # === 配置 ===

    def get_config(self) -> dict:
        return self.project_manager.config
