from __future__ import annotations

from pathlib import Path


class RestoreService:
    """Coordinates restoring an account to a configured emulator slot."""

    def restore_account(self, account_path: Path, emulator_id: int) -> None:
        restore_account(account_path, emulator_id)


def restore_account(account_path: Path, emulator_id: int) -> None:
    """Restore an account backup to emulator 1~4.

    This function is intentionally reserved as the integration point for the
    real emulator restore implementation. Wire file-copy, ADB, or vendor CLI
    operations here when the emulator storage layout is finalized.
    """
    if emulator_id not in {1, 2, 3, 4}:
        raise ValueError("emulator_id 必须是 1~4")
    if not account_path.exists() or not account_path.is_dir():
        raise FileNotFoundError(f"账号目录不存在：{account_path}")
