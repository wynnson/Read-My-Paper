from __future__ import annotations

import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def data_root() -> Path:
    path = Path(os.environ.get("RMP_DATA_DIR", REPOSITORY_ROOT / "data")).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def papers_root() -> Path:
    path = data_root() / "papers"
    path.mkdir(exist_ok=True)
    return path


def voices_root() -> Path:
    path = data_root() / "voices"
    path.mkdir(exist_ok=True)
    return path
