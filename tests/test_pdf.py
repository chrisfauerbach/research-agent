"""Tests for PDF text extraction utility."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from research_agent.util.pdf import extract_text_from_pdf


def _make_mock_page(text: str) -> MagicMock:
    page = MagicMock()
    page.get_text.return_value = text
    return page


def _make_mock_doc(pages: list[MagicMock], page_count: int | None = None) -> MagicMock:
    doc = MagicMock()
    doc.__iter__ = MagicMock(return_value=iter(enumerate(pages)))
    # fitz iterates pages as (index, page) when using enumerate, but actually
    # the doc itself iterates yielding page objects
    doc.__iter__ = MagicMock(return_value=iter(pages))
    doc.page_count = page_count if page_count is not None else len(pages)
    doc.close = MagicMock()
    return doc


def test_extract_text_success():
    pages = [_make_mock_page("Page one content."), _make_mock_page("Page two content.")]
    mock_doc = _make_mock_doc(pages)

    with patch("research_agent.util.pdf.fitz") as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert "--- Page 1 ---" in result
    assert "Page one content." in result
    assert "--- Page 2 ---" in result
    assert "Page two content." in result
    mock_doc.close.assert_called_once()


def test_extract_text_truncation():
    pages = [
        _make_mock_page("A" * 100),
        _make_mock_page("B" * 100),
        _make_mock_page("C" * 100),
    ]
    mock_doc = _make_mock_doc(pages, page_count=3)

    with patch("research_agent.util.pdf.fitz") as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        result = extract_text_from_pdf(b"fake", max_chars=150)

    # Only first page fits (100 chars < 150), second page (100+100=200 > 150) triggers truncation
    assert "--- Page 1 ---" in result
    assert "truncated" in result
    assert "2 more page(s)" in result


def test_extract_text_empty_pdf():
    pages = [_make_mock_page(""), _make_mock_page("   ")]
    mock_doc = _make_mock_doc(pages)

    with patch("research_agent.util.pdf.fitz") as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        with pytest.raises(ValueError, match="no extractable text"):
            extract_text_from_pdf(b"fake")


def test_extract_text_invalid_pdf():
    with patch("research_agent.util.pdf.fitz") as mock_fitz:
        mock_fitz.open.side_effect = RuntimeError("not a pdf")
        with pytest.raises(ValueError, match="Failed to parse PDF"):
            extract_text_from_pdf(b"not pdf")


def test_extract_text_skips_empty_pages():
    pages = [
        _make_mock_page(""),
        _make_mock_page("Content here."),
        _make_mock_page(""),
    ]
    mock_doc = _make_mock_doc(pages, page_count=3)

    with patch("research_agent.util.pdf.fitz") as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        result = extract_text_from_pdf(b"fake")

    # Only page 2 has content (index 1 → display "Page 2")
    assert "--- Page 2 ---" in result
    assert "Content here." in result
    assert "Page 1" not in result
    assert "Page 3" not in result
