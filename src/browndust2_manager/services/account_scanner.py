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
            stat = child.stat()
            accounts.append(
                Account(
                    name=child.name,
                    path=child,
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                )
            )
        return sorted(accounts, key=lambda account: account.name.lower())
