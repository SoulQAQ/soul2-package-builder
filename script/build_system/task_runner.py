"""
Installer Builder - 任务运行器
负责执行构建过程中的各个步骤
"""
import time
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task:
    """单个构建任务"""

    def __init__(self, name: str, action: Callable, description: str = ""):
        self.name = name
        self.action = action
        self.description = description or name
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.duration: float = 0
        self.log: List[str] = []

    def run(self) -> bool:
        """执行任务"""
        self.status = TaskStatus.RUNNING
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 开始执行: {self.name}")

        start_time = time.time()
        try:
            self.result = self.action()
            self.status = TaskStatus.COMPLETED
            self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 完成: {self.name}")
            return True
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 失败: {e}")
            return False
        finally:
            self.duration = time.time() - start_time


class TaskRunner:
    """任务运行器，管理构建任务的执行"""

    def __init__(self):
        self.tasks: List[Task] = []
        self.current_task: Optional[Task] = None
        self.log: List[str] = []
        self.on_progress: Optional[Callable[[int, int, str], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None

    def add_task(self, name: str, action: Callable, description: str = ""):
        """添加任务"""
        task = Task(name, action, description)
        self.tasks.append(task)

    def clear(self):
        """清空任务列表"""
        self.tasks.clear()
        self.log.clear()

    def run_all(self) -> bool:
        """执行所有任务"""
        total = len(self.tasks)
        completed = 0

        for i, task in enumerate(self.tasks):
            self.current_task = task

            if self.on_progress:
                self.on_progress(i, total, task.description)

            success = task.run()

            # 记录日志
            for line in task.log:
                self.log.append(line)
                if self.on_log:
                    self.on_log(line)

            if success:
                completed += 1
            else:
                # 任务失败，停止执行
                if self.on_progress:
                    self.on_progress(total, total, f"失败: {task.name}")
                return False

        if self.on_progress:
            self.on_progress(total, total, "完成")

        return True

    def run_until_failed(self) -> bool:
        """执行任务直到失败"""
        return self.run_all()

    def get_summary(self) -> Dict:
        """获取执行摘要"""
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED)

        return {
            "total": len(self.tasks),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "success": failed == 0,
            "duration": sum(t.duration for t in self.tasks),
        }
