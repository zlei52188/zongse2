from __future__ import annotations

from browndust2_manager.services.account_scanner import AccountScanner


def test_scan_returns_sorted_account_directories(tmp_path):
    (tmp_path / "beta").mkdir()
    (tmp_path / "Alpha").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "note.txt").write_text("ignored", encoding="utf-8")

    accounts = AccountScanner().scan(tmp_path)

    assert [account.name for account in accounts] == ["Alpha", "beta"]


def test_scan_missing_directory_returns_empty_list(tmp_path):
    accounts = AccountScanner().scan(tmp_path / "missing")

    assert accounts == []
