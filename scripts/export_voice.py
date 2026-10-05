"""Export a standalone Pocket TTS voice profile; it is not registered for playback."""

from __future__ import annotations

import argparse
from pathlib import Path

from read_my_paper.infrastructure.pocket_tts import export_voice_profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Reference audio to clone")
    parser.add_argument("output", type=Path, help="Output .safetensors profile")
    args = parser.parse_args()
    try:
        output = export_voice_profile(args.audio, args.output)
    except ValueError as error:
        parser.error(str(error))
    print(f"Standalone voice profile saved to {output}")
    print("For normal playback setup, run: uv run rmp voice add <audio-file>")


if __name__ == "__main__":
    main()
