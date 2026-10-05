from __future__ import annotations

import os
import queue
import select
import sys
import termios
import threading
import time
import tty
from collections import deque
from collections.abc import Callable
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from pocket_tts import TTSModel

from read_my_paper.domain.errors import PlaybackFailed
from read_my_paper.domain.models import PlaybackResult
from read_my_paper.infrastructure.pocket_tts import load_model


StatusCallback = Callable[[str], None]
SEEK_SECONDS = 5
HISTORY_SECONDS = 30
KEY_COMMANDS = {ord(" "): "pause", ord("q"): "quit", ord("Q"): "quit"}
ARROW_COMMANDS = {b"\x1b[D": "back", b"\x1b[C": "forward"}


class _AudioHistory:
    """Rolling window of recently played samples, addressed by absolute sample position."""

    def __init__(self, max_samples: int) -> None:
        self.max_samples = max_samples
        self.chunks: deque[np.ndarray] = deque()
        self.samples = 0

    def remember(self, samples: np.ndarray) -> None:
        if len(samples):
            self.chunks.append(samples.copy())
            self.samples += len(samples)

        while self.chunks and self.samples > self.max_samples:
            self.samples -= len(self.chunks.popleft())

    def slice(self, start: int, end: int) -> np.ndarray:
        selected: list[np.ndarray] = []
        position = 0

        for chunk in self.chunks:
            chunk_end = position + len(chunk)
            if chunk_end > start and position < end:
                selected.append(chunk[max(0, start - position) : min(len(chunk), end - position)])

            position = chunk_end
            if position >= end:
                break

        return np.concatenate(selected) if selected else np.empty(0, dtype=np.float32)


def _start_control_reader(commands: queue.SimpleQueue[str], stop: threading.Event) -> threading.Thread | None:
    if not sys.stdin.isatty():
        return None

    def read_controls() -> None:
        file_descriptor = sys.stdin.fileno()
        original_mode = termios.tcgetattr(file_descriptor)
        pending = bytearray()

        try:
            tty.setcbreak(file_descriptor)
            while not stop.is_set():
                ready, _, _ = select.select([file_descriptor], [], [], 0.1)
                if not ready:
                    continue

                pending.extend(os.read(file_descriptor, 16))
                while pending:
                    if pending[0] == 0x1B:
                        if len(pending) < 3:
                            break
                        command = ARROW_COMMANDS.get(bytes(pending[:3]))
                        del pending[:3]
                    else:
                        command = KEY_COMMANDS.get(pending.pop(0))

                    if command:
                        commands.put(command)
        finally:
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, original_mode)

    thread = threading.Thread(target=read_controls, daemon=True)
    thread.start()
    return thread


class PlaybackController:
    """Prepare audio blocks off the device callback and stream them to SoundDevice."""

    def __init__(self, text: str, voice: Path, output: Path, on_status: StatusCallback | None = None) -> None:
        self.text = text
        self.voice = voice
        self.output = output
        self.on_status = on_status

        self.stop = threading.Event()
        self.source_done = threading.Event()
        self.feeding_done = threading.Event()
        self.drained = threading.Event()

        self.commands: queue.SimpleQueue[str] = queue.SimpleQueue()
        self.source: queue.Queue[np.ndarray] = queue.Queue(maxsize=50)
        self.ready: queue.Queue[np.ndarray] = queue.Queue(maxsize=50)

        self.failures: list[BaseException] = []
        self.cancelled = False
        self.underruns = 0

    def run(self) -> PlaybackResult:
        self.output.parent.mkdir(parents=True, exist_ok=True)

        model = load_model()
        voice_state = model.get_state_for_audio_prompt(str(self.voice))
        sample_rate = model.sample_rate
        block_size = max(1, sample_rate // 50)
        partial_output = self.output.with_name(f".{self.output.stem}.partial.wav")

        producer = threading.Thread(
            target=self._produce,
            args=(model, voice_state, sample_rate, partial_output),
            daemon=True,
        )
        producer.start()

        feeder = threading.Thread(target=self._feed_blocks, args=(sample_rate, block_size), daemon=True)
        feeder.start()

        controls = _start_control_reader(self.commands, self.stop)
        self._notify("playing")

        try:
            with sd.OutputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size,
                callback=self._callback,
            ):
                while not self.drained.wait(0.1):
                    if self.failures:
                        raise PlaybackFailed("Audio generation failed.") from self.failures[0]
        except KeyboardInterrupt:
            self.cancelled = True
            self.stop.set()
            raise
        finally:
            self.stop.set()
            producer.join(timeout=2)
            feeder.join(timeout=2)
            if controls:
                controls.join(timeout=1)

        if self.failures:
            raise PlaybackFailed("Audio generation failed.") from self.failures[0]

        output_path = self._finalize_recording(partial_output)
        self._notify("stopped" if self.cancelled else "finished")

        return PlaybackResult(
            completed=not self.cancelled,
            cancelled=self.cancelled,
            output_path=output_path,
            underruns=self.underruns,
        )

    def _produce(self, model: TTSModel, voice_state: dict, sample_rate: int, partial_output: Path) -> None:
        try:
            with sf.SoundFile(partial_output, "w", samplerate=sample_rate, channels=1, subtype="FLOAT") as wav:
                for chunk in model.generate_audio_stream(voice_state, self.text, stop=self.stop):
                    if self.stop.is_set():
                        break

                    samples = chunk.detach().cpu().numpy().astype(np.float32, copy=False)
                    wav.write(samples)

                    while not self.stop.is_set():
                        try:
                            self.source.put(samples, timeout=0.1)
                            break
                        except queue.Full:
                            pass
        except BaseException as error:
            self.failures.append(error)
        finally:
            self.source_done.set()

    def _feed_blocks(self, sample_rate: int, block_size: int) -> None:
        current = np.empty(0, dtype=np.float32)
        offset = 0

        rewind = np.empty(0, dtype=np.float32)
        rewind_offset = 0
        rewind_start = 0

        skip_remaining = 0
        paused = False
        seek = sample_rate * SEEK_SECONDS
        history = _AudioHistory(sample_rate * HISTORY_SECONDS)

        def next_source() -> np.ndarray | None:
            try:
                return self.source.get_nowait()
            except queue.Empty:
                return None

        while not self.stop.is_set():
            # Apply any pending key presses.
            while True:
                try:
                    command = self.commands.get_nowait()
                except queue.Empty:
                    break

                if command == "pause":
                    paused = not paused
                    self._clear_ready()
                    self._notify("paused" if paused else "playing")

                elif command == "back":
                    cursor = rewind_start + rewind_offset if len(rewind) else history.samples
                    rewind_start = max(0, cursor - seek)
                    rewind = history.slice(rewind_start, history.samples)
                    rewind_offset = 0
                    self._clear_ready()
                    self._notify(f"rewinding {SEEK_SECONDS}s" if len(rewind) else "playing")

                elif command == "forward":
                    if len(rewind):
                        cursor = rewind_start + rewind_offset
                        rewind_start = min(history.samples, cursor + seek)
                        rewind = history.slice(rewind_start, history.samples)
                        rewind_offset = 0
                    else:
                        skip_remaining += seek
                    self._clear_ready()
                    self._notify(f"skipping {SEEK_SECONDS}s")

                elif command == "quit":
                    self.cancelled = True
                    self.stop.set()
                    break

            if self.stop.is_set():
                break

            if paused:
                time.sleep(0.02)
                continue

            # Top up the ready queue with device-sized blocks.
            while self.ready.qsize() < 25 and not self.stop.is_set():
                while skip_remaining:
                    if offset == len(current):
                        next_audio = next_source()
                        if next_audio is None:
                            break
                        current, offset = next_audio, 0

                    count = min(skip_remaining, len(current) - offset)
                    history.remember(current[offset : offset + count])
                    offset += count
                    skip_remaining -= count

                if skip_remaining:
                    break

                block = np.zeros(block_size, dtype=np.float32)
                written = 0

                while written < block_size:
                    if rewind_offset < len(rewind):
                        count = min(block_size - written, len(rewind) - rewind_offset)
                        block[written : written + count] = rewind[rewind_offset : rewind_offset + count]
                        rewind_offset += count
                        written += count
                        continue

                    if offset == len(current):
                        next_audio = next_source()
                        if next_audio is None:
                            break
                        current, offset = next_audio, 0

                    count = min(block_size - written, len(current) - offset)
                    block[written : written + count] = current[offset : offset + count]
                    history.remember(current[offset : offset + count])
                    offset += count
                    written += count

                if not written:
                    break

                self.ready.put(block)

                if rewind_offset == len(rewind) and len(rewind):
                    rewind = np.empty(0, dtype=np.float32)
                    rewind_offset = 0
                    self._notify("playing")

            if self.source_done.is_set() and offset == len(current) and self.source.empty() and not len(rewind):
                self.feeding_done.set()
                return

            time.sleep(0.005)

        self.feeding_done.set()

    def _callback(self, outdata: np.ndarray, frames: int, _time: object, _status: object) -> None:
        outdata.fill(0)

        try:
            block = self.ready.get_nowait()
        except queue.Empty:
            self.underruns += 1
            if self.feeding_done.is_set():
                self.drained.set()
            return

        count = min(frames, len(block))
        outdata[:count, 0] = block[:count]

    def _clear_ready(self) -> None:
        while True:
            try:
                self.ready.get_nowait()
            except queue.Empty:
                return

    def _finalize_recording(self, partial_output: Path) -> Path:
        if not partial_output.exists():
            return self.output

        if self.cancelled:
            partial = self.output.with_name(f"{self.output.stem}-partial.wav")
            os.replace(partial_output, partial)
            return partial

        os.replace(partial_output, self.output)
        return self.output

    def _notify(self, state: str) -> None:
        if self.on_status:
            self.on_status(state)
