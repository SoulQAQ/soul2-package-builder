"""
Installer Builder - GUI Entry Point (pywebview)
"""
import json
import os
import sys
import webview
from datetime import datetime
from pathlib import Path
from typing import Optional

from core import Core


class AppApi:
    def __init__(self):
        self._window: Optional[webview.Window] = None
        self.core = Core()

    def set_window(self, window: webview.Window):
        self._window = window

    def _response(self, success: bool, data=None, message: str = "") -> dict:
        return {"success": success, "data": data, "message": message}

    def _error(self, message: str) -> dict:
        return self._response(False, message=message)

    def _ok(self, data=None) -> dict:
        return self._response(True, data=data)

    # === Project API ===

    def create_project(self, name: str) -> dict:
        try:
            project = self.core.create_project(name)
            return self._ok(project)
        except Exception as e:
            return self._error(str(e))

    def save_project(self, project_json: str) -> dict:
        try:
            project = json.loads(project_json)
            self.core.save_project(project)
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    def load_project(self, project_id: str) -> dict:
        try:
            project = self.core.load_project(project_id)
            if project:
                return self._ok(project)
            return self._error("Project not found")
        except Exception as e:
            return self._error(str(e))

    def list_projects(self) -> dict:
        try:
            projects = self.core.list_projects()
            return self._ok(projects)
        except Exception as e:
            return self._error(str(e))

    def delete_project(self, project_id: str) -> dict:
        try:
            self.core.delete_project(project_id)
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    # === File API ===

    def scan_directory(self, directory: str) -> dict:
        try:
            result = self.core.scan_directory(directory)
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    def get_file_info(self, file_path: str) -> dict:
        try:
            info = self.core.get_file_info(file_path)
            return self._ok(info)
        except Exception as e:
            return self._error(str(e))

    def select_file(self, file_types: str = "All Files (*.*)") -> dict:
        try:
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG, file_types=(file_types,)
            )
            if result and len(result) > 0:
                return self._ok({"path": result[0]})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    def select_folder(self) -> dict:
        try:
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return self._ok({"path": result[0]})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    def select_multiple_files(self, file_types: str = "All Files (*.*)") -> dict:
        try:
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=True, file_types=(file_types,)
            )
            if result:
                return self._ok({"paths": result})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    # === Build API ===

    def build_installer(self, project_json: str) -> dict:
        try:
            project = json.loads(project_json)
            result = self.core.build_installer(project)
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    def validate_project(self, project_json: str) -> dict:
        try:
            project = json.loads(project_json)
            result = self.core.validate_project(project)
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    # === Config API ===

    def get_config(self) -> dict:
        try:
            return self._ok(self.core.config)
        except Exception as e:
            return self._error(str(e))

    # === Output API ===

    def list_outputs(self) -> dict:
        try:
            outputs = []
            output_dir = self.core.OUTPUT_DIR
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
            return self._ok(sorted(outputs, key=lambda x: x["modified"], reverse=True))
        except Exception as e:
            return self._error(str(e))

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    # === App API ===

    def get_app_info(self) -> dict:
        return self._ok({
            "name": "Installer Builder",
            "version": "1.0.0",
            "platform": sys.platform,
        })

    def open_external(self, url: str) -> dict:
        try:
            import webbrowser
            webbrowser.open(url)
            return self._ok()
        except Exception as e:
            return self._error(str(e))


def get_webui_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "webui" / "index.html"
    return Path(__file__).parent.parent / "webui" / "index.html"


def main():
    api = AppApi()
    webui_path = get_webui_path()

    window = webview.create_window(
        "Installer Builder",
        str(webui_path),
        js_api=api,
        width=1280,
        height=800,
        min_size=(1024, 600),
        resizable=True,
    )
    api.set_window(window)

    webview.start(debug=False)


if __name__ == "__main__":
    main()
