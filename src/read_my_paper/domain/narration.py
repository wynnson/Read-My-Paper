from __future__ import annotations

import re
from collections import Counter

from read_my_paper.domain.latex_speech import latex_to_speech
from read_my_paper.domain.math_speech import unicode_to_speech
from read_my_paper.domain.models import NarrationBlock


STICKY_BACK_MATTER = {"references"}
SKIPPED_LABELS = {"caption", "chart", "page_footer", "page_header", "picture", "table"}
SPOKEN_LABELS = {"code", "formula", "list_item", "paragraph", "section_header", "text", "title"}
CITATION_PATTERN = re.compile(r"\s*\[(?:\s*\d+\s*(?:[,;\-\u2013\u2014]\s*\d+\s*)*)\]")


def normalize_text(text: str) -> str:
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = CITATION_PATTERN.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def spoken_text(raw_text: str, label: str) -> str:
    """Turn an extracted item into text the TTS can pronounce."""
    if label == "formula":
        return normalize_text(latex_to_speech(raw_text))
    return normalize_text(unicode_to_speech(raw_text))


def narration_from_document(document: object) -> tuple[list[NarrationBlock], dict[str, int]]:
    """Select main narrative content from Docling's layout-aware reading order."""
    blocks: list[NarrationBlock] = []
    skipped: Counter[str] = Counter()
    back_matter: str | None = None

    items = list(document.iterate_items(root=document.body))
    abstract_index = next((index for index, (item, _) in enumerate(items) if is_abstract_heading(item)), None)
    if abstract_index:
        skipped["front_matter"] = abstract_index
        items = items[abstract_index:]

    for item, _ in items:
        label = getattr(getattr(item, "label", None), "value", "")
        text = spoken_text(str(getattr(item, "text", "")), label)

        # Each heading opens or closes a back-matter section, except sticky ones that run to the end.
        if label == "section_header" and back_matter not in STICKY_BACK_MATTER:
            back_matter = back_matter_section(text)
        if back_matter:
            skipped[back_matter] += 1
            continue

        if label in SKIPPED_LABELS:
            skipped[label] += 1
            continue
        if label not in SPOKEN_LABELS or not text:
            continue

        provenance = getattr(item, "prov", [])
        page = getattr(provenance[0], "page_no", None) if provenance else None
        blocks.append(NarrationBlock(len(blocks), text, label, page))

    return blocks, dict(skipped)


def narration_text(blocks: list[NarrationBlock], start_block: int = 0) -> str:
    return "\n\n".join(block.text for block in blocks[start_block:])


def is_abstract_heading(item: object) -> bool:
    return normalize_text(str(getattr(item, "text", ""))).rstrip(".:").casefold() == "abstract"


def back_matter_section(text: str) -> str | None:
    heading = re.sub(r"^(?:\d+|[IVXLCDM]+)[.):-]*\s+", "", normalize_text(text), flags=re.I)
    heading = heading.rstrip(".:").casefold()

    if heading.startswith(("acknowledgment", "acknowledgement")):
        return "acknowledgements"
    if heading.startswith(("reference", "bibliography")):
        return "references"
    return None
