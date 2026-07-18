from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from browndust2_manager.models.account import Account


class AccountRepository:
    """负责 accounts.db 中账号表的读写。"""

    def __init__(self, db_path: Path = Path("accounts.db")) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    folder_path TEXT NOT NULL UNIQUE,
                    unity_cloud_userid TEXT NOT NULL DEFAULT '',
                    game_data_version TEXT NOT NULL DEFAULT '',
                    bundle_version TEXT NOT NULL DEFAULT '',
                    BuildPlayerVersion TEXT NOT NULL DEFAULT '',
                    last_restore_time TEXT,
                    favorite INTEGER NOT NULL DEFAULT 0,
                    remark TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '正常',
                    restore_count INTEGER NOT NULL DEFAULT 0,
                    color_label TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert_scanned_account(self, account: Account) -> Account:
        """扫描账号时同步新增或更新账号记录。"""
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO accounts (
                    account_name, folder_path, unity_cloud_userid, game_data_version,
                    bundle_version, BuildPlayerVersion, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(folder_path) DO UPDATE SET
                    account_name=excluded.account_name,
                    unity_cloud_userid=excluded.unity_cloud_userid,
                    game_data_version=excluded.game_data_version,
                    bundle_version=excluded.bundle_version,
                    BuildPlayerVersion=excluded.BuildPlayerVersion,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (
                    account.account_name,
                    str(account.folder_path),
                    account.unity_cloud_userid,
                    account.game_data_version,
                    account.bundle_version,
                    account.build_player_version,
                    account.status,
                    now,
                    now,
                ),
            )
            connection.commit()
        return self.get_by_path(account.folder_path) or account

    def list_accounts(self) -> list[Account]:
        """返回全部账号。"""
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM accounts ORDER BY lower(account_name)").fetchall()
        return [self._row_to_account(row) for row in rows]

    def get_by_path(self, path: Path) -> Account | None:
        """根据目录路径读取账号。"""
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM accounts WHERE folder_path = ?", (str(path),)).fetchone()
        return self._row_to_account(row) if row else None

    def set_favorite(self, account_id: int, favorite: bool) -> None:
        """更新收藏状态。"""
        self._update(account_id, favorite=int(favorite))

    def set_remark(self, account_id: int, remark: str) -> None:
        """更新备注。"""
        self._update(account_id, remark=remark)

    def set_color_label(self, account_id: int, color_label: str) -> None:
        """更新颜色标签。"""
        self._update(account_id, color_label=color_label)

    def record_restore(self, account_id: int) -> None:
        """增加恢复次数并记录最后恢复时间。"""
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                "UPDATE accounts SET restore_count = restore_count + 1, last_restore_time = ?, updated_at = ? WHERE id = ?",
                (now, now, account_id),
            )
            connection.commit()

    def _update(self, account_id: int, **fields: object) -> None:
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = [*fields.values(), datetime.now().isoformat(timespec="seconds"), account_id]
        with self._connect() as connection:
            connection.execute(f"UPDATE accounts SET {assignments}, updated_at = ? WHERE id = ?", values)
            connection.commit()

    def _row_to_account(self, row: sqlite3.Row) -> Account:
        def parse(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value) if value else None
        path = Path(row["folder_path"])
        modified = datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else parse(row["updated_at"]) or datetime.now()
        return Account(
            id=row["id"], account_name=row["account_name"], folder_path=path, modified_at=modified,
            unity_cloud_userid=row["unity_cloud_userid"], game_data_version=row["game_data_version"],
            bundle_version=row["bundle_version"], build_player_version=row["BuildPlayerVersion"],
            last_restore_time=parse(row["last_restore_time"]), favorite=bool(row["favorite"]),
            remark=row["remark"], status=row["status"], restore_count=row["restore_count"],
            color_label=row["color_label"], created_at=parse(row["created_at"]), updated_at=parse(row["updated_at"]),
        )
