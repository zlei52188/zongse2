from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Account:
    """A scanned account backup directory with parsed BrownDust2 metadata."""

    name: str
    path: Path
    modified_at: datetime
    shared_prefs_path: Path | None = None
    player_prefs_path: Path | None = None
    shared_prefs_size: int = 0
    is_valid: bool = False
    build_player_version: str = ""
    game_data_version: str = ""
    bundle_version: str = ""
    unity_cloud_userid: str = ""
    firebase_user: str = ""
    file_count: int = 0
    directory_size: int = 0
