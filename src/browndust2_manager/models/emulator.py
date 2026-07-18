from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Emulator:
    """模拟器配置与运行状态。"""

    id: int | None
    name: str
    adb_serial: str
    adb_port: int
    android_version: str = ""
    root: bool = False
    online: bool = False
    game_status: str = "未知"
    restore_count: int = 0
    last_restore_time: datetime | None = None
