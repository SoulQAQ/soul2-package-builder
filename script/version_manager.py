"""
Installer Builder - 版本号管理器
负责版本号的解析、递增、格式化等
"""
import re
from typing import Tuple, Optional


class VersionManager:
    """版本号管理器，支持 a.b.c 格式"""

    VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

    @staticmethod
    def parse(version: str) -> Tuple[int, int, int]:
        """解析版本号，返回 (major, minor, patch)"""
        match = VersionManager.VERSION_PATTERN.match(version.strip())
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return 1, 0, 0

    @staticmethod
    def format(major: int, minor: int, patch: int) -> str:
        """格式化版本号"""
        return f"{major}.{minor}.{patch}"

    @staticmethod
    def increment_patch(version: str) -> str:
        """修订版本 +1"""
        major, minor, patch = VersionManager.parse(version)
        return VersionManager.format(major, minor, patch + 1)

    @staticmethod
    def increment_minor(version: str) -> str:
        """次版本 +1，修订版本归零"""
        major, minor, _ = VersionManager.parse(version)
        return VersionManager.format(major, minor + 1, 0)

    @staticmethod
    def increment_major(version: str) -> str:
        """主版本 +1，次版本和修订版本归零"""
        major, _, _ = VersionManager.parse(version)
        return VersionManager.format(major + 1, 0, 0)

    @staticmethod
    def auto_increment(version: str, increment_patch: bool = False,
                        increment_minor: bool = False,
                        increment_major: bool = False) -> str:
        """
        自动递增版本号
        优先级：主版本 > 次版本 > 修订版本
        """
        if increment_major:
            return VersionManager.increment_major(version)
        elif increment_minor:
            return VersionManager.increment_minor(version)
        elif increment_patch:
            return VersionManager.increment_patch(version)
        return version

    @staticmethod
    def validate(version: str) -> bool:
        """验证版本号格式"""
        return bool(VersionManager.VERSION_PATTERN.match(version.strip()))

    @staticmethod
    def compare(v1: str, v2: str) -> int:
        """
        比较两个版本号
        返回：-1 (v1 < v2), 0 (v1 == v2), 1 (v1 > v2)
        """
        a1, b1, c1 = VersionManager.parse(v1)
        a2, b2, c2 = VersionManager.parse(v2)

        if a1 < a2:
            return -1
        elif a1 > a2:
            return 1

        if b1 < b2:
            return -1
        elif b1 > b2:
            return 1

        if c1 < c2:
            return -1
        elif c1 > c2:
            return 1

        return 0

    @staticmethod
    def get_version_info(version: str) -> dict:
        """获取版本号详细信息"""
        major, minor, patch = VersionManager.parse(version)
        return {
            "version": version,
            "major": major,
            "minor": minor,
            "patch": patch,
            "display": f"v{version}",
        }
