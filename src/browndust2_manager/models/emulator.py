from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Emulator:
    """Configured emulator target."""

    id: int
    name: str
    adb_serial: str
    root_path: str
    android_version: str = "未知"
    root_status: str = "未知"
    online: bool = False
