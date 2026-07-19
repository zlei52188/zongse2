from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态。"""

    PENDING = "等待中"
    RUNNING = "运行中"
    PAUSED = "已暂停"
    STOPPED = "已停止"
    DONE = "已完成"
    FAILED = "失败"


@dataclass(slots=True)
class RestoreTask:
    """恢复任务记录。"""

    id: int
    account_id: int
    emulator_id: int
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    elapsed_seconds: float = 0.0
    created_at: datetime | None = None
