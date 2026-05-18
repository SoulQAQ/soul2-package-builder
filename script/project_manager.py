"""
Installer Builder - 项目管理器
负责项目的读写、路径处理、最近项目记录等
"""
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


def get_base_dir() -> Path:
    """获取应用基础目录，兼容开发态和打包态"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).parent
    return Path(__file__).parent.parent


class ProjectManager:
    PROJECT_EXTENSION = ".ssc"
    DEFAULT_PROJECTS_DIR = "data/projects"
    MAX_RECENT_PROJECTS = 10

    def __init__(self):
        self.base_dir = get_base_dir()
        self.projects_dir = self.base_dir / self.DEFAULT_PROJECTS_DIR
        self.config_file = self.base_dir / "data" / "config.json"
        self._ensure_dirs()
        self.config = self._load_config()

    def _ensure_dirs(self):
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "recent_projects": [],
            "last_project": None,
            "last_output_dir": str(self.base_dir / "output"),
        }

    def _save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    # === 项目创建 ===

    def create_project(self, name: str, path: Optional[str] = None) -> dict:
        """创建新项目"""
        project_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        project = {
            "id": project_id,
            "name": name,
            "created": now,
            "modified": now,
            "version": "1.0.0",
            "config": {
                "app_name": name,
                "app_version": "1.0.0",
                "publisher": "",
                "main_exe": "",
                "install_dir": f"%ProgramFiles%\\{name}",
                "output_dir": str(self.base_dir / "output"),
                "install_icon": "",
                "source_dir": "",
                "uninstaller": True,
                "desktop_shortcut": True,
                "start_menu_shortcut": True,
            },
            "auto_version": {
                "increment_patch": False,
                "increment_minor": False,
                "increment_major": False,
            },
            "files": [],
            "build_log": [],
            "build_count": 0,
        }

        # 确定保存路径
        if path:
            save_path = Path(path)
            if not save_path.suffix == self.PROJECT_EXTENSION:
                save_path = save_path.with_suffix(self.PROJECT_EXTENSION)
        else:
            safe_name = self._safe_filename(name)
            save_path = self.projects_dir / f"{safe_name}{self.PROJECT_EXTENSION}"

        project["path"] = str(save_path)
        self._save_project(project)

        self._add_recent_project(project)
        return project

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        safe = "".join(c for c in name if c.isalnum() or c in " -_")
        return safe.strip() or "未命名项目"

    def _save_project(self, project: dict) -> bool:
        """保存项目到文件"""
        project["modified"] = datetime.now().isoformat()
        path = Path(project.get("path", ""))
        if not path:
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
        return True

    def save_project(self, project: dict) -> bool:
        """公开的保存方法"""
        result = self._save_project(project)
        if result:
            self._update_recent_project(project)
        return result

    def save_project_as(self, project: dict, new_path: str) -> dict:
        """另存为"""
        new_path = Path(new_path)
        if not new_path.suffix == self.PROJECT_EXTENSION:
            new_path = new_path.with_suffix(self.PROJECT_EXTENSION)

        project["path"] = str(new_path)
        project["id"] = str(uuid.uuid4())[:8]
        project["created"] = datetime.now().isoformat()
        self._save_project(project)
        self._add_recent_project(project)
        return project

    # === 项目读取 ===

    def load_project(self, path: str) -> Optional[dict]:
        """加载项目"""
        path = Path(path)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                project = json.load(f)

            # 迁移兼容
            project = self._migrate_project(project)
            project["path"] = str(path)

            self._add_recent_project(project)
            self.config["last_project"] = str(path)
            self._save_config()

            return project
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载项目失败: {e}")
            return None

    def _migrate_project(self, project: dict) -> dict:
        """项目配置迁移，兼容旧版本"""
        # 确保 auto_version 字段存在
        if "auto_version" not in project:
            project["auto_version"] = {
                "increment_patch": False,
                "increment_minor": False,
                "increment_major": False,
            }

        if "build_count" not in project:
            project["build_count"] = 0

        return project

    def load_project_by_id(self, project_id: str) -> Optional[dict]:
        """通过 ID 加载项目"""
        for path in self.projects_dir.glob(f"*{self.PROJECT_EXTENSION}"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    project = json.load(f)
                if project.get("id") == project_id:
                    return self.load_project(str(path))
            except:
                continue
        return None

    # === 项目列表 ===

    def list_projects(self) -> List[dict]:
        """列出所有项目"""
        projects = []
        for path in self.projects_dir.glob(f"*{self.PROJECT_EXTENSION}"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                projects.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "path": str(path),
                    "modified": data.get("modified"),
                    "version": data.get("config", {}).get("app_version", "1.0.0"),
                })
            except:
                continue
        return sorted(projects, key=lambda x: x.get("modified", ""), reverse=True)

    def delete_project(self, path: str) -> bool:
        """删除项目"""
        path = Path(path)
        if path.exists():
            path.unlink()
            self._remove_recent_project(str(path))
            return True
        return False

    # === 最近项目 ===

    def get_recent_projects(self) -> List[dict]:
        """获取最近项目列表"""
        recent = self.config.get("recent_projects", [])
        valid = []
        for item in recent:
            path = Path(item.get("path", ""))
            if path.exists():
                valid.append(item)
            else:
                self._remove_recent_project(str(path))
        return valid[:self.MAX_RECENT_PROJECTS]

    def _add_recent_project(self, project: dict):
        """添加到最近项目"""
        recent = self.config.get("recent_projects", [])
        path = project.get("path", "")

        # 移除已存在的
        recent = [r for r in recent if r.get("path") != path]

        # 添加到开头
        recent.insert(0, {
            "id": project.get("id"),
            "name": project.get("name"),
            "path": path,
            "modified": project.get("modified"),
        })

        self.config["recent_projects"] = recent[:self.MAX_RECENT_PROJECTS]
        self.config["last_project"] = path
        self._save_config()

    def _update_recent_project(self, project: dict):
        """更新最近项目记录"""
        path = project.get("path", "")
        recent = self.config.get("recent_projects", [])

        for item in recent:
            if item.get("path") == path:
                item["name"] = project.get("name")
                item["modified"] = project.get("modified")
                break

        self._save_config()

    def _remove_recent_project(self, path: str):
        """从最近项目移除"""
        recent = self.config.get("recent_projects", [])
        recent = [r for r in recent if r.get("path") != path]
        self.config["recent_projects"] = recent
        self._save_config()

    def clear_recent_projects(self):
        """清空最近项目"""
        self.config["recent_projects"] = []
        self._save_config()

    # === 项目选择对话框 ===

    def get_project_filter(self) -> str:
        """获取项目文件筛选器"""
        return f"安装项目 (*{self.PROJECT_EXTENSION})|*{self.PROJECT_EXTENSION}"
