from __future__ import annotations

from pathlib import Path

from browndust2_manager.models.emulator import Emulator
from browndust2_manager.services.emulator_manager import EmulatorManager
from browndust2_manager.services.recovery_engine import ProgressCallback, RecoveryEngine, RecoveryResult


class RestoreService:
    """Compatibility facade that delegates real restores to RecoveryEngine."""

    def __init__(self, recovery_engine: RecoveryEngine | None = None, emulator_manager: EmulatorManager | None = None) -> None:
        self.recovery_engine = recovery_engine or RecoveryEngine()
        self.emulator_manager = emulator_manager or EmulatorManager(root_service=self.recovery_engine.root_service)

    def restore_account(self, account_path: Path, emulator_id: int, callback: ProgressCallback | None = None) -> RecoveryResult:
        emulator = self.emulator_manager.get(emulator_id)
        return self.recovery_engine.recover(account_path, emulator, callback)


def restore_account(account_path: Path, emulator_id: int) -> None:
    """Restore an account backup to emulator 1~4 using the recovery engine."""
    if emulator_id not in {1, 2, 3, 4}:
        raise ValueError("emulator_id 必须是 1~4")
    if not account_path.exists() or not account_path.is_dir():
        raise FileNotFoundError(f"账号目录不存在：{account_path}")
    emulator = Emulator(id=emulator_id, name=f"模拟器{emulator_id}", adb_serial=f"emulator-{5552 + (emulator_id - 1) * 2}", root_path=str(account_path / "current_shared_prefs"))
    RecoveryEngine().recover(account_path, emulator)
