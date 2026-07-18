from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Account:
    """账号备份目录及数据库元数据。"""

    id: int | None
    account_name: str
    folder_path: Path
    modified_at: datetime
    unity_cloud_userid: str = ""
    game_data_version: str = ""
    bundle_version: str = ""
    build_player_version: str = ""
    last_restore_time: datetime | None = None
    favorite: bool = False
    remark: str = ""
    status: str = "正常"
    restore_count: int = 0
    color_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def name(self) -> str:
        """兼容旧界面的账号名称。"""
        return self.account_name

    @property
    def path(self) -> Path:
        """兼容旧服务的账号目录。"""
        return self.folder_path
