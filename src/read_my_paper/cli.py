from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path

import typer
from rich.live import Live
from rich.panel import Panel

from read_my_paper.application.papers import PaperService
from read_my_paper.application.playback import play_text
from read_my_paper.application.voices import VoiceService
from read_my_paper.domain.errors import ReadMyPaperError
from read_my_paper.domain.models import PlaybackResult
from read_my_paper.ui import (
    activity,
    collection_panel,
    console,
    error,
    note,
    papers_table,
    playback_panel,
    success,
    title,
    voices_table,
)


papers = PaperService()
voices = VoiceService()

app = typer.Typer(
    invoke_without_command=True,
    help="[title]rmp[/title]  a tiny local paper reader\n[muted]read softly. keep moving.[/muted]",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)
paper_app = typer.Typer(no_args_is_help=True, help="Add, inspect, and manage papers.")
voice_app = typer.Typer(no_args_is_help=True, help="Create and inspect cloned voices.")
app.add_typer(paper_app, name="paper")
app.add_typer(voice_app, name="voice")


def add_paper(pdf: Path, replace: bool = False) -> None:
    title("paper add")
    with console.status(activity("paper", "reading pages and arranging columns...")):
        manifest = papers.add(pdf, replace=replace)
    success("paper", f"added {manifest.id} from {manifest.source_name}")
    note("paper", f"{len(manifest.blocks)} narration blocks | skipped {manifest.skipped}")


def add_voice(audio: Path, name: str | None = None, replace: bool = False) -> None:
    title("voice add")
    with console.status(activity("voice", "learning this voice...")):
        profile = voices.add(audio, name=name, replace=replace)
    success("voice", f"{profile.id} is ready")
    note("voice", str(profile.path))


def play_paper(paper_id: str, voice_id: str, from_block: int = 0, output: Path | None = None) -> None:
    text = papers.text(paper_id, from_block)
    profile = voices.get(voice_id)
    output = output or papers.new_recording_path(paper_id)
    title("now reading")

    def panel(state: str) -> Panel:
        return playback_panel(paper_id, profile.id, state, output)

    if console.is_terminal:
        with Live(panel("warming up"), console=console, transient=True) as live:
            result = play_text(text, profile.path, output, lambda state: live.update(panel(state)))
    else:
        note("play", f"playing {paper_id} with {profile.id}; writing {output}")
        result = play_text(text, profile.path, output)

    _report_recording(result)


def _report_recording(result: PlaybackResult) -> None:
    if result.cancelled and result.output_path.is_file() and console.is_terminal:
        import questionary

        if questionary.confirm("Delete the saved recording?", default=False, qmark="rmp").ask():
            result.output_path.unlink()
            success("play", "recording deleted")
            return

    label = "saved" if result.completed else "saved partial"
    success("play", f"{label} {result.output_path}")


def run_command(workflow: Callable[[], None]) -> None:
    """Surface user-facing errors as Typer parameter errors."""
    try:
        workflow()
    except ReadMyPaperError as failure:
        raise typer.BadParameter(str(failure)) from failure


MENU_BACK = "__rmp_back__"
MENU_STYLE = [
    ("qmark", "fg:#d98aac bold"),
    ("question", "fg:#8ecae6 bold"),
    ("pointer", "fg:#d98aac bold"),
    ("highlighted", "fg:#f6d365 bold"),
    ("selected", "fg:#9dd9c2"),
    ("instruction", "fg:#c4b5fd"),
]


def _menu_select(prompt: str, choices: list[str], allow_back: bool = False) -> str | None:
    import questionary
    from prompt_toolkit.keys import Keys

    question = questionary.select(
        prompt,
        choices=choices,
        qmark="rmp",
        style=questionary.Style(MENU_STYLE),
        instruction="Left arrow: back" if allow_back else None,
    )

    if allow_back:
        @question.application.key_bindings.add(Keys.Left, eager=True)
        def go_back(event) -> None:
            event.app.exit(result=MENU_BACK)

    answer = question.ask()
    return None if answer == MENU_BACK else answer


def _menu_path(prompt: str, default: str) -> Path | None:
    import questionary

    answer = questionary.text(prompt, default=default).ask()
    return Path(answer) if answer else None


def _menu_add_paper() -> None:
    if source := _menu_path("PDF path:", "papers/"):
        add_paper(source)


def _menu_add_voice() -> None:
    if source := _menu_path("Audio path:", "audio/"):
        add_voice(source)


def _menu_play() -> None:
    paper_options, voice_options = papers.list(), voices.list()
    if not paper_options or not voice_options:
        note("menu", "add a paper and voice first")
        return

    paper_id = _menu_select("paper:", [paper.id for paper in paper_options], allow_back=True)
    if paper_id is None:
        return

    voice_id = _menu_select("voice:", [profile.id for profile in voice_options], allow_back=True)
    if voice_id is not None:
        play_paper(paper_id, voice_id)


MENU_ACTIONS: dict[str, Callable[[], None]] = {
    "Add a paper": _menu_add_paper,
    "Add a voice": _menu_add_voice,
    "Play a paper": _menu_play,
}


def run_menu() -> None:
    title("rmp")

    while True:
        choice = _menu_select("what would you like to do?", [*MENU_ACTIONS, "Quit"])
        action = MENU_ACTIONS.get(choice or "")
        if action is None:
            return

        try:
            action()
        except ReadMyPaperError as failure:
            error(str(failure))


@app.callback()
def app_callback(context: typer.Context, show_version: bool = typer.Option(False, "--version")) -> None:
    if show_version:
        console.print(f"[title]rmp[/title] {version('read-my-paper')}")
        raise typer.Exit()
    if context.invoked_subcommand is None:
        if console.is_terminal:
            run_menu()
        else:
            console.print(context.get_help())
        raise typer.Exit()


@app.command("menu")
def menu_command() -> None:
    """Open the interactive paper and voice selector."""
    run_menu()


@app.command("play")
def play_command(paper_id: str, voice: str = typer.Option(..., "--voice", "-v"),
                 from_block: int = typer.Option(0, min=0), output: Path | None = None) -> None:
    """Play a paper with interactive pause and seek controls."""
    run_command(lambda: play_paper(paper_id, voice, from_block, output))


@paper_app.command("add")
def paper_add(pdf: Path, replace: bool = typer.Option(False, "--replace")) -> None:
    """Add a PDF, extract its narrative text, and store it locally."""
    run_command(lambda: add_paper(pdf, replace))


@paper_app.command("list")
def paper_list() -> None:
    """List imported papers."""
    manifests = papers.list()
    title("paper shelf")
    if not manifests:
        note("paper", "no papers yet. Try: rmp paper add papers/paper.pdf")
        return
    console.print(collection_panel(papers_table(manifests), "paper"))


@paper_app.command("text")
def paper_text(paper_id: str) -> None:
    """Print narration text."""
    run_command(lambda: typer.echo(papers.text(paper_id)))


@voice_app.command("add")
def voice_add(audio: Path, name: str | None = typer.Option(None, "--name", "-n"),
              replace: bool = typer.Option(False, "--replace")) -> None:
    """Create a reusable cloned-voice profile."""
    run_command(lambda: add_voice(audio, name, replace))


@voice_app.command("list")
def voice_list() -> None:
    """List cloned voice profiles."""
    profiles = voices.list()
    title("voice closet")
    if not profiles:
        note("voice", "no voices yet. Try: rmp voice add audio/voice.wav")
        return
    console.print(collection_panel(voices_table(profiles), "voice"))
