from __future__ import annotations

import re
from pathlib import Path

from read_my_paper.domain.errors import InvalidVoiceId, VoiceAlreadyExists, VoiceNotFound
from read_my_paper.domain.models import VoiceProfile
from read_my_paper.infrastructure.paths import voices_root


PROFILE_SUFFIX = ".safetensors"


def voice_id_from_name(name: str) -> str:
    """Slug a voice name; underscores are kept so existing profiles like `ah_voice` stay addressable."""
    voice_id = re.sub(r"[^a-z0-9_]+", "-", name.casefold()).strip("-_")
    if not voice_id:
        raise InvalidVoiceId("Voice name must contain letters or numbers.")
    return voice_id


class VoiceStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or voices_root()
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, voice_id: str) -> VoiceProfile:
        profile = self._profile(voice_id)
        if not profile.path.is_file():
            raise VoiceNotFound(f"Voice profile not found: {voice_id}")
        return profile

    def list(self) -> list[VoiceProfile]:
        return [VoiceProfile(path.stem, path) for path in sorted(self.root.glob(f"*{PROFILE_SUFFIX}"))]

    def prepare_destination(self, voice_id: str, replace: bool) -> VoiceProfile:
        profile = self._profile(voice_id)
        if profile.path.exists() and not replace:
            raise VoiceAlreadyExists(f"A voice named '{profile.id}' already exists. Use --replace to overwrite it.")
        return profile

    def _profile(self, voice_id: str) -> VoiceProfile:
        voice_id = voice_id_from_name(voice_id)
        return VoiceProfile(voice_id, self.root / f"{voice_id}{PROFILE_SUFFIX}")
