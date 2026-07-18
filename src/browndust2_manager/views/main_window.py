from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from browndust2_manager.models.account_list_model import AccountListModel


class MainControllerProtocol(Protocol):
    def choose_accounts_dir(self) -> None: ...
    def refresh_accounts(self) -> None: ...
    def restore_selected_account(self, row: int, emulator_id: int) -> None: ...


class MainWindow(QMainWindow):
    """Main PySide6 window containing the left account list."""

    directory_chosen = Signal(Path)

    def __init__(self, model: AccountListModel) -> None:
        super().__init__()
        self._controller: MainControllerProtocol | None = None
        self._model = model
        self._current_dir: Path | None = None

        self.setWindowTitle("BrownDust2Manager")
        self.resize(960, 600)
        self._build_ui()

    def set_controller(self, controller: MainControllerProtocol) -> None:
        self._controller = controller

    def _build_ui(self) -> None:
        toolbar = QToolBar("账号")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        choose_button = QPushButton("选择目录...")
        choose_button.clicked.connect(self._on_choose_dir_clicked)
        toolbar.addWidget(choose_button)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self._on_refresh_clicked)
        toolbar.addWidget(refresh_button)

        root = QWidget()
        layout = QHBoxLayout(root)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self._directory_label = QLabel("账号目录：未设置")
        self._directory_label.setWordWrap(True)
        left_layout.addWidget(self._directory_label)

        self.account_list = QListView()
        self.account_list.setModel(self._model)
        self.account_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self._show_account_menu)
        left_layout.addWidget(self.account_list)
        left_panel.setMaximumWidth(360)
        layout.addWidget(left_panel)

        detail = QLabel("右键左侧账号，可恢复到 1~4 号模拟器。")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail, stretch=1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def set_accounts_dir(self, path: Path) -> None:
        self._current_dir = path
        self._directory_label.setText(f"账号目录：{path}")

    def ask_accounts_dir(self) -> Path | None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择 BrownDust2 账号目录",
            str(self._current_dir or Path.home()),
        )
        return Path(directory) if directory else None

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def set_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)

    def _on_choose_dir_clicked(self) -> None:
        if self._controller:
            self._controller.choose_accounts_dir()

    def _on_refresh_clicked(self) -> None:
        if self._controller:
            self._controller.refresh_accounts()

    def _show_account_menu(self, position: QPoint) -> None:
        index = self.account_list.indexAt(position)
        if not index.isValid() or self._controller is None:
            return

        menu = QMenu(self)
        for emulator_id in range(1, 5):
            action = menu.addAction(f"恢复到 {emulator_id} 号模拟器")
            action.triggered.connect(
                lambda checked=False, row=index.row(), target=emulator_id: self._controller.restore_selected_account(row, target)
            )
        menu.exec(self.account_list.viewport().mapToGlobal(position))
