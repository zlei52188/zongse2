from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from browndust2_manager.models.account import Account


class AccountListModel(QAbstractListModel):
    """Qt list model that exposes scanned BrownDust2 accounts."""

    NameRole = Qt.ItemDataRole.UserRole + 1
    PathRole = Qt.ItemDataRole.UserRole + 2
    ModifiedAtRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self) -> None:
        super().__init__()
        self._accounts: list[Account] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._accounts)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._accounts):
            return None

        account = self._accounts[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return account.account_name
        if role == self.NameRole:
            return account.account_name
        if role == self.PathRole:
            return str(account.folder_path)
        if role == self.ModifiedAtRole:
            return account.modified_at.strftime("%Y-%m-%d %H:%M:%S")
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{account.folder_path}\n修改时间：{account.modified_at:%Y-%m-%d %H:%M:%S}"
        return None

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.NameRole: b"name",
            self.PathRole: b"path",
            self.ModifiedAtRole: b"modified_at",
        }

    def set_accounts(self, accounts: Sequence[Account]) -> None:
        self.beginResetModel()
        self._accounts = list(accounts)
        self.endResetModel()

    def account_at(self, row: int) -> Account | None:
        if 0 <= row < len(self._accounts):
            return self._accounts[row]
        return None

    def add_manual_account(self, path: Path) -> None:
        stat = path.stat()
        account = Account(None, path.name, path, datetime.fromtimestamp(stat.st_mtime))
        self.set_accounts([*self._accounts, account])
