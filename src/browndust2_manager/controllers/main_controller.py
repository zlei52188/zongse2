from __future__ import annotations

from pathlib import Path

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.folder_opener import FolderOpener
from browndust2_manager.services.restore_service import RestoreService
from browndust2_manager.views.main_window import MainWindow


class MainController:
    """Connects the model, PySide6 view, and account services."""

    def __init__(
        self,
        model: AccountListModel,
        scanner: AccountScanner,
        restore_service: RestoreService,
        folder_opener: FolderOpener,
        window: MainWindow,
    ) -> None:
        self._model = model
        self._scanner = scanner
        self._restore_service = restore_service
        self._folder_opener = folder_opener
        self._window = window
        self._accounts_dir: Path = scanner.default_accounts_dir()

    def load_default_accounts(self) -> None:
        self._window.set_accounts_dir(self._accounts_dir)
        self.refresh_accounts()

    def choose_accounts_dir(self) -> None:
        selected = self._window.ask_accounts_dir()
        if selected is None:
            return
        self._accounts_dir = selected
        self._window.set_accounts_dir(selected)
        self.refresh_accounts()

    def refresh_accounts(self) -> None:
        try:
            accounts = self._scanner.scan(self._accounts_dir)
        except Exception as exc:  # noqa: BLE001 - surface scan errors in GUI
            self._window.show_error("扫描失败", str(exc))
            return

        self._model.set_accounts(accounts)
        self._window.set_status(f"已扫描 {len(accounts)} 个账号。")

    def restore_selected_account(self, row: int, emulator_id: int) -> None:
        account = self._model.account_at(row)
        if account is None:
            self._window.show_error("恢复失败", "未找到选中的账号。")
            return

        try:
            self._restore_service.restore_account(account.path, emulator_id)
        except Exception as exc:  # noqa: BLE001 - surface restore errors in GUI
            self._window.show_error("恢复失败", str(exc))
            return

        self._window.show_info("恢复完成", f"账号 {account.name} 已恢复到 {emulator_id} 号模拟器。")

    def open_account_folder(self, row: int) -> None:
        account = self._model.account_at(row)
        if account is None:
            self._window.show_error("打开失败", "未找到选中的账号。")
            return

        try:
            self._folder_opener.open_folder(account.path)
        except Exception as exc:  # noqa: BLE001 - surface open errors in GUI
            self._window.show_error("打开失败", str(exc))
            return

        self._window.set_status(f"已打开账号目录：{account.path}")
