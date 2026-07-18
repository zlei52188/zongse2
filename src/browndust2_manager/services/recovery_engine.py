from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Event
from typing import Callable

from browndust2_manager.models.emulator import Emulator
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.backup_service import BackupService
from browndust2_manager.services.root_service import RootService
from browndust2_manager.services.verify_service import VerifyService

ProgressCallback = Callable[["RecoveryProgress"], None]


class RecoveryStep(str, Enum):
    SCAN_ACCOUNT = "扫描账号"
    XML_REPAIR = "XML修复"
    STOP_GAME = "停止游戏"
    BACKUP = "备份当前shared_prefs"
    RESTORE = "恢复账号"
    PERMISSIONS = "恢复权限"
    START_GAME = "启动游戏"
    VERIFY = "检测结果"


@dataclass(frozen=True, slots=True)
class RecoveryProgress:
    account: Path
    emulator: Emulator
    step: RecoveryStep
    elapsed_seconds: float
    message: str
    progress: int


@dataclass(slots=True)
class RecoveryResult:
    account: Path
    emulator: Emulator
    success: bool
    attempts: int
    elapsed_seconds: float
    reason: str = ""
    log: list[str] = field(default_factory=list)
    backup_path: Path | None = None


@dataclass(slots=True)
class BatchRecoveryResult:
    results: list[RecoveryResult]

    @property
    def success_count(self) -> int:
        return sum(1 for item in self.results if item.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for item in self.results if not item.success)

    @property
    def failure_reasons(self) -> list[str]:
        return [f"{item.account.name} -> {item.emulator.name}: {item.reason}" for item in self.results if not item.success]

    def export_log(self, path: Path) -> None:
        lines = [f"成功数量: {self.success_count}", f"失败数量: {self.failed_count}"]
        lines.extend(self.failure_reasons)
        for result in self.results:
            lines.append(f"[{result.account.name}][{result.emulator.name}] attempts={result.attempts} success={result.success}")
            lines.extend(result.log)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")


class RecoveryEngine:
    """Controls the complete account recovery workflow."""

    MAX_RETRIES = 3

    def __init__(self, root_service: RootService | None = None, backup_service: BackupService | None = None, verify_service: VerifyService | None = None, scanner: AccountScanner | None = None) -> None:
        self.root_service = root_service or RootService()
        self.backup_service = backup_service or BackupService()
        self.verify_service = verify_service or VerifyService()
        self.scanner = scanner or AccountScanner()
        self._paused = Event()
        self._paused.set()
        self._cancelled = Event()

    def pause(self) -> None:
        self._paused.clear()

    def resume(self) -> None:
        self._paused.set()

    def cancel(self) -> None:
        self._cancelled.set()
        self._paused.set()

    def recover(self, account_path: Path, emulator: Emulator, callback: ProgressCallback | None = None) -> RecoveryResult:
        last: RecoveryResult | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            self._cancelled.clear()
            result = self._recover_once(account_path, emulator, attempt, callback)
            last = result
            if result.success:
                return result
        return last or RecoveryResult(account_path, emulator, False, 0, 0, "未执行")

    def recover_batch(self, accounts: list[Path], emulators: list[Emulator], callback: ProgressCallback | None = None) -> BatchRecoveryResult:
        results = []
        for account in accounts:
            for emulator in emulators:
                self._paused.wait()
                if self._cancelled.is_set():
                    return BatchRecoveryResult(results)
                results.append(self.recover(account, emulator, callback))
        return BatchRecoveryResult(results)

    def _recover_once(self, account_path: Path, emulator: Emulator, attempt: int, callback: ProgressCallback | None) -> RecoveryResult:
        start = time.monotonic()
        log: list[str] = []
        backup_path: Path | None = None
        steps = list(RecoveryStep)

        def emit(step: RecoveryStep, message: str) -> None:
            self._paused.wait()
            if self._cancelled.is_set():
                raise RuntimeError("恢复已取消")
            log.append(message)
            if callback:
                callback(RecoveryProgress(account_path, emulator, step, time.monotonic() - start, message, int((steps.index(step) + 1) / len(steps) * 100)))

        try:
            emit(RecoveryStep.SCAN_ACCOUNT, f"扫描账号：{account_path}")
            if not account_path.exists() or not account_path.is_dir():
                raise FileNotFoundError(f"账号目录不存在：{account_path}")
            shared_prefs = account_path / "shared_prefs" if (account_path / "shared_prefs").is_dir() else account_path

            emit(RecoveryStep.XML_REPAIR, "检查并修复账号 XML")
            missing = self.verify_service.verify_and_repair(shared_prefs)
            if missing:
                raise RuntimeError(f"XML 修复后仍缺失：{', '.join(missing)}")

            emit(RecoveryStep.STOP_GAME, f"停止游戏：{emulator.adb_serial}")
            self.root_service.stop_game(emulator.adb_serial)

            emit(RecoveryStep.BACKUP, "备份当前 shared_prefs")
            backup_path = self.backup_service.create_backup(Path(emulator.root_path))

            emit(RecoveryStep.RESTORE, "恢复账号 shared_prefs")
            self.root_service.push_shared_prefs(emulator.adb_serial, shared_prefs)

            emit(RecoveryStep.PERMISSIONS, "恢复文件权限")
            self.root_service.restore_permissions(emulator.adb_serial)

            emit(RecoveryStep.START_GAME, "启动游戏")
            self.root_service.start_game(emulator.adb_serial)

            emit(RecoveryStep.VERIFY, "检测恢复结果")
            return RecoveryResult(account_path, emulator, True, attempt, time.monotonic() - start, log=log, backup_path=backup_path)
        except Exception as exc:  # noqa: BLE001 - retry engine records all failures
            log.append(f"失败：{exc}")
            return RecoveryResult(account_path, emulator, False, attempt, time.monotonic() - start, str(exc), log, backup_path)
