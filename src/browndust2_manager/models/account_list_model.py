from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from browndust2_manager.models.account import Account


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


class AccountListModel(QAbstractTableModel):
    """Qt table model that exposes scanned BrownDust2 accounts."""

    COLUMNS = ("图标", "账号名称", "最后修改时间", "shared_prefs大小", "是否有效")

    def __init__(self) -> None:
        super().__init__()
        self._accounts: list[Account] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._accounts)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._accounts):
            return None
        account = self._accounts[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return (
                "",
                account.name,
                account.modified_at.strftime("%Y-%m-%d %H:%M:%S"),
                format_bytes(account.shared_prefs_size),
                "有效" if account.is_valid else "无效",
            )[index.column()]
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            app = QApplication.instance()
            if app:
                return app.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            return QIcon()
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{account.path}\nshared_prefs：{format_bytes(account.shared_prefs_size)}"
        if role == Qt.ItemDataRole.UserRole:
            return account
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

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
        account = Account(path.name, path, datetime.fromtimestamp(stat.st_mtime))
        self.set_accounts([*self._accounts, account])
