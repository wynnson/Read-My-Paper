from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from read_my_paper.domain.errors import InvalidPaperId
from read_my_paper.domain.models import NarrationBlock, PaperManifest
from read_my_paper.infrastructure.paper_store import PaperStore


class Document:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def save_as_json(self, path: Path) -> None:
        if self.fail:
            raise OSError("disk full")
        path.write_text("{}", encoding="utf-8")


class PaperStoreTests(unittest.TestCase):
    def test_failed_replace_preserves_existing_paper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"pdf")
            store = PaperStore(root / "papers")
            original = PaperManifest("paper", "paper.pdf", [NarrationBlock(0, "old", "text", 1)], {})
            replacement = PaperManifest("paper", "paper.pdf", [NarrationBlock(0, "new", "text", 1)], {})
            store.save(source, Document(), original)

            with self.assertRaises(OSError):
                store.save(source, Document(fail=True), replacement, replace=True)

            self.assertEqual(store.load("paper").blocks[0].text, "old")

    def test_rejects_unsafe_paper_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PaperStore(Path(directory))
            with self.assertRaises(InvalidPaperId):
                store.load("../outside")
