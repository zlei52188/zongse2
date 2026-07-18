from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from browndust2_manager.models.emulator import Emulator
from browndust2_manager.services.root_service import RootService


class EmulatorManager:
    """Stores and refreshes the four supported emulator configurations."""

    def __init__(self, config_path: Path | None = None, root_service: RootService | None = None) -> None:
        self.config_path = config_path or Path.home() / ".browndust2_manager" / "emulators.json"
        self.root_service = root_service or RootService()
        self._emulators = self._load()

    def all(self) -> list[Emulator]:
        return list(self._emulators)

    def get(self, emulator_id: int) -> Emulator:
        for emulator in self._emulators:
            if emulator.id == emulator_id:
                return emulator
        raise ValueError("emulator_id 必须是 1~4")

    def save(self, emulators: list[Emulator]) -> None:
        if {item.id for item in emulators} != {1, 2, 3, 4}:
            raise ValueError("必须保存 1~4 号模拟器配置")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps([asdict(item) for item in emulators], ensure_ascii=False, indent=2), encoding="utf-8")
        self._emulators = sorted(emulators, key=lambda item: item.id)

    def refresh_status(self) -> list[Emulator]:
        refreshed = []
        for emulator in self._emulators:
            emulator.online = self.root_service.is_online(emulator.adb_serial)
            emulator.root_status = self.root_service.root_status(emulator.adb_serial) if emulator.online else "离线"
            emulator.android_version = self.root_service.android_version(emulator.adb_serial) if emulator.online else "未知"
            refreshed.append(emulator)
        self.save(refreshed)
        return refreshed

    def _load(self) -> list[Emulator]:
        if self.config_path.exists():
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            return [Emulator(**item) for item in data]
        return [Emulator(id=i, name=f"模拟器{i}", adb_serial=f"emulator-{5552 + (i - 1) * 2}", root_path=RootService.SHARED_PREFS) for i in range(1, 5)]
