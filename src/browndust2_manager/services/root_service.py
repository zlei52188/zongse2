from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PACKAGE_NAME = "com.neowizgames.game.browndust2"
TMP_RESTORE_DIR = "/data/local/tmp/bd2_restore"
DEFAULT_ROOT_DIR = f"/data/data/{PACKAGE_NAME}"

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int], None]


@dataclass(slots=True)
class EmulatorConfig:
    """Persistent settings for one rooted Android emulator target."""

    slot: int
    name: str = ""
    serial: str = ""
    root_dir: str = DEFAULT_ROOT_DIR


@dataclass(slots=True)
class DeviceInfo:
    """ADB-discovered Android device or emulator state."""

    name: str
    serial: str
    state: str
    root_status: str = "未知"
    android_version: str = "未知"


@dataclass(slots=True)
class CommandResult:
    """Result of an adb or root shell command."""

    command: str
    stdout: str
    stderr: str
    returncode: int
    elapsed_ms: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class RootService:
    """Runs all BrownDust2 restore operations through ADB and root shell."""

    def __init__(self, adb_path: str | None = None, log_callback: LogCallback | None = None) -> None:
        self.adb_path = adb_path or shutil.which("adb") or "adb"
        self._log_callback = log_callback

    def set_log_callback(self, callback: LogCallback | None) -> None:
        self._log_callback = callback

    def list_devices(self) -> list[DeviceInfo]:
        result = self._run([self.adb_path, "devices"])
        if not result.ok:
            raise RuntimeError(result.stderr or result.stdout or "adb devices 执行失败")

        devices: list[DeviceInfo] = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            raw_state = parts[1] if len(parts) > 1 else "unknown"
            state = "online" if raw_state == "device" else raw_state
            device = DeviceInfo(name=serial, serial=serial, state=state)
            if raw_state == "device":
                device.name = self.device_name(serial)
                device.android_version = self.android_version(serial)
                device.root_status = "Root" if self.check_root(serial) else "未Root"
            devices.append(device)
        return devices

    def connect_emulator(self, serial: str) -> CommandResult:
        if not serial.strip():
            raise ValueError("adb serial 不能为空")
        return self._run([self.adb_path, "connect", serial.strip()])

    def device_name(self, serial: str) -> str:
        result = self._adb(serial, ["shell", "getprop", "ro.product.model"])
        return result.stdout.strip() or serial

    def android_version(self, serial: str) -> str:
        result = self._adb(serial, ["shell", "getprop", "ro.build.version.release"])
        return result.stdout.strip() or "未知"

    def check_root(self, serial: str) -> bool:
        result = self._root_shell(serial, "id")
        return result.ok and "uid=0" in result.stdout

    def restore_account(
        self,
        account_path: Path,
        config: EmulatorConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        if config.slot not in {1, 2, 3, 4}:
            raise ValueError("模拟器编号必须是 1~4")
        if not config.serial.strip():
            raise ValueError("请先配置 adb serial")
        if not config.root_dir.strip():
            raise ValueError("Root目录不能为空")
        if not account_path.exists() or not account_path.is_dir():
            raise FileNotFoundError(f"账号目录不存在：{account_path}")

        shared_prefs = account_path / "shared_prefs"
        if not shared_prefs.exists() or not shared_prefs.is_dir():
            raise FileNotFoundError(f"账号缺少 shared_prefs 目录：{shared_prefs}")

        serial = config.serial.strip()
        root_dir = config.root_dir.rstrip("/")
        self._emit_progress(progress_callback, 10)
        if not self.check_root(serial):
            raise PermissionError(f"设备 {serial} 未检测到 Root")

        self._must(self._adb(serial, ["shell", "am", "force-stop", PACKAGE_NAME]))
        self._must(self._root_shell(serial, f"rm -rf {self._q(root_dir)}/shared_prefs {self._q(TMP_RESTORE_DIR)}"))
        self._emit_progress(progress_callback, 30)

        self._must(self._adb(serial, ["push", str(shared_prefs), TMP_RESTORE_DIR]))
        self._emit_progress(progress_callback, 60)

        copy_cmd = f"cp -rf {self._q(TMP_RESTORE_DIR)} {self._q(root_dir)}/shared_prefs"
        self._must(self._root_shell(serial, copy_cmd))
        package_uid = self._package_uid(serial, root_dir)
        permission_cmd = (
            f"restorecon -R {self._q(root_dir)}/shared_prefs 2>/dev/null || true; "
            f"chown -R {package_uid}:{package_uid} {self._q(root_dir)}/shared_prefs; "
            f"chmod -R u+rwX,go-rwx {self._q(root_dir)}/shared_prefs"
        )
        self._must(self._root_shell(serial, permission_cmd))
        self._emit_progress(progress_callback, 90)

        self._must(self._root_shell(serial, "sync"))
        self._must(self._adb(serial, ["shell", "monkey", "-p", PACKAGE_NAME, "-c", "android.intent.category.LAUNCHER", "1"]))
        self._emit_progress(progress_callback, 100)

    def _package_uid(self, serial: str, root_dir: str) -> str:
        result = self._root_shell(serial, f"stat -c %U {self._q(root_dir)}")
        return result.stdout.strip() if result.ok and result.stdout.strip() else PACKAGE_NAME

    def _adb(self, serial: str, args: list[str]) -> CommandResult:
        return self._run([self.adb_path, "-s", serial, *args])

    def _root_shell(self, serial: str, command: str) -> CommandResult:
        return self._adb(serial, ["shell", "su", "-c", command])

    def _run(self, command: list[str]) -> CommandResult:
        started = time.perf_counter()
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        result = CommandResult(" ".join(command), completed.stdout, completed.stderr, completed.returncode, elapsed_ms)
        self._log(result)
        return result

    def _must(self, result: CommandResult) -> None:
        if not result.ok:
            raise RuntimeError(result.stderr or result.stdout or f"命令执行失败：{result.command}")

    def _log(self, result: CommandResult) -> None:
        if self._log_callback is None:
            return
        parts = [f"$ {result.command}", f"耗时：{result.elapsed_ms} ms", f"返回码：{result.returncode}"]
        if result.stdout:
            parts.append(f"输出：\n{result.stdout.rstrip()}")
        if result.stderr:
            parts.append(f"错误：\n{result.stderr.rstrip()}")
        self._log_callback("\n".join(parts))

    @staticmethod
    def _emit_progress(callback: ProgressCallback | None, value: int) -> None:
        if callback:
            callback(value)

    @staticmethod
    def _q(value: str) -> str:
        return "'" + value.replace("'", "'\\''") + "'"
