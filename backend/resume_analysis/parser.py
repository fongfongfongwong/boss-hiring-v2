"""Resume file parsing – extract raw text from PDF / Word documents."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pymupdf."""
    try:
        import fitz  # pymupdf

        doc = fitz.open(file_path)
        text_parts: list[str] = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n".join(text_parts).strip()
        logger.info("Parsed PDF (%d chars): %s", len(text), file_path)
        return text
    except Exception as e:
        logger.error("Failed to parse PDF %s: %s", file_path, e)
        return ""


def parse_docx(file_path: str) -> str:
    """Extract text from a Word (.docx) file."""
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        logger.info("Parsed DOCX (%d chars): %s", len(text), file_path)
        return text
    except Exception as e:
        logger.error("Failed to parse DOCX %s: %s", file_path, e)
        return ""


def parse_resume(file_path: str) -> str:
    """Parse a resume file and return raw text.

    Supports PDF and DOCX formats.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        return parse_docx(file_path)
    else:
        logger.warning("Unsupported file format: %s", suffix)
        # Try reading as plain text
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""
