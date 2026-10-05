from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from read_my_paper.domain.models import PaperManifest, VoiceProfile


theme = Theme(
    {
        "accent": "#f3a6c2",
        "yellow": "#f6d365",
        "sky": "#8ecae6",
        "mint": "#9dd9c2",
        "lilac": "#c4b5fd",
        "soft": "#b7a8d5",
        "muted": "#978da8",
        "title": "bold #f7b2cf",
    }
)
console = Console(theme=theme, highlight=False, no_color=bool(os.environ.get("NO_COLOR")))
SCOPE_COLORS = {"paper": "sky", "voice": "mint", "play": "yellow", "error": "accent"}


def scope_color(scope: str) -> str:
    return SCOPE_COLORS.get(scope, "lilac")


def _scoped(scope: str, message: str, scope_style: str, message_style: str) -> Text:
    return Text.assemble(("[", "muted"), (scope, scope_style), ("] ", "muted"), (message, message_style))


def title(text: str) -> None:
    if console.is_terminal:
        console.print(Text(f"[{text}]", style="title"))


def activity(scope: str, message: str) -> Text:
    return _scoped(scope, message, scope_color(scope), "soft")


def success(scope: str, message: str) -> None:
    color = scope_color(scope)
    console.print(_scoped(scope, message, color, color))


def note(scope: str, message: str) -> None:
    console.print(_scoped(scope, message, "muted", "muted"))


def error(message: str) -> None:
    console.print(activity("error", message))


def collection_panel(content: Table, label: str) -> Panel:
    return Panel(
        content,
        title=Text(f"[{label}]", style=scope_color(label)),
        title_align="left",
        box=box.ROUNDED,
        border_style=scope_color(label),
        style="on #261f33",
        padding=(0, 1),
    )


def papers_table(papers: Iterable[PaperManifest]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, header_style="lilac", border_style="sky", show_edge=False)
    table.add_column("paper", style="sky")
    table.add_column("blocks", justify="right", style="yellow")
    table.add_column("source", style="mint")
    for paper in papers:
        table.add_row(paper.id, str(len(paper.blocks)), paper.source_name)
    return table


def voices_table(voices: Iterable[VoiceProfile]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, header_style="lilac", border_style="mint", show_edge=False)
    table.add_column("voice", style="mint")
    table.add_column("profile", style="sky")
    for voice in voices:
        table.add_row(voice.id, str(voice.path))
    return table


def playback_panel(paper_id: str, voice: str, state: str, output: Path) -> Panel:
    lines = Group(
        Text(f"[play] {state}  {paper_id}", style="title"),
        Text(f"voice: {voice}    recording: {output.name}", style="muted"),
        Text("Space pause  Left/Right seek 5s  q quit", style="soft"),
    )
    return Panel(
        lines,
        box=box.ROUNDED,
        border_style="yellow",
        style="on #2b2136",
        padding=(0, 1),
    )
