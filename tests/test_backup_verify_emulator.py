from __future__ import annotations

from datetime import datetime

from browndust2_manager.models.emulator import Emulator
from browndust2_manager.services.backup_service import BackupService
from browndust2_manager.services.emulator_manager import EmulatorManager
from browndust2_manager.services.verify_service import VerifyService


def test_backup_service_create_list_restore_delete(tmp_path):
    prefs = tmp_path / "prefs"
    prefs.mkdir()
    (prefs / "a.xml").write_text("a", encoding="utf-8")
    service = BackupService(tmp_path / "backup")

    backup = service.create_backup(prefs, datetime(2026, 7, 18, 1, 2, 3))
    assert backup.name == "20260718_010203"
    assert service.list_backups()[0].path == backup
    target = tmp_path / "target"
    service.restore_backup(backup, target)
    assert (target / "a.xml").read_text(encoding="utf-8") == "a"
    service.delete_backup(backup)
    assert service.list_backups() == []


def test_verify_service_repairs_required_keys(tmp_path):
    prefs = tmp_path / "prefs"
    missing = VerifyService().verify_and_repair(prefs)
    assert missing == []
    assert VerifyService().verify(prefs) == []


def test_emulator_manager_saves_four_slots(tmp_path):
    manager = EmulatorManager(tmp_path / "emulators.json")
    emulators = [Emulator(i, f"E{i}", f"s{i}", f"/r{i}") for i in range(1, 5)]
    manager.save(emulators)
    assert [item.name for item in EmulatorManager(tmp_path / "emulators.json").all()] == ["E1", "E2", "E3", "E4"]
