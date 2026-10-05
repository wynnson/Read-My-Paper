from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from read_my_paper.domain.errors import InvalidManifest, InvalidPaperId, PaperAlreadyExists, PaperNotFound
from read_my_paper.domain.models import NarrationBlock, PaperManifest
from read_my_paper.domain.narration import narration_text
from read_my_paper.infrastructure.paths import papers_root


PAPER_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MANIFEST_NAME = "manifest.json"


def paper_id_from_name(source_name: str) -> str:
    paper_id = re.sub(r"[^a-z0-9]+", "-", Path(source_name).stem.casefold()).strip("-")
    if not paper_id:
        raise InvalidPaperId("PDF filename must contain letters or numbers.")
    return paper_id


def validate_paper_id(paper_id: str) -> str:
    if not PAPER_ID_PATTERN.fullmatch(paper_id):
        raise InvalidPaperId("Paper ID may only contain lowercase letters, digits, and hyphens.")
    return paper_id


def read_manifest(path: Path) -> PaperManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["blocks"] = [NarrationBlock(**block) for block in data["blocks"]]
    return PaperManifest(**data)


def write_manifest(path: Path, manifest: PaperManifest) -> None:
    path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")


class PaperStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or papers_root()
        self.root.mkdir(parents=True, exist_ok=True)

    def exists(self, paper_id: str) -> bool:
        return self._path(paper_id).is_dir()

    def load(self, paper_id: str) -> PaperManifest:
        path = self._path(paper_id) / MANIFEST_NAME
        if not path.is_file():
            raise PaperNotFound(f"Unknown paper ID: {paper_id}")

        try:
            manifest = read_manifest(path)
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise InvalidManifest(f"Invalid manifest for paper '{paper_id}'.") from error

        if manifest.id != paper_id:
            raise InvalidManifest(f"Manifest ID does not match paper directory '{paper_id}'.")

        return manifest

    def list(self) -> list[PaperManifest]:
        return [self.load(path.parent.name) for path in sorted(self.root.glob(f"*/{MANIFEST_NAME}"))]

    def save(self, source: Path, document: object, manifest: PaperManifest, replace: bool = False) -> None:
        destination = self._path(manifest.id)
        if destination.exists() and not replace:
            raise PaperAlreadyExists(f"A paper named '{manifest.id}' is already imported.")

        # Build everything in a hidden staging directory, then swap it into place.
        staging = self.root / f".{manifest.id}-{uuid.uuid4().hex}.tmp"
        staging.mkdir()

        try:
            shutil.copy2(source, staging / "source.pdf")
            document.save_as_json(staging / "document.json")
            write_manifest(staging / MANIFEST_NAME, manifest)
            (staging / "narration.txt").write_text(narration_text(manifest.blocks), encoding="utf-8")
            self._replace_directory(staging, destination)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def new_recording_path(self, paper_id: str) -> Path:
        """Timestamped location for a fresh recording; the directory is created on write."""
        return self._path(paper_id) / "audio" / f"{datetime.now():%Y%m%d-%H%M%S}.wav"

    def _path(self, paper_id: str) -> Path:
        return self.root / validate_paper_id(paper_id)

    @staticmethod
    def _replace_directory(staging: Path, destination: Path) -> None:
        if not destination.exists():
            os.replace(staging, destination)
            return

        backup = destination.with_name(f".{destination.name}-{uuid.uuid4().hex}.bak")
        os.replace(destination, backup)

        try:
            os.replace(staging, destination)
        except BaseException:
            os.replace(backup, destination)
            raise

        shutil.rmtree(backup)
