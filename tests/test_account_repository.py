from __future__ import annotations

from browndust2_manager.repositories.account_repository import AccountRepository
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.account_service import AccountService


def test_scan_and_sync_creates_sqlite_record(tmp_path):
    account_dir = tmp_path / "acc"
    prefs = account_dir / "shared_prefs"
    prefs.mkdir(parents=True)
    (prefs / "game.xml").write_text('<map><string name="unity_cloud_userid">u1</string></map>', encoding="utf-8")
    repository = AccountRepository(tmp_path / "accounts.db")
    service = AccountService(AccountScanner(), repository)

    accounts = service.scan_and_sync(tmp_path)

    assert len(accounts) == 1
    assert accounts[0].id is not None
    assert accounts[0].unity_cloud_userid == "u1"
    assert repository.list_accounts()[0].account_name == "acc"


def test_integrity_checks_report_missing_shared_prefs(tmp_path):
    account_dir = tmp_path / "acc"
    account_dir.mkdir()
    repository = AccountRepository(tmp_path / "accounts.db")
    account = repository.upsert_scanned_account(AccountScanner().account_from_folder(account_dir))
    service = AccountService(AccountScanner(), repository)

    result = service.check_shared_prefs(account)

    assert result.ok is False
    assert "缺少 shared_prefs 目录" in result.messages
