from __future__ import annotations

import pytest

from browndust2_manager.services.restore_service import restore_account


def test_restore_account_validates_emulator_id(tmp_path):
    account_dir = tmp_path / "account"
    account_dir.mkdir()

    with pytest.raises(ValueError):
        restore_account(account_dir, 5)


def test_restore_account_validates_account_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_account(tmp_path / "missing", 1)
