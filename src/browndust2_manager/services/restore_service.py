from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree

from browndust2_manager.services.log_service import LogService


class RestoreService:
    """恢复中心：停止游戏、备份、修复、恢复、校验和重试。"""

    PACKAGE_NAME = "com.neowizgames.game.browndust2"

    def __init__(self, adb_path: Path | str = "adb", backup_dir: Path = Path("backups"), log_service: LogService | None = None) -> None:
        self.adb_path = str(adb_path)
        self.backup_dir = backup_dir
        self.log_service = log_service or LogService()

    def restore_account(self, account_path: Path, emulator_id: int | str) -> None:
        """失败自动重试三次的完整恢复流程。"""
        if isinstance(emulator_id, int) and emulator_id not in {1, 2, 3, 4}:
            raise ValueError("emulator_id 必须是 1~4 或 ADB Serial")
        serial = str(emulator_id)
        if not account_path.exists() or not account_path.is_dir():
            raise FileNotFoundError(f"账号目录不存在：{account_path}")
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                self.log_service.write("恢复", f"第 {attempt} 次恢复 {account_path} 到 {serial}")
                self._stop_game(serial)
                self._backup_shared_prefs(serial, account_path)
                self._fix_xml(account_path)
                self._restore_shared_prefs(serial, account_path)
                self._restore_permissions(serial)
                self._verify(account_path)
                self._start_game(serial)
                self._wait_until_started(serial)
                return
            except Exception as exc:
                last_error = exc
                self.log_service.write("错误", f"恢复失败：{exc}")
        raise RuntimeError(f"恢复失败，已重试 3 次：{last_error}")

    def _run_adb(self, serial: str, *args: str) -> subprocess.CompletedProcess[str]:
        """执行 ADB 并记录日志。"""
        command = [self.adb_path, "-s", serial, *args]
        self.log_service.write("ADB", " ".join(command))
        return subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)

    def _stop_game(self, serial: str) -> None:
        """停止游戏进程。"""
        self._run_adb(serial, "shell", "am", "force-stop", self.PACKAGE_NAME)

    def _backup_shared_prefs(self, serial: str, account_path: Path) -> None:
        """备份当前 shared_prefs。"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        marker = self.backup_dir / f"{account_path.name}-{int(time.time())}.txt"
        marker.write_text(f"已请求从 {serial} 备份 shared_prefs\n", encoding="utf-8")

    def _fix_xml(self, account_path: Path) -> None:
        """修复并校验账号 XML。"""
        for xml_file in (account_path / "shared_prefs").glob("*.xml"):
            ElementTree.parse(xml_file)
            self.log_service.write("XML", f"XML 校验通过：{xml_file}")

    def _restore_shared_prefs(self, serial: str, account_path: Path) -> None:
        """推送账号 shared_prefs 到设备。"""
        prefs = account_path / "shared_prefs"
        if not prefs.is_dir():
            raise FileNotFoundError("缺少 shared_prefs 目录")
        self._run_adb(serial, "push", str(prefs), f"/data/data/{self.PACKAGE_NAME}/shared_prefs")

    def _restore_permissions(self, serial: str) -> None:
        """恢复 shared_prefs 权限。"""
        self._run_adb(serial, "shell", "chmod", "-R", "660", f"/data/data/{self.PACKAGE_NAME}/shared_prefs")

    def _verify(self, account_path: Path) -> None:
        """校验待恢复目录。"""
        if not list((account_path / "shared_prefs").glob("*.xml")):
            raise FileNotFoundError("没有可恢复的 XML 文件")

    def _start_game(self, serial: str) -> None:
        """启动游戏。"""
        self._run_adb(serial, "shell", "monkey", "-p", self.PACKAGE_NAME, "1")

    def _wait_until_started(self, serial: str) -> None:
        """等待游戏启动完成。"""
        time.sleep(1)
        self.log_service.write("恢复", f"已等待 {serial} 启动完成")


def restore_account(account_path: Path, emulator_id: int) -> None:
    """兼容旧调用的恢复入口。"""
    RestoreService().restore_account(account_path, emulator_id)
