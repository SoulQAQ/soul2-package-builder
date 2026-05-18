"""
Installer Builder - Core Business Logic
"""
import json
import os
import sys
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).parent
    return Path(__file__).parent.parent


class Core:
    def __init__(self):
        self.BASE_DIR = get_base_dir()
        self.DATA_DIR = self.BASE_DIR / "data"
        self.PROJECTS_DIR = self.DATA_DIR / "projects"
        self.CONFIG_FILE = self.DATA_DIR / "config.json"
        self.OUTPUT_DIR = self.BASE_DIR / "output"
        self._ensure_dirs()
        self.config = self._load_config()

    def _ensure_dirs(self):
        self.DATA_DIR.mkdir(exist_ok=True)
        self.PROJECTS_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"recent_projects": [], "last_output_dir": ""}

    def _save_config(self):
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def create_project(self, name: str) -> dict:
        project_id = str(uuid.uuid4())[:8]
        project = {
            "id": project_id,
            "name": name,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "config": {
                "app_name": "",
                "app_version": "1.0.0",
                "publisher": "",
                "main_exe": "",
                "install_dir": "%ProgramFiles%\\AppName",
                "output_dir": "",
                "install_icon": "",
                "uninstaller": True,
                "desktop_shortcut": True,
                "start_menu_shortcut": True,
            },
            "files": [],
            "build_log": [],
        }

        project_file = self.PROJECTS_DIR / f"{project_id}.json"
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)

        self._add_recent_project(project_id, name)
        return project

    def save_project(self, project: dict) -> bool:
        project["modified"] = datetime.now().isoformat()
        project_file = self.PROJECTS_DIR / f"{project['id']}.json"
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
        return True

    def load_project(self, project_id: str) -> Optional[dict]:
        project_file = self.PROJECTS_DIR / f"{project_id}.json"
        if project_file.exists():
            with open(project_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_projects(self) -> list:
        projects = []
        for f in self.PROJECTS_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    projects.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "modified": data.get("modified"),
                    })
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(projects, key=lambda x: x.get("modified", ""), reverse=True)

    def delete_project(self, project_id: str) -> bool:
        project_file = self.PROJECTS_DIR / f"{project_id}.json"
        if project_file.exists():
            project_file.unlink()
            return True
        return False

    def _add_recent_project(self, project_id: str, name: str):
        recent = self.config.get("recent_projects", [])
        recent = [p for p in recent if p.get("id") != project_id]
        recent.insert(0, {"id": project_id, "name": name})
        self.config["recent_projects"] = recent[:10]
        self._save_config()

    def scan_directory(self, directory: str) -> dict:
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
                file_info = {
                    "path": str(rel_path),
                    "size": size,
                    "size_formatted": self._format_size(size),
                }
                files.append(file_info)
                if f.suffix.lower() == ".exe":
                    exe_files.append(str(rel_path))

        return {
            "files": files,
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size),
            "exe_files": exe_files,
            "file_count": len(files),
        }

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def build_installer(self, project: dict) -> dict:
        config = project.get("config", {})
        app_name = config.get("app_name", "setup").strip()
        if not app_name:
            app_name = "setup"

        safe_name = "".join(c for c in app_name if c.isalnum() or c in " -_").strip()
        output_filename = f"{safe_name}_setup.exe"
        output_path = self.OUTPUT_DIR / output_filename

        timestamp = datetime.now().isoformat()
        log = [
            {"time": timestamp, "level": "info", "message": "Build started"},
            {"time": timestamp, "level": "info", "message": f"Application: {app_name}"},
            {"time": timestamp, "level": "info", "message": f"Version: {config.get('app_version', '1.0.0')}"},
            {"time": timestamp, "level": "info", "message": f"Publisher: {config.get('publisher', 'Unknown')}"},
        ]

        # Write a stub executable (just a marker file for MVP)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Installer Builder - Stub Output\n")
            f.write(f"App: {app_name}\n")
            f.write(f"Version: {config.get('app_version', '1.0.0')}\n")
            f.write(f"Built: {timestamp}\n")

        log.append({"time": timestamp, "level": "success", "message": f"Output: {output_path}"})

        project["build_log"] = log
        project["last_build"] = timestamp
        project["output_file"] = str(output_path)
        self.save_project(project)

        return {
            "success": True,
            "log": log,
            "output_file": str(output_path),
            "message": "Build completed successfully (simulation)",
        }

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

    def validate_project(self, project: dict) -> dict:
        errors = []
        warnings = []
        config = project.get("config", {})

        if not config.get("app_name"):
            errors.append("Application name is required")
        if not config.get("app_version"):
            warnings.append("Version is recommended")
        if not config.get("main_exe"):
            errors.append("Main executable is required")
        if not config.get("output_dir"):
            warnings.append("Output directory not set, using default")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
