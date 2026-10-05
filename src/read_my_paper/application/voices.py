from __future__ import annotations

from pathlib import Path

from read_my_paper.domain.errors import ReadMyPaperError
from read_my_paper.domain.models import VoiceProfile
from read_my_paper.infrastructure.pocket_tts import export_voice_profile
from read_my_paper.infrastructure.voice_store import VoiceStore


class VoiceService:
    def __init__(self, store: VoiceStore | None = None) -> None:
        self.store = store or VoiceStore()

    def add(self, audio: Path, name: str | None = None, replace: bool = False) -> VoiceProfile:
        audio = audio.expanduser().resolve()
        profile = self.store.prepare_destination(name or audio.stem, replace)
        try:
            export_voice_profile(audio, profile.path)
        except ValueError as error:
            raise ReadMyPaperError(str(error)) from error
        return profile

    def get(self, voice_id: str) -> VoiceProfile:
        return self.store.get(voice_id)

    def list(self) -> list[VoiceProfile]:
        return self.store.list()
