from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from browndust2_manager.models.account import Account
from browndust2_manager.services.xml_parser_service import XmlParserService


class AccountScanner:
    """Scans a filesystem directory for account backup folders."""

    DEFAULT_ENV_NAME = "BROWNDUST2_ACCOUNTS_DIR"
    DEFAULT_RELATIVE_DIR = Path("Documents") / "BrownDust2Accounts"

    def __init__(self, xml_parser: XmlParserService | None = None) -> None:
        self._xml_parser = xml_parser or XmlParserService()

    def default_accounts_dir(self) -> Path:
        configured = os.environ.get(self.DEFAULT_ENV_NAME)
        if configured:
            return Path(configured).expanduser()
        return Path.home() / self.DEFAULT_RELATIVE_DIR

    def scan(self, root: Path) -> list[Account]:
        root = root.expanduser()
        if not root.exists():
            return []
        if not root.is_dir():
            raise NotADirectoryError(f"账号目录不是文件夹：{root}")

        accounts: list[Account] = []
        for child in root.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            accounts.append(self._build_account(child))
        return sorted(accounts, key=lambda account: account.name.lower())

    def _build_account(self, path: Path) -> Account:
        stat = path.stat()
        shared_prefs_path = path / "shared_prefs"
        player_prefs_path = shared_prefs_path / XmlParserService.PLAYER_PREFS_FILENAME
        prefs = self._xml_parser.parse_player_prefs(player_prefs_path)
        return Account(
            name=path.name,
            path=path,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            shared_prefs_path=shared_prefs_path,
            player_prefs_path=player_prefs_path,
            shared_prefs_size=self._path_size(shared_prefs_path),
            is_valid=player_prefs_path.exists(),
            build_player_version=prefs.get("BuildPlayerVersion", ""),
            game_data_version=prefs.get("game_data_version", ""),
            bundle_version=prefs.get("bundle_version", ""),
            unity_cloud_userid=prefs.get("unity.cloud_userid", ""),
            firebase_user=prefs.get("Firebase User", ""),
            file_count=self._file_count(path),
            directory_size=self._path_size(path),
        )

    def _path_size(self, path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())

    def _file_count(self, path: Path) -> int:
        return sum(1 for file in path.rglob("*") if file.is_file())
