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


def test_scan_reads_player_prefs_metadata(tmp_path):
    account_dir = tmp_path / "account-a"
    prefs_dir = account_dir / "shared_prefs"
    prefs_dir.mkdir(parents=True)
    (prefs_dir / "com.neowizgames.game.browndust2.v2.playerprefs.xml").write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<map>
  <string name="BuildPlayerVersion">1.2.3</string>
  <string name="game_data_version">20260718</string>
  <string name="bundle_version">9</string>
  <string name="unity.cloud_userid">cloud-123</string>
  <string name="Firebase User">firebase-abc</string>
</map>
""",
        encoding="utf-8",
    )

    account = AccountScanner().scan(tmp_path)[0]

    assert account.is_valid is True
    assert account.shared_prefs_path == prefs_dir
    assert account.build_player_version == "1.2.3"
    assert account.game_data_version == "20260718"
    assert account.bundle_version == "9"
    assert account.unity_cloud_userid == "cloud-123"
    assert account.firebase_user == "firebase-abc"
    assert account.file_count == 1
    assert account.directory_size > 0
