from __future__ import annotations

from pathlib import Path

from browndust2_manager.services.xml_repair_service import XmlRepairPreview, XmlRepairService, XmlVersionConfig


class RestoreService:
    """Coordinates repairing XML and restoring an account to an emulator slot."""

    def __init__(self, xml_repair_service: XmlRepairService | None = None) -> None:
        self._xml_repair_service = xml_repair_service or XmlRepairService()

    def preview_repair(self, account_path: Path, config: XmlVersionConfig) -> XmlRepairPreview:
        return self._xml_repair_service.preview_account(account_path, config)

    def repair_account_xml(self, account_path: Path, config: XmlVersionConfig) -> XmlRepairPreview:
        return self._xml_repair_service.repair_account(account_path, config)

    def restore_account(self, account_path: Path, emulator_id: int, config: XmlVersionConfig) -> XmlRepairPreview:
        preview = self.repair_account_xml(account_path, config)
        restore_account(account_path, emulator_id)
        return preview


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
