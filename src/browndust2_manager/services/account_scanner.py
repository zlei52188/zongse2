from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from browndust2_manager.models.account import Account


class AccountScanner:
    """Scans a filesystem directory for account backup folders."""

    DEFAULT_ENV_NAME = "BROWNDUST2_ACCOUNTS_DIR"
    DEFAULT_RELATIVE_DIR = Path("Documents") / "BrownDust2Accounts"

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
            accounts.append(self.account_from_folder(child))
        return sorted(accounts, key=lambda account: account.name.lower())

    def account_from_folder(self, folder: Path) -> Account:
        """从账号文件夹构造账号对象并提取基础版本字段。"""
        stat = folder.stat()
        xml_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in (folder / "shared_prefs").glob("*.xml")) if (folder / "shared_prefs").is_dir() else ""
        return Account(
            id=None,
            account_name=folder.name,
            folder_path=folder,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            unity_cloud_userid=self._extract_value(xml_text, "unity_cloud_userid"),
            game_data_version=self._extract_value(xml_text, "game_data_version"),
            bundle_version=self._extract_value(xml_text, "bundle_version"),
            build_player_version=self._extract_value(xml_text, "BuildPlayerVersion"),
            status="正常" if (folder / "shared_prefs").is_dir() else "缺少shared_prefs",
        )

    def _extract_value(self, text: str, key: str) -> str:
        """用轻量方式从 shared_prefs XML 文本提取字段。"""
        marker = f'name="{key}"'
        index = text.find(marker)
        if index == -1:
            return ""
        tail = text[index:index + 300]
        if ">" not in tail:
            return ""
        value = tail.split(">", 1)[1].split("<", 1)[0].strip()
        return value
