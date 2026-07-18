from __future__ import annotations

from pathlib import Path

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.restore_service import RestoreService
from browndust2_manager.services.xml_repair_service import XmlRepairPreview, XmlVersionConfig
from browndust2_manager.views.main_window import MainWindow


class MainController:
    """Connects the model, PySide6 view, and account services."""

    def __init__(
        self,
        model: AccountListModel,
        scanner: AccountScanner,
        restore_service: RestoreService,
        window: MainWindow,
    ) -> None:
        self._model = model
        self._scanner = scanner
        self._restore_service = restore_service
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

        config = self._window.version_config()
        try:
            preview = self._restore_service.preview_repair(account.path, config)
        except Exception as exc:  # noqa: BLE001 - surface preview errors in GUI
            self._window.show_error("预览失败", str(exc))
            return
        if not self._window.confirm_repair_preview(account.name, preview):
            self._window.set_status("已取消恢复。")
            return

        try:
            self._restore_service.restore_account(account.path, emulator_id, config)
        except Exception as exc:  # noqa: BLE001 - surface restore errors in GUI
            self._window.show_error("恢复失败", str(exc))
            return

        self._window.show_info("恢复完成", f"账号 {account.name} 已修复 XML 并恢复到 {emulator_id} 号模拟器。")

    def repair_selected_accounts(self, rows: list[int]) -> None:
        accounts = [account for row in rows if (account := self._model.account_at(row)) is not None]
        if not accounts:
            self._window.show_error("修复失败", "请先选择至少一个账号。")
            return

        config = self._window.version_config()
        previews: list[tuple[str, XmlRepairPreview]] = []
        try:
            for account in accounts:
                previews.append((account.name, self._restore_service.preview_repair(account.path, config)))
        except Exception as exc:  # noqa: BLE001 - surface preview errors in GUI
            self._window.show_error("预览失败", str(exc))
            return

        if not self._window.confirm_batch_repair_preview(previews):
            self._window.set_status("已取消 XML 修复。")
            return

        try:
            for account in accounts:
                self._restore_service.repair_account_xml(account.path, config)
        except Exception as exc:  # noqa: BLE001 - surface repair errors in GUI
            self._window.show_error("修复失败", str(exc))
            return

        self._window.show_info("修复完成", f"已修复 {len(accounts)} 个账号的 XML。")
