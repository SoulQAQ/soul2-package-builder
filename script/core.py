"""
Installer Builder - Core 业务逻辑
整合项目管理器、版本管理器和构建系统
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from project_manager import ProjectManager
from version_manager import VersionManager
from build_system import Builder


class Core:
    """核心业务逻辑"""

    def __init__(self):
        self.project_manager = ProjectManager()
        self.version_manager = VersionManager()
        self.builder = Builder(str(self.project_manager.base_dir / "output"))
        self.current_project: Optional[dict] = None

    # === 项目管理 ===

    def create_project(self, name: str, path: Optional[str] = None) -> dict:
        """创建新项目"""
        project = self.project_manager.create_project(name, path)
        self.current_project = project
        return project

    def save_project(self, project: Optional[dict] = None) -> bool:
        """保存项目"""
        if project is None:
            project = self.current_project
        if not project:
            return False
        return self.project_manager.save_project(project)

    def save_project_as(self, new_path: str) -> dict:
        """另存为"""
        if not self.current_project:
            raise ValueError("没有当前项目")
        self.current_project = self.project_manager.save_project_as(
            self.current_project, new_path
        )
        return self.current_project

    def load_project(self, path: str) -> Optional[dict]:
        """加载项目"""
        project = self.project_manager.load_project(path)
        if project:
            self.current_project = project
        return project

    def load_project_by_id(self, project_id: str) -> Optional[dict]:
        """通过 ID 加载项目"""
        project = self.project_manager.load_project_by_id(project_id)
        if project:
            self.current_project = project
        return project

    def list_projects(self) -> List[dict]:
        """列出项目"""
        return self.project_manager.list_projects()

    def get_recent_projects(self) -> List[dict]:
        """获取最近项目"""
        return self.project_manager.get_recent_projects()

    def delete_project(self, path: str) -> bool:
        """删除项目"""
        if self.current_project and self.current_project.get("path") == path:
            self.current_project = None
        return self.project_manager.delete_project(path)

    def close_project(self):
        """关闭当前项目"""
        if self.current_project:
            self.save_project()
        self.current_project = None

    # === 版本管理 ===

    def get_version_info(self) -> dict:
        """获取当前版本信息"""
        if not self.current_project:
            return VersionManager.get_version_info("1.0.0")
        version = self.current_project.get("config", {}).get("app_version", "1.0.0")
        return VersionManager.get_version_info(version)

    def set_version(self, version: str) -> bool:
        """设置版本号"""
        if not self.current_project:
            return False
        if not VersionManager.validate(version):
            return False
        self.current_project["config"]["app_version"] = version
        return True

    def auto_increment_version(self) -> str:
        """自动递增版本号"""
        if not self.current_project:
            return "1.0.0"

        config = self.current_project.get("config", {})
        auto = self.current_project.get("auto_version", {})
        current = config.get("app_version", "1.0.0")

        new_version = VersionManager.auto_increment(
            current,
            increment_patch=auto.get("increment_patch", False),
            increment_minor=auto.get("increment_minor", False),
            increment_major=auto.get("increment_major", False),
        )

        # 更新版本号
        config["app_version"] = new_version

        # 主版本或次版本递增后，重置勾选状态
        if auto.get("increment_major") or auto.get("increment_minor"):
            auto["increment_major"] = False
            auto["increment_minor"] = False
            auto["increment_patch"] = False

        self.save_project()
        return new_version

    def set_auto_version_config(self, patch: bool = False,
                                  minor: bool = False,
                                  major: bool = False) -> dict:
        """设置自动版本配置"""
        if not self.current_project:
            return {}

        # 主版本或次版本勾选时，禁用修订版本
        if major or minor:
            patch = False

        self.current_project["auto_version"] = {
            "increment_patch": patch,
            "increment_minor": minor,
            "increment_major": major,
        }
        self.save_project()
        return self.current_project["auto_version"]

    # === 文件操作 ===

    def scan_directory(self, directory: str) -> dict:
        """扫描目录"""
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"files": [], "total_size": 0, "exe_files": []}

        files = []
        total_size = 0
        exe_files = []

        for f in dir_path.rglob("*"):
            if f.is_file():
                size = f.stat().st_size
                total_size += size
                rel_path = f.relative_to(dir_path)
                files.append({
                    "path": str(rel_path),
                    "size": size,
                    "size_formatted": self._format_size(size),
                })
                if f.suffix.lower() == ".exe":
                    exe_files.append(str(rel_path))

        # 更新当前项目的源目录
        if self.current_project:
            self.current_project["config"]["source_dir"] = directory
            self.current_project["files"] = files

        return {
            "files": files,
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size),
            "exe_files": exe_files,
            "file_count": len(files),
        }

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
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
        """执行构建"""
        if not self.current_project:
            return {"success": False, "error": "没有当前项目"}

        # 设置回调
        self.builder.on_log = on_log
        self.builder.on_progress = on_progress

        # 执行构建
        result = self.builder.build(self.current_project)

        if result["success"]:
            # 自动递增版本号
            self.auto_increment_version()

            # 更新构建计数
            self.current_project["build_count"] = \
                self.current_project.get("build_count", 0) + 1
            self.current_project["last_build"] = datetime.now().isoformat()
            self.save_project()

        return result

    def validate_project(self, project: Optional[dict] = None) -> dict:
        """验证项目配置"""
        if project is None:
            project = self.current_project
        if not project:
            return {"valid": False, "errors": ["没有项目"], "warnings": []}

        errors = []
        warnings = []
        config = project.get("config", {})

        if not config.get("app_name"):
            errors.append("应用名称不能为空")
        if not config.get("app_version"):
            warnings.append("建议设置版本号")
        if not config.get("main_exe"):
            errors.append("主程序不能为空")
        if not config.get("output_dir"):
            warnings.append("未设置输出目录，将使用默认目录")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # === 输出 ===

    def list_outputs(self) -> List[dict]:
        """列出输出文件"""
        outputs = []
        output_dir = Path(self.project_manager.base_dir / "output")
        if output_dir.exists():
            for f in output_dir.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    stat = f.stat()
                    outputs.append({
                        "name": f.name,
                        "path": str(f),
                        "size": stat.st_size,
                        "size_formatted": self._format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
        return sorted(outputs, key=lambda x: x["modified"], reverse=True)

    # === 配置 ===

    def get_config(self) -> dict:
        """获取应用配置"""
        return self.project_manager.config