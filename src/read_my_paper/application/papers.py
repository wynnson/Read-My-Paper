from __future__ import annotations

from pathlib import Path

from read_my_paper.domain.errors import PaperAlreadyExists, ReadMyPaperError
from read_my_paper.domain.models import PaperManifest
from read_my_paper.domain.narration import narration_from_document, narration_text
from read_my_paper.infrastructure.docling_extractor import extract_pdf
from read_my_paper.infrastructure.paper_store import PaperStore, paper_id_from_name


class PaperService:
    def __init__(self, store: PaperStore | None = None) -> None:
        self.store = store or PaperStore()

    def add(self, source: Path, replace: bool = False) -> PaperManifest:
        source = source.expanduser().resolve()
        if not source.is_file() or source.suffix.lower() != ".pdf":
            raise ReadMyPaperError("Source must be an existing PDF file.")

        paper_id = paper_id_from_name(source.name)

        # Fail before the slow OCR pass; the store re-checks on save.
        if not replace and self.store.exists(paper_id):
            raise PaperAlreadyExists(
                f"A paper named '{paper_id}' is already imported. Use --replace to overwrite it."
            )

        document = extract_pdf(source)
        blocks, skipped = narration_from_document(document)
        if not blocks:
            raise ReadMyPaperError("No narration text was extracted from this PDF.")

        manifest = PaperManifest(paper_id, source.name, blocks, skipped)
        self.store.save(source, document, manifest, replace=replace)

        return manifest

    def list(self) -> list[PaperManifest]:
        return self.store.list()

    def get(self, paper_id: str) -> PaperManifest:
        return self.store.load(paper_id)

    def text(self, paper_id: str, start_block: int = 0) -> str:
        manifest = self.get(paper_id)
        if start_block < 0 or start_block >= len(manifest.blocks):
            raise ReadMyPaperError("--from-block is past the end of this paper.")

        return narration_text(manifest.blocks, start_block)

    def new_recording_path(self, paper_id: str) -> Path:
        return self.store.new_recording_path(paper_id)
