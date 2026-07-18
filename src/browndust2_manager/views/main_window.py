from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QPoint, QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.services.xml_repair_service import XmlRepairPreview, XmlVersionConfig


class MainControllerProtocol(Protocol):
    def choose_accounts_dir(self) -> None: ...
    def refresh_accounts(self) -> None: ...
    def restore_selected_account(self, row: int, emulator_id: int) -> None: ...
    def repair_selected_accounts(self, rows: list[int]) -> None: ...


class MainWindow(QMainWindow):
    """Main PySide6 window containing the left account list."""

    directory_chosen = Signal(Path)

    def __init__(self, model: AccountListModel) -> None:
        super().__init__()
        self._controller: MainControllerProtocol | None = None
        self._model = model
        self._current_dir: Path | None = None
        self._settings = QSettings("BrownDust2Manager", "BrownDust2Manager")

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

        repair_button = QPushButton("仅修复XML")
        repair_button.clicked.connect(self._on_repair_clicked)
        toolbar.addWidget(repair_button)

        root = QWidget()
        layout = QHBoxLayout(root)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self._directory_label = QLabel("账号目录：未设置")
        self._directory_label.setWordWrap(True)
        left_layout.addWidget(self._directory_label)

        self.account_list = QListView()
        self.account_list.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.account_list.setModel(self._model)
        self.account_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self._show_account_menu)
        left_layout.addWidget(self.account_list)
        left_panel.setMaximumWidth(360)
        layout.addWidget(left_panel)

        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.addWidget(QLabel("设置：恢复/修复时使用的版本值"))
        form = QFormLayout()
        self._game_data_version = QLineEdit(str(self._settings.value("game_data_version", "")))
        self._bundle_version = QLineEdit(str(self._settings.value("bundle_version", "")))
        self._build_player_version = QLineEdit(str(self._settings.value("BuildPlayerVersion", "")))
        for edit in (self._game_data_version, self._bundle_version, self._build_player_version):
            edit.editingFinished.connect(self._save_version_settings)
        form.addRow("game_data_version", self._game_data_version)
        form.addRow("bundle_version", self._bundle_version)
        form.addRow("BuildPlayerVersion", self._build_player_version)
        settings_layout.addLayout(form)
        settings_layout.addStretch(1)
        layout.addWidget(settings_panel, stretch=1)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def version_config(self) -> XmlVersionConfig:
        self._save_version_settings()
        return XmlVersionConfig(
            game_data_version=self._game_data_version.text().strip(),
            bundle_version=self._bundle_version.text().strip(),
            build_player_version=self._build_player_version.text().strip(),
        )

    def _save_version_settings(self) -> None:
        self._settings.setValue("game_data_version", self._game_data_version.text().strip())
        self._settings.setValue("bundle_version", self._bundle_version.text().strip())
        self._settings.setValue("BuildPlayerVersion", self._build_player_version.text().strip())

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

    def confirm_repair_preview(self, account_name: str, preview: XmlRepairPreview) -> bool:
        return self.confirm_batch_repair_preview([(account_name, preview)])

    def confirm_batch_repair_preview(self, previews: list[tuple[str, XmlRepairPreview]]) -> bool:
        dialog = QDialog(self)
        dialog.setWindowTitle("XML 修复预览")
        dialog.resize(900, 650)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        sections = []
        for account_name, preview in previews:
            diff = preview.diff or "（无变化）\n"
            sections.append(f"# {account_name}\n文件：{preview.path}\n\n{diff}")
        text.setPlainText("\n".join(sections))
        layout.addWidget(QLabel("恢复前 / 恢复后 Diff 对比："))
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _selected_rows(self) -> list[int]:
        return sorted({index.row() for index in self.account_list.selectionModel().selectedIndexes()})

    def _on_choose_dir_clicked(self) -> None:
        if self._controller:
            self._controller.choose_accounts_dir()

    def _on_refresh_clicked(self) -> None:
        if self._controller:
            self._controller.refresh_accounts()

    def _on_repair_clicked(self) -> None:
        if self._controller:
            self._controller.repair_selected_accounts(self._selected_rows())

    def _show_account_menu(self, position: QPoint) -> None:
        index = self.account_list.indexAt(position)
        if not index.isValid() or self._controller is None:
            return

        menu = QMenu(self)
        menu.addAction("仅修复XML").triggered.connect(lambda checked=False: self._controller.repair_selected_accounts(self._selected_rows() or [index.row()]))
        menu.addSeparator()
        for emulator_id in range(1, 5):
            action = menu.addAction(f"恢复到 {emulator_id} 号模拟器")
            action.triggered.connect(
                lambda checked=False, row=index.row(), target=emulator_id: self._controller.restore_selected_account(row, target)
            )
        menu.exec(self.account_list.viewport().mapToGlobal(position))
