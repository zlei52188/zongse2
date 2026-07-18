from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.restore_service import RestoreService
from browndust2_manager.views.main_window import MainWindow


class MainController:
    """Connects the model, PySide6 view, and account services."""

    def __init__(self, model: AccountListModel, scanner: AccountScanner, restore_service: RestoreService, window: MainWindow) -> None:
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
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("扫描失败", str(exc))
            return
        self._model.set_accounts(accounts)
        self._window.set_status(f"已扫描 {len(accounts)} 个账号。")

    def restore_selected_account(self, row: int, emulator_id: int) -> None:
        account = self._model.account_at(row)
        if account:
            self._restore_accounts([account.path], emulator_id)

    def restore_selected_accounts(self, emulator_id: int) -> None:
        accounts = self._selected_accounts()
        if not accounts:
            self._window.show_error("恢复失败", "未选择账号。")
            return
        self._restore_accounts([account.path for account in accounts], emulator_id)

    def _restore_accounts(self, account_paths: list[Path], emulator_id: int) -> None:
        try:
            for account_path in account_paths:
                self._restore_service.restore_account(account_path, emulator_id)
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("恢复失败", str(exc))
            return
        self._window.show_info("恢复完成", f"已恢复 {len(account_paths)} 个账号到 {emulator_id} 号模拟器。")

    def add_account(self) -> None:
        source = self._window.ask_account_dir()
        if source is None:
            return
        target = self._accounts_dir / source.name
        try:
            if target.exists():
                raise FileExistsError(f"账号已存在：{target}")
            shutil.copytree(source, target)
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("添加失败", str(exc))
            return
        self.refresh_accounts()

    def import_zip(self) -> None:
        zip_path = self._window.ask_open_zip()
        if zip_path is None:
            return
        try:
            self._accounts_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(self._accounts_dir)
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("导入失败", str(exc))
            return
        self.refresh_accounts()

    def export_selected_accounts(self) -> None:
        accounts = self._selected_accounts()
        if not accounts:
            self._window.show_error("导出失败", "未选择账号。")
            return
        target = self._window.ask_save_zip(f"{accounts[0].name}.zip" if len(accounts) == 1 else "BrownDust2Accounts.zip")
        if target is None:
            return
        try:
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
                for account in accounts:
                    for file in account.path.rglob("*"):
                        if file.is_file():
                            archive.write(file, Path(account.name) / file.relative_to(account.path))
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("导出失败", str(exc))
            return
        self._window.set_status(f"已导出 {len(accounts)} 个账号到 {target}")

    def open_selected_account_dir(self) -> None:
        account = self._first_selected_account()
        if account is None:
            return
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", str(account.path)])  # noqa: S603,S607
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(account.path)])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", str(account.path)])  # noqa: S603,S607

    def delete_selected_accounts(self) -> None:
        accounts = self._selected_accounts()
        if not accounts or not self._window.confirm("删除账号", f"确定删除 {len(accounts)} 个账号？"):
            return
        try:
            for account in accounts:
                shutil.rmtree(account.path)
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("删除失败", str(exc))
            return
        self.refresh_accounts()

    def rename_selected_account(self) -> None:
        account = self._first_selected_account()
        if account is None:
            return
        new_name = self._window.ask_text("重命名账号", "新账号名称：", account.name)
        if new_name is None:
            return
        try:
            account.path.rename(account.path.with_name(new_name.strip()))
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("重命名失败", str(exc))
            return
        self.refresh_accounts()

    def _selected_accounts(self):
        return [account for row in self._window.selected_source_rows() if (account := self._model.account_at(row)) is not None]

    def _first_selected_account(self):
        accounts = self._selected_accounts()
        return accounts[0] if accounts else None
