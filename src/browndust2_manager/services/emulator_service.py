from __future__ import annotations

import subprocess
from pathlib import Path

from browndust2_manager.models.emulator import Emulator


class EmulatorService:
    """无限模拟器管理与 ADB 发现服务。"""

    def __init__(self, adb_path: Path | str = "adb") -> None:
        self.adb_path = str(adb_path)
        self._emulators: dict[int, Emulator] = {}
        self._next_id = 1

    def add(self, emulator: Emulator) -> Emulator:
        """新增模拟器。"""
        emulator.id = self._next_id
        self._emulators[self._next_id] = emulator
        self._next_id += 1
        return emulator

    def update(self, emulator_id: int, emulator: Emulator) -> None:
        """修改模拟器。"""
        emulator.id = emulator_id
        self._emulators[emulator_id] = emulator

    def delete(self, emulator_id: int) -> None:
        """删除模拟器。"""
        self._emulators.pop(emulator_id, None)

    def list_all(self) -> list[Emulator]:
        """返回全部模拟器。"""
        return list(self._emulators.values())

    def test_connection(self, serial: str) -> bool:
        """测试 ADB 连接。"""
        result = subprocess.run([self.adb_path, "-s", serial, "get-state"], capture_output=True, text=True, timeout=10, check=False)
        return result.stdout.strip() == "device"

    def discover(self) -> list[Emulator]:
        """自动发现在线 ADB 设备。"""
        result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=10, check=False)
        devices: list[Emulator] = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(Emulator(None, parts[0], parts[0], 0, online=True))
        return devices
