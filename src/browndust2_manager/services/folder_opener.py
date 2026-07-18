from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class FolderOpener:
    """Opens account directories in the host file manager."""

    def open_folder(self, path: Path) -> None:
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"账号目录不存在：{path}")

        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return
        subprocess.Popen(["xdg-open", str(path)])
