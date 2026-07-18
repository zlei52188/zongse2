from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTableView,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.models.emulator_config_model import EmulatorConfigModel
from browndust2_manager.services.root_service import DeviceInfo


class MainControllerProtocol(Protocol):
    def choose_accounts_dir(self) -> None: ...
    def refresh_accounts(self) -> None: ...
    def refresh_devices(self) -> None: ...
    def connect_emulators(self) -> None: ...
    def check_selected_root(self) -> None: ...
    def restore_selected_account(self, row: int, emulator_id: int) -> None: ...


class MainWindow(QMainWindow):
    """Main PySide6 window for rooted BrownDust2 account restoration."""

    directory_chosen = Signal(Path)

    def __init__(self, model: AccountListModel, emulator_model: EmulatorConfigModel) -> None:
        super().__init__()
        self._controller: MainControllerProtocol | None = None
        self._model = model
        self._emulator_model = emulator_model
        self._current_dir: Path | None = None

        self.setWindowTitle("BrownDust2Manager Root恢复器")
        self.resize(1180, 760)
        self._build_ui()

    def set_controller(self, controller: MainControllerProtocol) -> None:
        self._controller = controller

    def _build_ui(self) -> None:
        toolbar = QToolBar("Root恢复器")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        for text, handler in [
            ("选择目录...", self._on_choose_dir_clicked),
            ("刷新账号", self._on_refresh_clicked),
            ("连接模拟器", self._on_connect_clicked),
            ("刷新设备", self._on_refresh_devices_clicked),
            ("检测Root", self._on_check_root_clicked),
        ]:
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

        self.account_list = QListView()
        self.account_list.setModel(self._model)
        self.account_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self._show_account_menu)
        left_layout.addWidget(self.account_list)
        left_panel.setMaximumWidth(360)
        layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("模拟器配置（仅支持 Root Android 模拟器）"))
        self.emulator_table = QTableView()
        self.emulator_table.setModel(self._emulator_model)
        self.emulator_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.emulator_table.selectRow(0)
        right_layout.addWidget(self.emulator_table)

        right_layout.addWidget(QLabel("已识别设备"))
        self._devices_label = QLabel("尚未刷新设备。")
        self._devices_label.setWordWrap(True)
        right_layout.addWidget(self._devices_label)

        right_layout.addWidget(QLabel("恢复进度"))
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        right_layout.addWidget(self._progress)

        right_layout.addWidget(QLabel("ADB / Root日志"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        right_layout.addWidget(self._log, stretch=1)
        layout.addWidget(right_panel, stretch=1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def selected_emulator_slot(self) -> int:
        row = self.emulator_table.currentIndex().row()
        return row + 1 if row >= 0 else 1

    def set_devices(self, devices: list[DeviceInfo]) -> None:
        if not devices:
            self._devices_label.setText("未发现设备。")
            return
        self._devices_label.setText("\n".join(
            f"设备名称：{d.name} | serial：{d.serial} | 状态：{d.state} | Root状态：{d.root_status} | Android版本：{d.android_version}"
            for d in devices
        ))

    def append_log(self, message: str) -> None:
        self._log.append(message)
        self._log.append("-" * 80)

    def set_restore_progress(self, value: int) -> None:
        self._progress.setValue(value)

    def set_accounts_dir(self, path: Path) -> None:
        self._current_dir = path
        self._directory_label.setText(f"账号目录：{path}")

    def ask_accounts_dir(self) -> Path | None:
        directory = QFileDialog.getExistingDirectory(self, "选择 BrownDust2 账号目录", str(self._current_dir or Path.home()))
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

    def _on_connect_clicked(self) -> None:
        if self._controller:
            self._controller.connect_emulators()

    def _on_refresh_devices_clicked(self) -> None:
        if self._controller:
            self._controller.refresh_devices()

    def _on_check_root_clicked(self) -> None:
        if self._controller:
            self._controller.check_selected_root()

    def _show_account_menu(self, position: QPoint) -> None:
        index = self.account_list.indexAt(position)
        if not index.isValid() or self._controller is None:
            return

        menu = QMenu(self)
        for emulator_id in range(1, 5):
            action = menu.addAction(f"恢复到 模拟器{emulator_id}")
            action.triggered.connect(
                lambda checked=False, row=index.row(), target=emulator_id: self._controller.restore_selected_account(row, target)
            )
        menu.exec(self.account_list.viewport().mapToGlobal(position))
