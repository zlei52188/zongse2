from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BackupInfo:
    path: Path
    created_at: datetime


class BackupService:
    """Manages shared_prefs backups before restore."""

    def __init__(self, backup_root: Path | None = None) -> None:
        self.backup_root = backup_root or Path.cwd() / "backup"

    def create_backup(self, shared_prefs: Path, created_at: datetime | None = None) -> Path:
        if not shared_prefs.exists() or not shared_prefs.is_dir():
            raise FileNotFoundError(f"shared_prefs 目录不存在：{shared_prefs}")
        stamp = (created_at or datetime.now()).strftime("%Y%m%d_%H%M%S")
        destination = self.backup_root / stamp
        suffix = 1
        while destination.exists():
            destination = self.backup_root / f"{stamp}_{suffix}"
            suffix += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(shared_prefs, destination)
        return destination

    def list_backups(self) -> list[BackupInfo]:
        if not self.backup_root.exists():
            return []
        backups = []
        for child in self.backup_root.iterdir():
            if child.is_dir():
                backups.append(BackupInfo(child, datetime.fromtimestamp(child.stat().st_mtime)))
        return sorted(backups, key=lambda item: item.created_at, reverse=True)

    def restore_backup(self, backup_path: Path, target_shared_prefs: Path) -> None:
        if not backup_path.exists() or not backup_path.is_dir():
            raise FileNotFoundError(f"备份不存在：{backup_path}")
        if target_shared_prefs.exists():
            shutil.rmtree(target_shared_prefs)
        shutil.copytree(backup_path, target_shared_prefs)

    def delete_backup(self, backup_path: Path) -> None:
        if backup_path.exists():
            shutil.rmtree(backup_path)
