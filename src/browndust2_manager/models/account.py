from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Account:
    """A scanned account backup directory."""

    name: str
    path: Path
    modified_at: datetime
    has_shared_prefs: bool
