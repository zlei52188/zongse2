from __future__ import annotations

from pathlib import Path

from browndust2_manager.services.root_service import EmulatorConfig, ProgressCallback, RootService


class RestoreService:
    """Coordinates rooted restore for a configured emulator slot."""

    def __init__(self, root_service: RootService | None = None) -> None:
        self._root_service = root_service or RootService()

    def restore_account(
        self,
        account_path: Path,
        config: EmulatorConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self._root_service.restore_account(account_path, config, progress_callback)


def restore_account(account_path: Path, emulator_id: int) -> None:
    """Compatibility validator for older integrations and tests."""
    if emulator_id not in {1, 2, 3, 4}:
        raise ValueError("emulator_id 必须是 1~4")
    if not account_path.exists() or not account_path.is_dir():
        raise FileNotFoundError(f"账号目录不存在：{account_path}")
