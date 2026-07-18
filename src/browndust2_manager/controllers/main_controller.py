from __future__ import annotations

from pathlib import Path

from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.models.emulator_config_model import EmulatorConfigModel
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.restore_service import RestoreService
from browndust2_manager.services.root_service import RootService
from browndust2_manager.views.main_window import MainWindow


class MainController:
    """Connects models, PySide6 view, and root restore services."""

    def __init__(
        self,
        model: AccountListModel,
        emulator_model: EmulatorConfigModel,
        scanner: AccountScanner,
        root_service: RootService,
        restore_service: RestoreService,
        window: MainWindow,
    ) -> None:
        self._model = model
        self._emulator_model = emulator_model
        self._scanner = scanner
        self._root_service = root_service
        self._restore_service = restore_service
        self._window = window
        self._accounts_dir: Path = scanner.default_accounts_dir()
        self._root_service.set_log_callback(self._window.append_log)

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

    def refresh_devices(self) -> None:
        try:
            devices = self._root_service.list_devices()
        except Exception as exc:  # noqa: BLE001
            self._window.show_error("刷新设备失败", str(exc))
            return
        self._window.set_devices(devices)
        self._window.set_status(f"已识别 {len(devices)} 个设备。")

    def connect_emulators(self) -> None:
        for config in self._emulator_model.configs:
            if config.serial.strip():
                self._root_service.connect_emulator(config.serial)
        self.refresh_devices()

    def check_selected_root(self) -> None:
        config = self._emulator_model.config_for_slot(self._window.selected_emulator_slot())
        if not config.serial.strip():
            self._window.show_error("检测Root失败", "请先填写选中模拟器的 adb serial。")
            return
        rooted = self._root_service.check_root(config.serial)
        self._window.show_info("Root状态", f"{config.name or config.serial}：{'已Root' if rooted else '未Root'}")

    def restore_selected_account(self, row: int, emulator_id: int) -> None:
        account = self._model.account_at(row)
        if account is None:
            self._window.show_error("恢复失败", "未找到选中的账号。")
            return
        config = self._emulator_model.config_for_slot(emulator_id)
        try:
            self._restore_service.restore_account(account.path, config, self._window.set_restore_progress)
        except Exception as exc:  # noqa: BLE001 - surface restore errors in GUI
            self._window.show_error("恢复失败", str(exc))
            return

        self._window.show_info("恢复完成", f"账号 {account.name} 已恢复到 {config.name or emulator_id}。")
