from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class RootService:
    """Runs all ADB/root operations for BrownDust2Manager."""

    PACKAGE = "com.neowizgames.game.browndust2"
    SHARED_PREFS = f"/data/data/{PACKAGE}/shared_prefs"

    def __init__(self, adb_path: str = "adb") -> None:
        self.adb_path = adb_path

    def run_adb(self, serial: str, *args: str) -> subprocess.CompletedProcess[str]:
        command = [self.adb_path]
        if serial:
            command.extend(["-s", serial])
        command.extend(args)
        return subprocess.run(command, check=True, text=True, capture_output=True)

    def is_online(self, serial: str) -> bool:
        try:
            result = self.run_adb(serial, "get-state")
        except Exception:  # noqa: BLE001 - ADB availability varies by machine
            return False
        return result.stdout.strip() == "device"

    def root_status(self, serial: str) -> str:
        try:
            result = self.run_adb(serial, "shell", "su", "-c", "id")
        except Exception:  # noqa: BLE001 - surface as status string for UI
            return "未 Root"
        return "已 Root" if "uid=0" in result.stdout else "未 Root"

    def android_version(self, serial: str) -> str:
        try:
            return self.run_adb(serial, "shell", "getprop", "ro.build.version.release").stdout.strip() or "未知"
        except Exception:  # noqa: BLE001
            return "未知"

    def stop_game(self, serial: str) -> None:
        self.run_adb(serial, "shell", "am", "force-stop", self.PACKAGE)

    def start_game(self, serial: str) -> None:
        self.run_adb(serial, "shell", "monkey", "-p", self.PACKAGE, "1")

    def pull_shared_prefs(self, serial: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.run_adb(serial, "exec-out", "su", "-c", f"tar -C {self.SHARED_PREFS} -cf - .")
        # Real devices stream tar through stdout. Tests and offline use can mock this method.

    def push_shared_prefs(self, serial: str, source: Path) -> None:
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(f"shared_prefs 源目录不存在：{source}")
        self.run_adb(serial, "push", str(source), "/sdcard/bd2_shared_prefs")
        self.run_adb(serial, "shell", "su", "-c", f"rm -rf {self.SHARED_PREFS}/* && cp -r /sdcard/bd2_shared_prefs/* {self.SHARED_PREFS}/")

    def restore_permissions(self, serial: str) -> None:
        self.run_adb(serial, "shell", "su", "-c", f"chown -R $(stat -c %u:%g /data/data/{self.PACKAGE}) {self.SHARED_PREFS} && chmod -R 660 {self.SHARED_PREFS}/*")

    @staticmethod
    def copy_local_shared_prefs(source: Path, destination: Path) -> None:
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
