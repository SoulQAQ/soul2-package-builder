"""
Installer Builder - 版本号管理器
负责版本号解析、校验和自动推进
"""
import re
from typing import Tuple, Dict


class VersionManager:
    """版本号管理器，使用 a.b.c 三段非负整数格式。"""

    VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

    @staticmethod
    def parse(version: str) -> Tuple[int, int, int]:
        """解析版本号，非法值回退到 1.0.0。"""
        value = str(version or "").strip()
        match = VersionManager.VERSION_PATTERN.match(value)
        if not match:
            return 1, 0, 0
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        return max(0, major), max(0, minor), max(0, patch)

    @staticmethod
    def format(major: int, minor: int, patch: int) -> str:
        """格式化为 a.b.c。"""
        return f"{max(0, int(major))}.{max(0, int(minor))}.{max(0, int(patch))}"

    @staticmethod
    def validate(version: str) -> bool:
        """校验版本号格式是否为 a.b.c 且全为非负整数。"""
        value = str(version or "").strip()
        return bool(VersionManager.VERSION_PATTERN.fullmatch(value))

    @staticmethod
    def normalize(version: str) -> str:
        """把输入标准化为合法版本号字符串。"""
        if VersionManager.validate(version):
            major, minor, patch = VersionManager.parse(version)
            return VersionManager.format(major, minor, patch)
        return "1.0.0"

    @staticmethod
    def normalize_auto_flags(
        increment_patch: bool = False,
        increment_minor: bool = False,
        increment_major: bool = False,
    ) -> Dict[str, bool]:
        """
        规范自动版本规则，优先级 major > minor > patch。
        """
        major = bool(increment_major)
        minor = bool(increment_minor)
        patch = bool(increment_patch)

        if major:
            return {
                "increment_patch": False,
                "increment_minor": False,
                "increment_major": True,
            }
        if minor:
            return {
                "increment_patch": False,
                "increment_minor": True,
                "increment_major": False,
            }
        return {
            "increment_patch": patch,
            "increment_minor": False,
            "increment_major": False,
        }

    @staticmethod
    def next_version_with_strategy(
        version: str,
        increment_patch: bool = False,
        increment_minor: bool = False,
        increment_major: bool = False,
    ) -> Dict[str, object]:
        """
        计算下一版本并返回策略说明：
        - major: major+1, minor=0, patch=0，且自动取消 major/minor/patch
        - minor: minor+1, patch=0，且自动取消 minor/patch
        - patch: patch+1，patch 保留勾选
        - none: 不变化
        """
        major, minor, patch = VersionManager.parse(version)
        flags = VersionManager.normalize_auto_flags(
            increment_patch=increment_patch,
            increment_minor=increment_minor,
            increment_major=increment_major,
        )

        strategy = "none"
        new_major = major
        new_minor = minor
        new_patch = patch
        next_flags = dict(flags)

        if flags["increment_major"]:
            strategy = "major"
            new_major = major + 1
            new_minor = 0
            new_patch = 0
            next_flags = {
                "increment_patch": False,
                "increment_minor": False,
                "increment_major": False,
            }
        elif flags["increment_minor"]:
            strategy = "minor"
            new_minor = minor + 1
            new_patch = 0
            next_flags = {
                "increment_patch": False,
                "increment_minor": False,
                "increment_major": False,
            }
        elif flags["increment_patch"]:
            strategy = "patch"
            new_patch = patch + 1
            next_flags = {
                "increment_patch": True,
                "increment_minor": False,
                "increment_major": False,
            }

        current_version = VersionManager.format(major, minor, patch)
        new_version = VersionManager.format(new_major, new_minor, new_patch)
        changed = current_version != new_version
        return {
            "strategy": strategy,
            "changed": changed,
            "old_version": current_version,
            "new_version": new_version,
            "next_auto_version": next_flags,
            "normalized_auto_version": flags,
        }

    @staticmethod
    def get_version_info(version: str) -> dict:
        """返回版本信息。"""
        normalized = VersionManager.normalize(version)
        major, minor, patch = VersionManager.parse(normalized)
        return {
            "version": normalized,
            "major": major,
            "minor": minor,
            "patch": patch,
            "display": f"v{normalized}",
        }
