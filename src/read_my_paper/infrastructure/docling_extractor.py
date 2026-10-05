from __future__ import annotations

from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def extract_pdf(source: Path) -> object:
    options = PdfPipelineOptions()
    options.do_ocr = True
    options.do_formula_enrichment = True
    options.use_reading_order_separators = True
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
    return converter.convert(source).document
