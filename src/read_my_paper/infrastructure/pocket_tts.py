from __future__ import annotations

from pathlib import Path

from pocket_tts import TTSModel, export_model_state


def load_model() -> TTSModel:
    return TTSModel.load_model(language="english")


def export_voice_profile(audio_path: Path, destination: Path) -> Path:
    if not audio_path.is_file():
        raise ValueError(f"Audio file not found: {audio_path}")
    if destination.suffix != ".safetensors":
        raise ValueError("Voice profile destination must end in .safetensors.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    model = load_model()
    state = model.get_state_for_audio_prompt(str(audio_path))
    export_model_state(state, str(destination))
    return destination
