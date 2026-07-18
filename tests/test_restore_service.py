from __future__ import annotations

import stat

import pytest

from browndust2_manager.services.restore_service import RestoreService, restore_account


def test_restore_account_validates_emulator_id(tmp_path):
    account_dir = tmp_path / "account"
    account_dir.mkdir()

    with pytest.raises(ValueError):
        restore_account(account_dir, 5)


def test_restore_account_validates_account_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_account(tmp_path / "missing", 1)


def test_restore_account_copies_shared_prefs_and_replaces_target(tmp_path):
    account_dir = tmp_path / "account"
    source_prefs = account_dir / "shared_prefs"
    source_prefs.mkdir(parents=True)
    source_file = source_prefs / "player.xml"
    source_file.write_text("new-account", encoding="utf-8")
    source_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    target_data_dir = (
        tmp_path / "emu1" / "data" / "data" / "com.neowizgames.game.browndust2"
    )
    target_prefs = target_data_dir / "shared_prefs"
    target_prefs.mkdir(parents=True)
    (target_prefs / "old.xml").write_text("old-account", encoding="utf-8")

    messages: list[str] = []

    restore_account(
        account_dir,
        1,
        {1: target_data_dir},
        log_callback=messages.append,
    )

    copied_file = target_prefs / "player.xml"
    assert not (target_prefs / "old.xml").exists()
    assert copied_file.read_text(encoding="utf-8") == "new-account"
    assert stat.S_IMODE(copied_file.stat().st_mode) == stat.S_IRUSR | stat.S_IWUSR
    assert messages == ["正在删除……", "正在复制……", "恢复完成"]


def test_restore_service_saves_and_loads_emulator_dirs(tmp_path):
    config_path = tmp_path / "settings.json"
    first_service = RestoreService(config_path=config_path)
    emulator_dirs = {slot: tmp_path / f"emu{slot}" for slot in range(1, 5)}

    first_service.set_emulator_dirs(emulator_dirs)
    first_service.save_config()

    second_service = RestoreService(config_path=config_path)

    assert second_service.emulator_dirs() == emulator_dirs
