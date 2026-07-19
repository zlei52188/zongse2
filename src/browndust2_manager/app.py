from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from browndust2_manager.controllers.main_controller import MainController
from browndust2_manager.models.account_list_model import AccountListModel
from browndust2_manager.repositories.account_repository import AccountRepository
from browndust2_manager.services.account_scanner import AccountScanner
from browndust2_manager.services.account_service import AccountService
from browndust2_manager.services.restore_service import RestoreService
from browndust2_manager.views.main_window import MainWindow


def main() -> int:
    """Start the BrownDust2Manager desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("BrownDust2Manager")

    model = AccountListModel()
    scanner = AccountScanner()
    account_repository = AccountRepository()
    account_service = AccountService(scanner, account_repository)
    restore_service = RestoreService()
    window = MainWindow(model=model)
    controller = MainController(
        model=model,
        account_service=account_service,
        restore_service=restore_service,
        window=window,
    )
    window.set_controller(controller)
    window.show()

    controller.load_default_accounts()
    return app.exec()
