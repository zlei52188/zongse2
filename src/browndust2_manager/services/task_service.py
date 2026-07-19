from __future__ import annotations

import time
from collections.abc import Callable

from browndust2_manager.models.task import RestoreTask, TaskStatus


class TaskService:
    """恢复任务队列业务服务。"""

    def __init__(self) -> None:
        self._tasks: dict[int, RestoreTask] = {}
        self._next_id = 1

    def create_restore_task(self, account_id: int, emulator_id: int) -> RestoreTask:
        """新增恢复任务。"""
        task = RestoreTask(self._next_id, account_id, emulator_id)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def start(self, task_id: int, runner: Callable[[RestoreTask], None]) -> None:
        """开始任务并记录进度和耗时。"""
        task = self._tasks[task_id]
        started = time.monotonic()
        task.status = TaskStatus.RUNNING
        task.progress = 10
        try:
            runner(task)
        except Exception:
            task.status = TaskStatus.FAILED
            raise
        finally:
            task.elapsed_seconds = time.monotonic() - started
        if task.status == TaskStatus.RUNNING:
            task.progress = 100
            task.status = TaskStatus.DONE

    def pause(self, task_id: int) -> None:
        """暂停任务。"""
        self._tasks[task_id].status = TaskStatus.PAUSED

    def resume(self, task_id: int) -> None:
        """继续任务。"""
        self._tasks[task_id].status = TaskStatus.RUNNING

    def stop(self, task_id: int) -> None:
        """停止任务。"""
        self._tasks[task_id].status = TaskStatus.STOPPED

    def delete(self, task_id: int) -> None:
        """删除任务。"""
        self._tasks.pop(task_id, None)

    def history(self) -> list[RestoreTask]:
        """返回恢复记录。"""
        return list(self._tasks.values())
