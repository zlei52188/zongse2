from __future__ import annotations

from datetime import datetime
from pathlib import Path


class LogService:
    """按天保存错误、ADB、恢复和 XML 日志。"""

    def __init__(self, log_dir: Path = Path("logs")) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def write(self, category: str, message: str) -> Path:
        """写入一条分类日志。"""
        today = datetime.now().strftime("%Y-%m-%d")
        path = self.log_dir / f"{today}.log"
        line = f"{datetime.now().isoformat(timespec='seconds')} [{category}] {message}\n"
        path.write_text(path.read_text(encoding="utf-8") + line if path.exists() else line, encoding="utf-8")
        return path

    def search(self, keyword: str) -> list[str]:
        """搜索所有日志文件。"""
        result: list[str] = []
        for path in sorted(self.log_dir.glob("*.log")):
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if keyword.casefold() in line.casefold():
                    result.append(f"{path.name}: {line}")
        return result
