from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable
from pathlib import Path

LogCallback = Callable[[str], None]


class RestoreService:
    """Coordinates restoring account shared preferences to emulator data dirs."""

    CONFIG_ENV_NAME = "BROWNDUST2_MANAGER_CONFIG"
    DEFAULT_GAME_DATA_DIR = Path("/data/data/com.neowizgames.game.browndust2")

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or self.default_config_path()
        self._emulator_dirs: dict[int, Path] = {
            slot: self.DEFAULT_GAME_DATA_DIR for slot in range(1, 5)
        }
        self.load_config()

    @classmethod
    def default_config_path(cls) -> Path:
        configured = os.environ.get(cls.CONFIG_ENV_NAME)
        if configured:
            return Path(configured).expanduser()
        return Path.home() / ".config" / "BrownDust2Manager" / "settings.json"

    def emulator_dirs(self) -> dict[int, Path]:
        return dict(self._emulator_dirs)

    def set_emulator_dirs(self, emulator_dirs: dict[int, Path]) -> None:
        normalized: dict[int, Path] = {}
        for slot in range(1, 5):
            path = emulator_dirs.get(slot)
            if path is None:
                raise ValueError(f"缺少模拟器 {slot} 的数据目录配置。")
            normalized[slot] = Path(path).expanduser()
        self._emulator_dirs = normalized

    def load_config(self) -> None:
        if not self._config_path.exists():
            return
        data = json.loads(self._config_path.read_text(encoding="utf-8"))
        configured_dirs = data.get("emulator_dirs", {})
        for key, value in configured_dirs.items():
            slot = int(key)
            if slot in {1, 2, 3, 4}:
                self._emulator_dirs[slot] = Path(value).expanduser()

    def save_config(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "emulator_dirs": {
                str(slot): str(path)
                for slot, path in sorted(self._emulator_dirs.items())
            }
        }
        self._config_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def restore_account(
        self,
        account_path: Path,
        emulator_id: int,
        log_callback: LogCallback | None = None,
    ) -> None:
        restore_account(
            account_path,
            emulator_id,
            self._emulator_dirs,
            log_callback=log_callback,
        )


def restore_account(
    account_path: Path,
    emulator_id: int,
    emulator_dirs: dict[int, Path] | None = None,
    log_callback: LogCallback | None = None,
) -> None:
    """Restore an account backup shared_prefs directory to emulator 1~4."""
    if emulator_id not in {1, 2, 3, 4}:
        raise ValueError("emulator_id 必须是 1~4")

    account_path = account_path.expanduser()
    if not account_path.exists() or not account_path.is_dir():
        raise FileNotFoundError(f"账号目录不存在：{account_path}")

    source_shared_prefs = account_path / "shared_prefs"
    if not source_shared_prefs.exists() or not source_shared_prefs.is_dir():
        raise FileNotFoundError(f"账号 shared_prefs 不存在：{source_shared_prefs}")

    configured_dirs = emulator_dirs or {
        slot: RestoreService.DEFAULT_GAME_DATA_DIR for slot in range(1, 5)
    }
    target_data_dir = configured_dirs.get(emulator_id)
    if target_data_dir is None:
        raise ValueError(f"未配置模拟器 {emulator_id} 的数据目录。")

    target_data_dir = target_data_dir.expanduser()
    if not target_data_dir.exists() or not target_data_dir.is_dir():
        raise FileNotFoundError(f"模拟器数据目录不存在：{target_data_dir}")

    target_shared_prefs = target_data_dir / "shared_prefs"

    _log(log_callback, "正在删除……")
    if target_shared_prefs.exists():
        if not target_shared_prefs.is_dir():
            raise NotADirectoryError(
                f"目标 shared_prefs 不是文件夹：{target_shared_prefs}"
            )
        shutil.rmtree(target_shared_prefs)

    _log(log_callback, "正在复制……")
    shutil.copytree(
        source_shared_prefs, target_shared_prefs, copy_function=shutil.copy2
    )

    _refresh_directory(target_data_dir)
    _log(log_callback, "恢复完成")


def _log(log_callback: LogCallback | None, message: str) -> None:
    if log_callback is not None:
        log_callback(message)


def _refresh_directory(path: Path) -> None:
    # Force a directory enumeration so callers and file managers see the new tree promptly.
    list(path.iterdir())
    sync = getattr(os, "sync", None)
    if sync is not None:
        sync()
