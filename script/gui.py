"""
Installer Builder - GUI 入口 (pywebview)
"""
import json
import sys
import webview
from datetime import datetime
from pathlib import Path
from typing import Optional

from core import Core


def get_base_dir() -> Path:
    """获取基础目录，兼容开发态和打包态"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).parent
    return Path(__file__).parent.parent


def get_icon_path() -> Optional[str]:
    """获取图标路径"""
    base = get_base_dir()
    icon_path = base / "app.ico"
    if icon_path.exists():
        return str(icon_path)
    return None


class AppApi:
    """前端 API 桥接"""

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

    # === 项目 API ===

    def create_project(self, name: str) -> dict:
        try:
            project = self.core.create_project(name)
            return self._ok(project)
        except Exception as e:
            return self._error(str(e))

    def save_project(self, project_json: str = None) -> dict:
        try:
            if project_json:
                project = json.loads(project_json)
                self.core.current_project = project
            self.core.save_project()
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    def save_project_as(self, path: str) -> dict:
        try:
            project = self.core.save_project_as(path)
            return self._ok(project)
        except Exception as e:
            return self._error(str(e))

    def load_project(self, path_or_id: str) -> dict:
        try:
            # 尝试作为路径加载
            project = self.core.load_project(path_or_id)
            if not project:
                # 尝试作为 ID 加载
                project = self.core.load_project_by_id(path_or_id)
            if project:
                return self._ok(project)
            return self._error("项目未找到")
        except Exception as e:
            return self._error(str(e))

    def list_projects(self) -> dict:
        try:
            projects = self.core.list_projects()
            return self._ok(projects)
        except Exception as e:
            return self._error(str(e))

    def get_recent_projects(self) -> dict:
        try:
            projects = self.core.get_recent_projects()
            return self._ok(projects)
        except Exception as e:
            return self._error(str(e))

    def delete_project(self, path: str) -> dict:
        try:
            self.core.delete_project(path)
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    def close_project(self) -> dict:
        try:
            self.core.close_project()
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    def get_current_project(self) -> dict:
        return self._ok(self.core.current_project)

    def update_project_config(self, config_json: str) -> dict:
        try:
            config = json.loads(config_json)
            if self.core.current_project:
                self.core.current_project["config"] = {
                    **self.core.current_project.get("config", {}),
                    **config
                }
                self.core.save_project()
            return self._ok(self.core.current_project)
        except Exception as e:
            return self._error(str(e))

    # === 版本 API ===

    def get_version_info(self) -> dict:
        try:
            info = self.core.get_version_info()
            return self._ok(info)
        except Exception as e:
            return self._error(str(e))

    def set_version(self, version: str) -> dict:
        try:
            self.core.set_version(version)
            self.core.save_project()
            return self._ok(self.core.get_version_info())
        except Exception as e:
            return self._error(str(e))

    def set_auto_version(self, patch: bool = False,
                          minor: bool = False,
                          major: bool = False) -> dict:
        try:
            result = self.core.set_auto_version_config(patch, minor, major)
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    # === 文件 API ===

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

    def select_file(self, file_types: str = "所有文件 (*.*)") -> dict:
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

    def select_save_file(self, default_name: str = "",
                         file_types: str = "安装项目 (*.ssc)") -> dict:
        try:
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=(file_types,)
            )
            if result:
                return self._ok({"path": result})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    def select_open_file(self, file_types: str = "安装项目 (*.ssc)") -> dict:
        try:
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG, file_types=(file_types,)
            )
            if result and len(result) > 0:
                return self._ok({"path": result[0]})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    # === 构建 API ===

    def build_installer(self) -> dict:
        try:
            # 先保存项目
            self.core.save_project()

            # 执行构建
            result = self.core.build()
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    def validate_project(self, project_json: str = None) -> dict:
        try:
            if project_json:
                project = json.loads(project_json)
                result = self.core.validate_project(project)
            else:
                result = self.core.validate_project()
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    # === 输出 API ===

    def list_outputs(self) -> dict:
        try:
            outputs = self.core.list_outputs()
            return self._ok(outputs)
        except Exception as e:
            return self._error(str(e))

    def open_output_folder(self) -> dict:
        try:
            import subprocess
            output_dir = get_base_dir() / "output"
            output_dir.mkdir(exist_ok=True)
            subprocess.run(["explorer", str(output_dir)])
            return self._ok()
        except Exception as e:
            return self._error(str(e))

    # === 应用 API ===

    def get_app_info(self) -> dict:
        return self._ok({
            "name": "安装包生成器",
            "name_en": "Installer Builder",
            "version": "1.0.0",
            "platform": sys.platform,
        })

    def get_config(self) -> dict:
        try:
            return self._ok(self.core.get_config())
        except Exception as e:
            return self._error(str(e))

    def open_external(self, url: str) -> dict:
        try:
            import webbrowser
            webbrowser.open(url)
            return self._ok()
        except Exception as e:
            return self._error(str(e))


def get_webui_path() -> Path:
    """获取 UI 文件路径"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "webui" / "index.html"
    return Path(__file__).parent.parent / "webui" / "index.html"


def main():
    api = AppApi()
    webui_path = get_webui_path()

    window = webview.create_window(
        "安装包生成器",
        str(webui_path),
        js_api=api,
        width=1280,
        height=800,
        min_size=(1024, 600),
        resizable=True,
    )
    api.set_window(window)

    # pywebview 6.x 使用 icon 参数在 start() 中设置
    webview.start(debug=False, icon="app.ico")


if __name__ == "__main__":
    main()
