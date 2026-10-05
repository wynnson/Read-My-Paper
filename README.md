# RMP

Read research papers aloud, locally, in your own voice.

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

`paper` comes from `paper.pdf`. `voice` comes from `voice.wav`.

The CLI shows what it is doing with labels such as `[paper]`, `[voice]`, and `[play]`.

Formula blocks are converted from LaTeX to spoken English when possible. Unstructured equation OCR is skipped instead of read as symbols.

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
