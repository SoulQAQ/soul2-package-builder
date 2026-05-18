"""
Installer Builder - 构建清单
负责收集和描述所有需要打包的文件和配置
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class Manifest:
    """构建清单，描述安装包的所有内容"""

    def __init__(self):
        self.app_name = ""
        self.app_version = "1.0.0"
        self.publisher = ""
        self.main_exe = ""
        self.install_dir = ""
        self.output_dir = ""
        self.install_icon = ""
        self.source_dir = ""
        self.uninstaller = True
        self.desktop_shortcut = True
        self.start_menu_shortcut = True
        self.files: List[Dict] = []
        self.shortcuts: List[Dict] = []
        self.registry_entries: List[Dict] = []
        self.environment_vars: List[Dict] = []
        self.created = datetime.now().isoformat()

    @classmethod
    def from_project(cls, project: dict) -> "Manifest":
        """从项目配置创建清单"""
        manifest = cls()
        config = project.get("config", {})

        manifest.app_name = config.get("app_name", "")
        manifest.app_version = config.get("app_version", "1.0.0")
        manifest.publisher = config.get("publisher", "")
        manifest.main_exe = config.get("main_exe", "")
        manifest.install_dir = config.get("install_dir", "")
        manifest.output_dir = config.get("output_dir", "")
        manifest.install_icon = config.get("install_icon", "")
        manifest.source_dir = config.get("source_dir", "")
        manifest.uninstaller = config.get("uninstaller", True)
        manifest.desktop_shortcut = config.get("desktop_shortcut", True)
        manifest.start_menu_shortcut = config.get("start_menu_shortcut", True)
        manifest.files = project.get("files", [])

        # 生成快捷方式配置
        manifest._generate_shortcuts()

        return manifest

    def _generate_shortcuts(self):
        """生成快捷方式配置"""
        self.shortcuts = []

        if self.desktop_shortcut and self.main_exe:
            self.shortcuts.append({
                "name": self.app_name,
                "target": "$INSTDIR\\" + Path(self.main_exe).name,
                "location": "desktop",
                "working_dir": "$INSTDIR",
            })

        if self.start_menu_shortcut and self.main_exe:
            self.shortcuts.append({
                "name": self.app_name,
                "target": "$INSTDIR\\" + Path(self.main_exe).name,
                "location": "start_menu",
                "working_dir": "$INSTDIR",
            })

    def add_file(self, source: str, dest: str, size: int = 0):
        """添加文件到清单"""
        self.files.append({
            "source": source,
            "dest": dest,
            "size": size,
        })

    def validate(self) -> tuple:
        """验证清单完整性"""
        errors = []
        warnings = []

        if not self.app_name:
            errors.append("应用名称不能为空")

        if not self.main_exe:
            errors.append("主程序不能为空")

        if not self.install_dir:
            warnings.append("未设置安装目录，将使用默认目录")

        if not self.output_dir:
            warnings.append("未设置输出目录，将使用默认目录")

        return len(errors) == 0, errors, warnings

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "publisher": self.publisher,
            "main_exe": self.main_exe,
            "install_dir": self.install_dir,
            "output_dir": self.output_dir,
            "install_icon": self.install_icon,
            "source_dir": self.source_dir,
            "uninstaller": self.uninstaller,
            "desktop_shortcut": self.desktop_shortcut,
            "start_menu_shortcut": self.start_menu_shortcut,
            "files": self.files,
            "shortcuts": self.shortcuts,
            "registry_entries": self.registry_entries,
            "environment_vars": self.environment_vars,
            "created": self.created,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def save(self, path: str):
        """保存清单到文件"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
