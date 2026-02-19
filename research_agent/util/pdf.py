"""PDF text extraction using PyMuPDF."""

from __future__ import annotations

import fitz  # PyMuPDF


def extract_text_from_pdf(data: bytes, *, max_chars: int = 40_000) -> str:
    """Extract text from PDF bytes, truncating at page boundaries.

    Args:
        data: Raw PDF file bytes.
        max_chars: Maximum characters to return.  Truncation happens at page
            boundaries so partial pages are never included.

    Returns:
        Extracted text with page markers.

    Raises:
        ValueError: If the file cannot be parsed as a PDF.
    """
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF: {exc}") from exc

    pages: list[str] = []
    total_chars = 0
    truncated_at: int | None = None

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue
        if total_chars + len(text) > max_chars:
            truncated_at = i
            break
        pages.append(f"--- Page {i + 1} ---\n{text}")
        total_chars += len(text)

    page_count = doc.page_count
    doc.close()

    if not pages:
        raise ValueError("PDF contains no extractable text")

    result = "\n\n".join(pages)
    if truncated_at is not None:
        remaining = page_count - truncated_at
        result += f"\n\n[...truncated, {remaining} more page(s)...]"

    return result
