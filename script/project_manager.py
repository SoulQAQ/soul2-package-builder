"""
Installer Builder - 项目管理器
负责 .ssc 项目配置的创建、读写、迁移和最近项目维护
"""
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from version_manager import VersionManager


def get_base_dir() -> Path:
    """获取应用根目录，兼容开发态和 PyInstaller。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class ProjectManager:
    PROJECT_EXTENSION = ".ssc"
    DEFAULT_PROJECTS_DIR = "data/projects"
    MAX_RECENT_PROJECTS = 5
    SCHEMA_VERSION = 1

    def __init__(self):
        self.base_dir = get_base_dir()
        self.projects_dir = self.base_dir / self.DEFAULT_PROJECTS_DIR
        self.config_file = self.base_dir / "data" / "config.json"
        self._ensure_dirs()
        self.config = self._load_config()

    def _ensure_dirs(self):
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "output").mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        if self.config_file.exists():
            try:
                with self.config_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("recent_projects", [])
                    data.setdefault("last_project", None)
                    data.setdefault("last_output_dir", str(self.base_dir / "output"))
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "recent_projects": [],
            "last_project": None,
            "last_output_dir": str(self.base_dir / "output"),
        }

    def _save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with self.config_file.open("w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c for c in (name or "") if c.isalnum() or c in " -_")
        safe = safe.strip()
        return safe or "未命名项目"

    def _ensure_project_extension(self, path: Path) -> Path:
        if path.suffix.lower() != self.PROJECT_EXTENSION:
            return path.with_suffix(self.PROJECT_EXTENSION)
        return path

    def _default_project_data(self, name: str) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        safe_name = (name or "").strip() or "未命名项目"
        install_dir = f"%ProgramFiles%\\{safe_name}"
        output_dir = str(self.base_dir / "output")
        return {
            "schemaVersion": self.SCHEMA_VERSION,
            "id": str(uuid.uuid4())[:8],
            "projectName": safe_name,
            "projectPath": "",
            "name": safe_name,
            "createdAt": now,
            "updatedAt": now,
            "created": now,
            "modified": now,
            "appName": safe_name,
            "publisher": "",
            "version": {"major": 1, "minor": 0, "patch": 0},
            "autoVersion": {"patch": False, "minor": False, "major": False},
            "paths": {
                "mainExecutable": "",
                "installIcon": "",
                "sourceDir": "",
                "installDir": install_dir,
                "outputDir": output_dir,
            },
            "shortcuts": {
                "desktop": True,
                "startMenu": True,
                "uninstaller": True,
            },
            "build": {"simulated": True, "count": 0, "lastBuildAt": None},
            "files": [],
            "build_log": [],
            "build_count": 0,
            "config": {
                "app_name": safe_name,
                "app_version": "1.0.0",
                "publisher": "",
                "main_exe": "",
                "install_dir": install_dir,
                "output_dir": output_dir,
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
            "version": "1.0.0",
        }

    def _normalize_project(self, project: Dict[str, Any], path: Optional[Path] = None) -> Dict[str, Any]:
        """兼容旧结构并补齐默认字段。"""
        data = dict(project or {})
        now = datetime.now().isoformat()

        if not data.get("id"):
            data["id"] = str(uuid.uuid4())[:8]

        name = (
            data.get("projectName")
            or data.get("name")
            or data.get("appName")
            or data.get("config", {}).get("app_name")
            or "未命名项目"
        )
        name = str(name).strip() or "未命名项目"
        data["projectName"] = name
        data["name"] = name
        data["appName"] = data.get("appName") or data.get("config", {}).get("app_name") or name

        default_project = self._default_project_data(name)
        data.setdefault("schemaVersion", self.SCHEMA_VERSION)
        data["schemaVersion"] = int(data.get("schemaVersion") or self.SCHEMA_VERSION)

        created_at = data.get("createdAt") or data.get("created") or now
        updated_at = data.get("updatedAt") or data.get("modified") or now
        data["createdAt"] = created_at
        data["updatedAt"] = updated_at
        data["created"] = created_at
        data["modified"] = updated_at

        config = dict(default_project["config"])
        config.update(data.get("config", {}))
        config["app_name"] = str(config.get("app_name") or data["appName"] or name).strip() or name
        data["appName"] = config["app_name"]
        data["projectName"] = data["appName"]
        data["name"] = data["appName"]

        normalized_version = VersionManager.normalize(
            str(config.get("app_version") or data.get("version") or "1.0.0")
        )
        config["app_version"] = normalized_version
        v_major, v_minor, v_patch = VersionManager.parse(normalized_version)
        data["version"] = {"major": v_major, "minor": v_minor, "patch": v_patch}

        auto_obj = data.get("auto_version", {})
        if "autoVersion" in data and isinstance(data.get("autoVersion"), dict):
            auto_src = data["autoVersion"]
            auto_obj = {
                "increment_patch": bool(auto_src.get("patch", False)),
                "increment_minor": bool(auto_src.get("minor", False)),
                "increment_major": bool(auto_src.get("major", False)),
            }
        auto_flags = VersionManager.normalize_auto_flags(
            increment_patch=bool(auto_obj.get("increment_patch", False)),
            increment_minor=bool(auto_obj.get("increment_minor", False)),
            increment_major=bool(auto_obj.get("increment_major", False)),
        )
        data["auto_version"] = dict(auto_flags)
        data["autoVersion"] = {
            "patch": auto_flags["increment_patch"],
            "minor": auto_flags["increment_minor"],
            "major": auto_flags["increment_major"],
        }

        paths = dict(default_project["paths"])
        if isinstance(data.get("paths"), dict):
            paths.update(data["paths"])
        paths.update({
            "mainExecutable": config.get("main_exe", ""),
            "installIcon": config.get("install_icon", ""),
            "sourceDir": config.get("source_dir", ""),
            "installDir": config.get("install_dir", default_project["config"]["install_dir"]),
            "outputDir": config.get("output_dir", default_project["config"]["output_dir"]),
        })
        data["paths"] = paths

        shortcuts = dict(default_project["shortcuts"])
        if isinstance(data.get("shortcuts"), dict):
            shortcuts.update(data["shortcuts"])
        shortcuts["desktop"] = bool(config.get("desktop_shortcut", shortcuts["desktop"]))
        shortcuts["startMenu"] = bool(config.get("start_menu_shortcut", shortcuts["startMenu"]))
        shortcuts["uninstaller"] = bool(config.get("uninstaller", shortcuts["uninstaller"]))
        data["shortcuts"] = shortcuts

        config["main_exe"] = str(paths.get("mainExecutable", "") or "")
        config["install_icon"] = str(paths.get("installIcon", "") or "")
        config["source_dir"] = str(paths.get("sourceDir", "") or "")
        config["install_dir"] = str(paths.get("installDir", "") or default_project["config"]["install_dir"])
        config["output_dir"] = str(paths.get("outputDir", "") or default_project["config"]["output_dir"])
        config["desktop_shortcut"] = bool(shortcuts.get("desktop", True))
        config["start_menu_shortcut"] = bool(shortcuts.get("startMenu", True))
        config["uninstaller"] = bool(shortcuts.get("uninstaller", True))
        data["config"] = config

        if not isinstance(data.get("files"), list):
            data["files"] = []
        if not isinstance(data.get("build_log"), list):
            data["build_log"] = []

        build = {
            "simulated": True,
            "count": int(data.get("build_count") or 0),
            "lastBuildAt": data.get("last_build"),
        }
        if isinstance(data.get("build"), dict):
            build.update(data["build"])
        build["count"] = int(build.get("count") or 0)
        data["build"] = build
        data["build_count"] = build["count"]
        data["last_build"] = build.get("lastBuildAt")

        if path is not None:
            normalized_path = self._ensure_project_extension(path.resolve())
            data["path"] = str(normalized_path)
            data["projectPath"] = str(normalized_path)
        else:
            existing_path = data.get("path") or data.get("projectPath") or ""
            if existing_path:
                data["path"] = str(self._ensure_project_extension(Path(existing_path)))
                data["projectPath"] = data["path"]
            else:
                data["path"] = ""
                data["projectPath"] = ""

        data["versionString"] = normalized_version
        return data

    def _save_project(self, project: Dict[str, Any]) -> bool:
        path_str = project.get("path") or project.get("projectPath")
        if not path_str:
            return False
        path = self._ensure_project_extension(Path(path_str))
        now = datetime.now().isoformat()

        project["updatedAt"] = now
        project["modified"] = now
        project["projectPath"] = str(path)
        project["path"] = str(path)
        project["schemaVersion"] = self.SCHEMA_VERSION
        project["projectName"] = project.get("projectName") or project.get("name") or "未命名项目"
        project["name"] = project["projectName"]

        normalized = self._normalize_project(project, path=path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
        project.clear()
        project.update(normalized)
        return True

    def create_project(self, name: str, path: Optional[str] = None) -> Dict[str, Any]:
        project = self._default_project_data(name)
        if path:
            save_path = self._ensure_project_extension(Path(path))
        else:
            safe_name = self._safe_filename(project["projectName"])
            save_path = self.projects_dir / f"{safe_name}{self.PROJECT_EXTENSION}"

        project = self._normalize_project(project, path=save_path)
        self._save_project(project)
        self._add_recent_project(project)
        return project

    def save_project(self, project: Dict[str, Any]) -> bool:
        result = self._save_project(project)
        if result:
            self._update_recent_project(project)
        return result

    def save_project_as(self, project: Dict[str, Any], new_path: str) -> Dict[str, Any]:
        path = self._ensure_project_extension(Path(new_path))
        now = datetime.now().isoformat()
        project = self._normalize_project(dict(project), path=path)
        project["id"] = str(uuid.uuid4())[:8]
        project["createdAt"] = now
        project["created"] = now
        self._save_project(project)
        self._add_recent_project(project)
        return project

    def load_project(self, path: str) -> Optional[Dict[str, Any]]:
        target = self._ensure_project_extension(Path(path))
        if not target.exists():
            return None
        try:
            with target.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            project = self._normalize_project(raw, path=target)
            self._save_project(project)
            self._add_recent_project(project)
            self.config["last_project"] = str(target)
            self._save_config()
            return project
        except (json.JSONDecodeError, OSError):
            return None

    def load_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        for path in self.projects_dir.glob(f"*{self.PROJECT_EXTENSION}"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("id") == project_id:
                    return self.load_project(str(path))
            except (json.JSONDecodeError, OSError):
                continue
        return None

    def _build_project_list_item(self, path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_project(data, path=path)
        app_version = normalized.get("config", {}).get("app_version", "1.0.0")
        return {
            "id": normalized.get("id"),
            "name": normalized.get("projectName"),
            "projectName": normalized.get("projectName"),
            "path": str(path),
            "projectPath": str(path),
            "modified": normalized.get("modified"),
            "updatedAt": normalized.get("updatedAt"),
            "version": app_version,
            "appVersion": app_version,
        }

    def list_projects(self) -> List[Dict[str, Any]]:
        projects: List[Dict[str, Any]] = []
        for path in self.projects_dir.glob(f"*{self.PROJECT_EXTENSION}"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                projects.append(self._build_project_list_item(path, data))
            except (json.JSONDecodeError, OSError):
                continue
        projects.sort(key=lambda x: x.get("modified") or "", reverse=True)
        return projects

    def delete_project(self, path: str) -> bool:
        target = self._ensure_project_extension(Path(path))
        if target.exists():
            target.unlink()
            self._remove_recent_project(str(target))
            return True
        return False

    def _sanitize_recent(self):
        recent = self.config.get("recent_projects", [])
        cleaned = []
        seen = set()
        for item in recent:
            path = str(item.get("path") or "").strip()
            if not path:
                continue
            norm = str(self._ensure_project_extension(Path(path)))
            if norm in seen:
                continue
            seen.add(norm)
            if Path(norm).exists():
                cleaned.append({
                    "id": item.get("id"),
                    "name": item.get("name") or Path(norm).stem,
                    "path": norm,
                    "modified": item.get("modified") or datetime.now().isoformat(),
                })
        self.config["recent_projects"] = cleaned[:self.MAX_RECENT_PROJECTS]
        self._save_config()

    def get_recent_projects(self) -> List[Dict[str, Any]]:
        self._sanitize_recent()
        return self.config.get("recent_projects", [])[:self.MAX_RECENT_PROJECTS]

    def _add_recent_project(self, project: Dict[str, Any]):
        path = str(project.get("path") or project.get("projectPath") or "").strip()
        if not path:
            return
        normalized_path = str(self._ensure_project_extension(Path(path)))
        recent = self.config.get("recent_projects", [])
        recent = [item for item in recent if str(item.get("path")) != normalized_path]
        recent.insert(0, {
            "id": project.get("id"),
            "name": project.get("projectName") or project.get("name") or Path(normalized_path).stem,
            "path": normalized_path,
            "modified": project.get("modified") or project.get("updatedAt") or datetime.now().isoformat(),
        })
        self.config["recent_projects"] = recent[:self.MAX_RECENT_PROJECTS]
        self.config["last_project"] = normalized_path
        self._save_config()

    def _update_recent_project(self, project: Dict[str, Any]):
        path = str(project.get("path") or project.get("projectPath") or "").strip()
        if not path:
            return
        normalized_path = str(self._ensure_project_extension(Path(path)))
        recent = self.config.get("recent_projects", [])
        updated = False
        for item in recent:
            if str(item.get("path")) == normalized_path:
                item["name"] = project.get("projectName") or project.get("name") or item.get("name")
                item["modified"] = project.get("modified") or project.get("updatedAt") or datetime.now().isoformat()
                updated = True
                break
        if not updated:
            self._add_recent_project(project)
            return
        self.config["recent_projects"] = recent[:self.MAX_RECENT_PROJECTS]
        self._save_config()

    def _remove_recent_project(self, path: str):
        normalized_path = str(self._ensure_project_extension(Path(path)))
        recent = self.config.get("recent_projects", [])
        recent = [item for item in recent if str(item.get("path")) != normalized_path]
        self.config["recent_projects"] = recent
        self._save_config()

    def clear_recent_projects(self):
        self.config["recent_projects"] = []
        self._save_config()

    def get_project_filter(self) -> str:
        return f"安装项目 (*{self.PROJECT_EXTENSION})|*{self.PROJECT_EXTENSION}"
