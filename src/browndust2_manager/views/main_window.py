from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from browndust2_manager.models.account import Account
from browndust2_manager.models.account_list_model import AccountListModel, format_bytes


class MainControllerProtocol(Protocol):
    def choose_accounts_dir(self) -> None: ...
    def refresh_accounts(self) -> None: ...
    def add_account(self) -> None: ...
    def import_zip(self) -> None: ...
    def export_selected_accounts(self) -> None: ...
    def restore_selected_accounts(self, emulator_id: int) -> None: ...
    def open_selected_account_dir(self) -> None: ...
    def delete_selected_accounts(self) -> None: ...
    def rename_selected_account(self) -> None: ...


class AccountFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row: int, source_parent):  # noqa: N802
        pattern = self.filterRegularExpression().pattern().lower()
        if not pattern:
            return True
        account = self.sourceModel().account_at(source_row)  # type: ignore[attr-defined]
        return account is not None and pattern in account.name.lower()

    def lessThan(self, left, right):  # noqa: N802
        left_account = self.sourceModel().account_at(left.row())  # type: ignore[attr-defined]
        right_account = self.sourceModel().account_at(right.row())  # type: ignore[attr-defined]
        if left_account is None or right_account is None:
            return False
        column = left.column()
        values = [
            (left_account.name, right_account.name),
            (left_account.name.lower(), right_account.name.lower()),
            (left_account.modified_at, right_account.modified_at),
            (left_account.shared_prefs_size, right_account.shared_prefs_size),
            (left_account.is_valid, right_account.is_valid),
        ][column]
        return values[0] < values[1]


class MainWindow(QMainWindow):
    """Main PySide6 window containing account management UI."""

    directory_chosen = Signal(Path)

    def __init__(self, model: AccountListModel) -> None:
        super().__init__()
        self._controller: MainControllerProtocol | None = None
        self._model = model
        self._proxy = AccountFilterProxyModel(self)
        self._proxy.setSourceModel(model)
        self._current_dir: Path | None = None
        self._detail_labels: dict[str, QLabel] = {}

        self.setWindowTitle("BrownDust2Manager")
        self.resize(1200, 720)
        self._build_ui()

    def set_controller(self, controller: MainControllerProtocol) -> None:
        self._controller = controller

    def _build_ui(self) -> None:
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for text, handler in (
            ("扫描", self._on_choose_dir_clicked),
            ("刷新", self._on_refresh_clicked),
            ("添加账号", lambda: self._controller and self._controller.add_account()),
            ("导入ZIP", lambda: self._controller and self._controller.import_zip()),
            ("导出ZIP", lambda: self._controller and self._controller.export_selected_accounts()),
            ("批量恢复", lambda: self._controller and self._controller.restore_selected_accounts(1)),
            ("设置", lambda: self.show_info("设置", "设置功能将在后续版本扩展。")),
            ("日志", lambda: self.show_info("日志", "请查看状态栏和终端输出。")),
        ):
            button = QPushButton(text)
            button.clicked.connect(handler)
            toolbar.addWidget(button)

        root = QWidget()
        layout = QHBoxLayout(root)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self._directory_label = QLabel("账号目录：未设置")
        self._directory_label.setWordWrap(True)
        left_layout.addWidget(self._directory_label)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索账号...")
        self.search_box.textChanged.connect(self._proxy.setFilterFixedString)
        left_layout.addWidget(self.search_box)

        self.account_list = QTableView()
        self.account_list.setModel(self._proxy)
        self.account_list.setSortingEnabled(True)
        self.account_list.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.account_list.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.account_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self._show_account_menu)
        self.account_list.selectionModel().selectionChanged.connect(lambda *_: self._update_details())
        self.account_list.resizeColumnsToContents()
        left_layout.addWidget(self.account_list)
        left_panel.setMinimumWidth(560)
        layout.addWidget(left_panel)

        detail_panel = QWidget()
        form = QFormLayout(detail_panel)
        for key in (
            "账号目录", "shared_prefs路径", "BuildPlayerVersion", "game_data_version",
            "bundle_version", "unity.cloud_userid", "Firebase User", "最后修改时间", "文件数量", "目录大小",
        ):
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._detail_labels[key] = label
            form.addRow(f"{key}：", label)
        layout.addWidget(detail_panel, stretch=1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def selected_source_rows(self) -> list[int]:
        rows = {self._proxy.mapToSource(index).row() for index in self.account_list.selectionModel().selectedRows()}
        return sorted(rows)

    def selected_account(self) -> Account | None:
        rows = self.selected_source_rows()
        return self._model.account_at(rows[0]) if rows else None

    def _update_details(self) -> None:
        account = self.selected_account()
        values = {} if account is None else {
            "账号目录": str(account.path),
            "shared_prefs路径": str(account.shared_prefs_path or ""),
            "BuildPlayerVersion": account.build_player_version,
            "game_data_version": account.game_data_version,
            "bundle_version": account.bundle_version,
            "unity.cloud_userid": account.unity_cloud_userid,
            "Firebase User": account.firebase_user,
            "最后修改时间": account.modified_at.strftime("%Y-%m-%d %H:%M:%S"),
            "文件数量": str(account.file_count),
            "目录大小": format_bytes(account.directory_size),
        }
        for key, label in self._detail_labels.items():
            label.setText(values.get(key, "-"))

    def set_accounts_dir(self, path: Path) -> None:
        self._current_dir = path
        self._directory_label.setText(f"账号目录：{path}")

    def ask_accounts_dir(self) -> Path | None:
        directory = QFileDialog.getExistingDirectory(self, "选择 BrownDust2 账号目录", str(self._current_dir or Path.home()))
        return Path(directory) if directory else None

    def ask_account_dir(self) -> Path | None:
        directory = QFileDialog.getExistingDirectory(self, "选择要添加的账号目录", str(Path.home()))
        return Path(directory) if directory else None

    def ask_open_zip(self) -> Path | None:
        filename, _ = QFileDialog.getOpenFileName(self, "导入账号 ZIP", str(Path.home()), "ZIP (*.zip)")
        return Path(filename) if filename else None

    def ask_save_zip(self, default_name: str) -> Path | None:
        filename, _ = QFileDialog.getSaveFileName(self, "导出账号 ZIP", default_name, "ZIP (*.zip)")
        return Path(filename) if filename else None

    def ask_text(self, title: str, label: str, text: str) -> str | None:
        from PySide6.QtWidgets import QInputDialog
        value, ok = QInputDialog.getText(self, title, label, text=text)
        return value if ok and value.strip() else None

    def confirm(self, title: str, message: str) -> bool:
        return QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes

    def show_info(self, title: str, message: str) -> None: QMessageBox.information(self, title, message)
    def show_error(self, title: str, message: str) -> None: QMessageBox.critical(self, title, message)
    def set_status(self, message: str) -> None: self.statusBar().showMessage(message, 6000)

    def _on_choose_dir_clicked(self) -> None:
        if self._controller: self._controller.choose_accounts_dir()
    def _on_refresh_clicked(self) -> None:
        if self._controller: self._controller.refresh_accounts()

    def _show_account_menu(self, position) -> None:
        if self._controller is None:
            return
        menu = QMenu(self)
        for emulator_id in range(1, 5):
            action = menu.addAction(f"恢复到模拟器{emulator_id}")
            action.triggered.connect(lambda checked=False, target=emulator_id: self._controller.restore_selected_accounts(target))
        menu.addSeparator()
        for text, handler in (
            ("打开目录", self._controller.open_selected_account_dir),
            ("导出ZIP", self._controller.export_selected_accounts),
            ("删除账号", self._controller.delete_selected_accounts),
            ("重命名", self._controller.rename_selected_account),
            ("刷新", self._controller.refresh_accounts),
        ):
            action = menu.addAction(text)
            action.triggered.connect(handler)
        menu.exec(self.account_list.viewport().mapToGlobal(position))
