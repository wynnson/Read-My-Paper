from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NarrationBlock:
    index: int
    text: str
    label: str
    page: int | None


@dataclass
class PaperManifest:
    id: str
    source_name: str
    blocks: list[NarrationBlock]
    skipped: dict[str, int]


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    path: Path


@dataclass(frozen=True)
class PlaybackResult:
    completed: bool
    cancelled: bool
    output_path: Path
    underruns: int
