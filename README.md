# Read My Paper

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/8dcb98d9-b9f6-4778-bc8b-0f85e5602059"
    alt="Read My Paper menu"
    width="750"
  />
</p>

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/bb2fcf07-7ec1-4443-b5c9-65af98864543"
    alt="Read My Paper voice selection"
    width="750"
  />
</p>

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/10bf03d3-2129-4164-a4ae-a3189f5b791e"
    alt="Read My Paper playback interface"
    width="750"
  />
</p>


Read research papers aloud, locally, with custom voice.


## Quick Start

```bash
uv sync
uv run rmp
```

Use arrow keys and Enter to add a paper, add a voice, or play a paper.

## Commands

```bash
uv run rmp paper add papers/paper.pdf
uv run rmp voice add audio/voice.wav
uv run rmp play paper --voice voice
```

## Voice cloning
Add a `.wav` clip into /audio. Then you can use the cli to convert it into safetensors.

## Adding a paper
Add a pdf under `\papers` (create a folder in the root). Then use the cli to convert it into something readable. This might take a while and it is not perfect.

## Clip a Voice Sample

```bash
uv run python scripts/clip_wav.py audio/egf.wav audio/egf_5s.wav --start 0 --end 5
```

Use any seconds for `--start` and `--end`.

## While Playing

- `Space`: pause/resume
- `Left` / `Right`: back/forward 5 seconds
- `q`: quit

```bash
uv run rmp --help
uv run rmp paper list
uv run rmp voice list
```

## License
Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
