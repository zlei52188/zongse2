from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    """应用设置。"""

    accounts_dir: str = ""
    adb_path: str = "adb"
    default_emulator: str = ""
    default_restore_mode: str = "标准恢复"
    game_data_version: str = ""
    bundle_version: str = ""
    BuildPlayerVersion: str = ""
    log_dir: str = "logs"
    backup_dir: str = "backups"
    auto_backup: bool = True
    auto_fix_xml: bool = True


class SettingsService:
    """设置读写服务。"""

    def __init__(self, path: Path = Path("settings.json")) -> None:
        self.path = path

    def load(self) -> AppSettings:
        """读取设置。"""
        if not self.path.exists():
            return AppSettings()
        return AppSettings(**json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, settings: AppSettings) -> None:
        """保存设置。"""
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
