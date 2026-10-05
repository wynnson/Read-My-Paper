"""Copy a time range from a WAV file."""

from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source WAV file")
    parser.add_argument("output", type=Path, help="Clipped WAV file")
    parser.add_argument("--start", type=float, required=True, help="Start time in seconds")
    parser.add_argument("--end", type=float, required=True, help="End time in seconds")
    args = parser.parse_args()

    if args.start < 0 or args.end <= args.start:
        parser.error("--end must be greater than --start, and --start must be non-negative.")
    if not args.input.is_file() or args.input.suffix.lower() != ".wav":
        parser.error("input must be an existing WAV file.")

    with sf.SoundFile(args.input) as source:
        start_frame = int(args.start * source.samplerate)
        end_frame = min(int(args.end * source.samplerate), len(source))
        if start_frame >= len(source):
            parser.error("--start is past the end of the input file.")
        source.seek(start_frame)
        audio = source.read(end_frame - start_frame)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(args.output, audio, source.samplerate, subtype=source.subtype)

    print(f"Wrote {args.output} ({args.start:.2f}s to {args.end:.2f}s)")


if __name__ == "__main__":
    main()
