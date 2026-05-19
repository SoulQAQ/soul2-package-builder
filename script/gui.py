"""
Installer Builder - GUI 入口 (pywebview)
"""
import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional, Any

import webview

from core import Core


def get_runtime_base_dir() -> Path:
    """应用根目录：开发态为项目根目录，打包态为 exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_bundle_base_dir() -> Path:
    """打包资源目录（PyInstaller _MEIPASS）或应用根目录。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return get_runtime_base_dir()


def resolve_resource_path(*parts: str) -> Path:
    """
    统一资源路径解析，兼容开发态和 PyInstaller 打包态。
    优先 _MEIPASS，其次 exe 目录。
    """
    bundle_path = get_bundle_base_dir().joinpath(*parts)
    if bundle_path.exists():
        return bundle_path
    runtime_path = get_runtime_base_dir().joinpath(*parts)
    return runtime_path


def get_icon_path() -> Optional[Path]:
    """获取应用自身图标路径（app.ico）。"""
    candidate = resolve_resource_path("app.ico")
    if candidate.exists():
        return candidate
    return None


def get_webui_path() -> Path:
    return resolve_resource_path("webui", "index.html")


class AppApi:
    """前端 API 桥接。"""

    def __init__(self):
        self._window: Optional[Any] = None
        self.core = Core()

    def set_window(self, window: Any):
        self._window = window

    def _response(self, success: bool, data: Any = None, message: str = "") -> dict:
        return {"success": success, "data": data, "message": message}

    def _ok(self, data: Any = None, message: str = "") -> dict:
        return self._response(True, data=data, message=message)

    def _error(self, message: str, data: Any = None) -> dict:
        return self._response(False, data=data, message=message)

    # === 项目 API ===
    def create_project(self, name: str) -> dict:
        try:
            project = self.core.create_project(name)
            return self._ok(project, "项目已创建")
        except Exception as e:
            return self._error(str(e))

    def save_project(self, project_json: Optional[str] = None) -> dict:
        try:
            if project_json:
                self.core.current_project = json.loads(project_json)
            saved = self.core.save_project()
            if not saved:
                return self._error("保存失败：当前没有可保存的项目")
            return self._ok(self.core.current_project, "已保存")
        except Exception as e:
            return self._error(str(e))

    def save_project_as(self, path: str) -> dict:
        try:
            project = self.core.save_project_as(path)
            return self._ok(project, "已另存为")
        except Exception as e:
            return self._error(str(e))

    def load_project(self, path_or_id: str) -> dict:
        try:
            project = self.core.load_project(path_or_id)
            if not project:
                project = self.core.load_project_by_id(path_or_id)
            if not project:
                return self._error("项目未找到")
            return self._ok(project, "项目已加载")
        except Exception as e:
            return self._error(str(e))

    def list_projects(self) -> dict:
        try:
            return self._ok(self.core.list_projects())
        except Exception as e:
            return self._error(str(e))

    def get_recent_projects(self) -> dict:
        try:
            return self._ok(self.core.get_recent_projects())
        except Exception as e:
            return self._error(str(e))

    def remove_recent_project(self, path: str) -> dict:
        try:
            self.core.project_manager._remove_recent_project(path)
            return self._ok(None, "最近项目已移除")
        except Exception as e:
            return self._error(str(e))

    def delete_project(self, path: str) -> dict:
        try:
            self.core.delete_project(path)
            return self._ok(None, "项目已删除")
        except Exception as e:
            return self._error(str(e))

    def close_project(self) -> dict:
        try:
            self.core.close_project()
            return self._ok(None, "项目已关闭")
        except Exception as e:
            return self._error(str(e))

    def get_current_project(self) -> dict:
        return self._ok(self.core.current_project)

    def update_project_config(self, config_json: str) -> dict:
        try:
            if not self.core.current_project:
                return self._error("没有当前项目")
            config = json.loads(config_json)
            current_config = self.core.current_project.setdefault("config", {})
            current_config.update(config)
            self.core.save_project()
            return self._ok(self.core.current_project, "项目配置已更新")
        except Exception as e:
            return self._error(str(e))

    # === 版本 API ===
    def get_version_info(self) -> dict:
        try:
            return self._ok(self.core.get_version_info())
        except Exception as e:
            return self._error(str(e))

    def set_version(self, version: str) -> dict:
        try:
            ok = self.core.set_version(version)
            if not ok:
                return self._error("版本号格式无效，请使用 a.b.c")
            self.core.save_project()
            return self._ok(self.core.get_version_info(), "版本号已更新")
        except Exception as e:
            return self._error(str(e))

    def set_auto_version(self, patch: bool = False, minor: bool = False, major: bool = False) -> dict:
        try:
            result = self.core.set_auto_version_config(patch, minor, major)
            return self._ok(result, "自动版本规则已更新")
        except Exception as e:
            return self._error(str(e))

    # === 文件 API ===
    def scan_directory(self, directory: str) -> dict:
        try:
            return self._ok(self.core.scan_directory(directory))
        except Exception as e:
            return self._error(str(e))

    def get_file_info(self, file_path: str) -> dict:
        try:
            return self._ok(self.core.get_file_info(file_path))
        except Exception as e:
            return self._error(str(e))

    def _ensure_window(self):
        if self._window is None:
            raise RuntimeError("窗口尚未初始化")

    def select_file(self, file_types: str = "所有文件 (*.*)") -> dict:
        try:
            self._ensure_window()
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=(file_types,))
            if result and len(result) > 0:
                return self._ok({"path": str(result[0])})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    def select_folder(self) -> dict:
        try:
            self._ensure_window()
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return self._ok({"path": str(result[0])})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    def select_save_file(self, default_name: str = "", file_types: str = "安装项目 (*.ssc)") -> dict:
        try:
            self._ensure_window()
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=(file_types,),
            )
            if not result:
                return self._ok(None)
            if isinstance(result, (list, tuple)):
                path = str(result[0]) if result else ""
            else:
                path = str(result)
            if not path:
                return self._ok(None)
            return self._ok({"path": path})
        except Exception as e:
            return self._error(str(e))

    def select_open_file(self, file_types: str = "安装项目 (*.ssc)") -> dict:
        try:
            self._ensure_window()
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=(file_types,))
            if result and len(result) > 0:
                return self._ok({"path": str(result[0])})
            return self._ok(None)
        except Exception as e:
            return self._error(str(e))

    # === 构建 API ===
    def validate_project(self, project_json: Optional[str] = None) -> dict:
        try:
            if project_json:
                project = json.loads(project_json)
                return self._ok(self.core.validate_project(project))
            return self._ok(self.core.validate_project())
        except Exception as e:
            return self._error(str(e))

    def build_installer(self) -> dict:
        try:
            if not self.core.current_project:
                return self._error("没有当前项目")
            self.core.save_project()
            result = self.core.build()
            return self._ok(result)
        except Exception as e:
            return self._error(str(e))

    # === 输出 API ===
    def list_outputs(self) -> dict:
        try:
            return self._ok(self.core.list_outputs())
        except Exception as e:
            return self._error(str(e))

    def open_output_folder(self) -> dict:
        try:
            output_dir = Path(self.core.current_project.get("config", {}).get("output_dir", "")) if self.core.current_project else None
            target = output_dir if output_dir and str(output_dir).strip() else (get_runtime_base_dir() / "output")
            target = Path(target)
            target.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["explorer", str(target)])
            return self._ok({"path": str(target)})
        except Exception as e:
            return self._error(str(e))

    # === 应用 API ===
    def get_app_info(self) -> dict:
        icon_path = get_icon_path()
        return self._ok(
            {
                "name": "安装包生成器",
                "name_en": "Installer Builder",
                "version": "1.0.0",
                "platform": sys.platform,
                "base_dir": str(get_runtime_base_dir()),
                "icon_path": str(icon_path) if icon_path else "",
                "simulated_build": True,
            }
        )

    def get_config(self) -> dict:
        try:
            return self._ok(self.core.get_config())
        except Exception as e:
            return self._error(str(e))

    def open_external(self, url: str) -> dict:
        try:
            webbrowser.open(url)
            return self._ok()
        except Exception as e:
            return self._error(str(e))


def create_main_window(api: AppApi) -> Any:
    webui_path = get_webui_path()
    icon_path = get_icon_path()

    # 部分 pywebview 5.x 后端对 create_window 的 icon 支持不一致，因此这里使用 try 兼容。
    window_kwargs = {
        "title": "安装包生成器",
        "url": str(webui_path),
        "js_api": api,
        "width": 1366,
        "height": 860,
        "min_size": (1120, 680),
        "resizable": True,
    }
    if icon_path:
        window_kwargs["icon"] = str(icon_path)

    try:
        window = webview.create_window(**window_kwargs)
    except TypeError:
        window_kwargs.pop("icon", None)
        window = webview.create_window(**window_kwargs)
    return window


def main():
    api = AppApi()
    icon_path = get_icon_path()
    window = create_main_window(api)
    api.set_window(window)

    start_kwargs = {"debug": False}
    if icon_path:
        # 对支持该参数的后端继续传入，确保打包/运行态尽量一致。
        start_kwargs["icon"] = str(icon_path)

    try:
        webview.start(**start_kwargs)
    except TypeError:
        start_kwargs.pop("icon", None)
        webview.start(**start_kwargs)


if __name__ == "__main__":
    main()
