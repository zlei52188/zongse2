from __future__ import annotations

from browndust2_manager.models.emulator import Emulator
from browndust2_manager.services.backup_service import BackupService
from browndust2_manager.services.recovery_engine import RecoveryEngine, RecoveryStep
from browndust2_manager.services.verify_service import VerifyService


class FakeRootService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def stop_game(self, serial: str) -> None:
        self.calls.append(f"stop:{serial}")

    def push_shared_prefs(self, serial: str, source) -> None:
        self.calls.append(f"push:{serial}:{source.name}")

    def restore_permissions(self, serial: str) -> None:
        self.calls.append(f"chmod:{serial}")

    def start_game(self, serial: str) -> None:
        self.calls.append(f"start:{serial}")


def test_recovery_engine_runs_full_flow_and_repairs_xml(tmp_path):
    account = tmp_path / "account"
    shared_prefs = account / "shared_prefs"
    shared_prefs.mkdir(parents=True)
    (shared_prefs / VerifyService.PLAYER_PREFS).write_text("<map />", encoding="utf-8")
    current = tmp_path / "current"
    current.mkdir()
    (current / "old.xml").write_text("old", encoding="utf-8")
    root = FakeRootService()
    engine = RecoveryEngine(root_service=root, backup_service=BackupService(tmp_path / "backup"))  # type: ignore[arg-type]
    seen: list[RecoveryStep] = []

    result = engine.recover(account, Emulator(1, "模拟器1", "serial-1", str(current)), lambda progress: seen.append(progress.step))

    assert result.success is True
    assert seen == list(RecoveryStep)
    assert root.calls == ["stop:serial-1", "push:serial-1:shared_prefs", "chmod:serial-1", "start:serial-1"]
    assert VerifyService().verify(shared_prefs) == []
    assert result.backup_path is not None and (result.backup_path / "old.xml").exists()


def test_batch_recovery_reports_success_and_failure_counts(tmp_path):
    account = tmp_path / "account"
    account.mkdir()
    current = tmp_path / "current"
    current.mkdir()
    engine = RecoveryEngine(root_service=FakeRootService(), backup_service=BackupService(tmp_path / "backup"))  # type: ignore[arg-type]

    batch = engine.recover_batch([account, tmp_path / "missing"], [Emulator(1, "模拟器1", "serial-1", str(current))])

    assert batch.success_count == 1
    assert batch.failed_count == 1
    assert "账号目录不存在" in batch.failure_reasons[0]
