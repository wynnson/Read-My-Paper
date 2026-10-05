from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from read_my_paper.domain.models import PlaybackResult
from read_my_paper.infrastructure.audio_player import PlaybackController


def play_text(text: str, voice: Path, output: Path, on_status: Callable[[str], None] | None = None) -> PlaybackResult:
    return PlaybackController(text, voice, output, on_status).run()
