from __future__ import annotations

from pathlib import Path

import pytest

from browndust2_manager.services.root_service import EmulatorConfig, RootService


class FakeRootService(RootService):
    def __init__(self, rooted: bool = True) -> None:
        super().__init__(adb_path="adb")
        self.rooted = rooted
        self.commands: list[str] = []

    def check_root(self, serial: str) -> bool:
        self.commands.append(f"check_root {serial}")
        return self.rooted

    def _adb(self, serial: str, args: list[str]):  # type: ignore[override]
        from browndust2_manager.services.root_service import CommandResult

        command = "adb -s " + serial + " " + " ".join(args)
        self.commands.append(command)
        return CommandResult(command, "", "", 0, 1)

    def _root_shell(self, serial: str, command: str):  # type: ignore[override]
        from browndust2_manager.services.root_service import CommandResult

        full = f"adb -s {serial} shell su -c {command}"
        self.commands.append(full)
        stdout = "u0_a123" if command.startswith("stat -c %U") else ""
        return CommandResult(full, stdout, "", 0, 1)


def test_restore_account_runs_root_restore_flow(tmp_path: Path):
    account = tmp_path / "account"
    (account / "shared_prefs").mkdir(parents=True)
    service = FakeRootService()
    progress: list[int] = []

    service.restore_account(account, EmulatorConfig(slot=1, serial="emulator-5554"), progress.append)

    assert progress == [10, 30, 60, 90, 100]
    joined = "\n".join(service.commands)
    assert "check_root emulator-5554" in joined
    assert "am force-stop com.neowizgames.game.browndust2" in joined
    assert "rm -rf '/data/data/com.neowizgames.game.browndust2'/shared_prefs" in joined
    assert "push" in joined and "/data/local/tmp/bd2_restore" in joined
    assert "cp -rf '/data/local/tmp/bd2_restore'" in joined
    assert "restorecon -R" in joined
    assert "chown -R u0_a123:u0_a123" in joined
    assert "chmod -R u+rwX,go-rwx" in joined
    assert "sync" in joined
    assert "monkey -p com.neowizgames.game.browndust2" in joined


def test_restore_account_requires_shared_prefs(tmp_path: Path):
    account = tmp_path / "account"
    account.mkdir()

    with pytest.raises(FileNotFoundError):
        FakeRootService().restore_account(account, EmulatorConfig(slot=1, serial="emulator-5554"))


def test_restore_account_requires_root(tmp_path: Path):
    account = tmp_path / "account"
    (account / "shared_prefs").mkdir(parents=True)

    with pytest.raises(PermissionError):
        FakeRootService(rooted=False).restore_account(account, EmulatorConfig(slot=1, serial="emulator-5554"))
