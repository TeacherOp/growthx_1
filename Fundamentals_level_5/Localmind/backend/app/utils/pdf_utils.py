"""
PDF Utilities - Helper functions for PDF manipulation.

Educational Note: This module handles PDF operations like:
- Getting page count
- Extracting single pages as separate PDFs
- Creating temporary single-page PDFs for API calls

Why split PDFs into pages?
- Claude API has a 100-page limit per request
- Processing page-by-page allows handling PDFs of any size
- Enables progress tracking for large documents
- Each page's extracted text can be appended with page markers
"""
import io
import tempfile
from pathlib import Path
from typing import Union, Generator, Tuple, List

from pypdf import PdfReader, PdfWriter


def get_page_count(pdf_path: Union[str, Path]) -> int:
    """
    Get the total number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF

    Raises:
        FileNotFoundError: If PDF doesn't exist
        Exception: If PDF is corrupted or unreadable
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    return len(reader.pages)


def extract_single_page_bytes(pdf_path: Union[str, Path], page_number: int) -> bytes:
    """
    Extract a single page from a PDF and return it as bytes.

    Educational Note: We create a new PDF with just the one page,
    then return it as bytes for base64 encoding. This allows
    sending individual pages to Claude API.

    Args:
        pdf_path: Path to the source PDF file
        page_number: 1-indexed page number to extract

    Returns:
        Bytes of a new PDF containing only the specified page

    Raises:
        ValueError: If page_number is out of range
        FileNotFoundError: If PDF doesn't exist
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    # Convert to 0-indexed for pypdf
    page_index = page_number - 1

    if page_index < 0 or page_index >= total_pages:
        raise ValueError(f"Page {page_number} out of range. PDF has {total_pages} pages.")

    # Create a new PDF with just this page
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])

    # Write to bytes buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer.read()


def iterate_pages(pdf_path: Union[str, Path]) -> Generator[Tuple[int, bytes], None, None]:
    """
    Generator that yields each page of a PDF as (page_number, page_bytes).

    Educational Note: Using a generator allows processing very large PDFs
    without loading all pages into memory at once. Each page is extracted
    and yielded one at a time.

    Args:
        pdf_path: Path to the PDF file

    Yields:
        Tuple of (page_number, page_bytes) where page_number is 1-indexed
        and page_bytes is the PDF bytes for that single page
    """
    pdf_path = Path(pdf_path)
    total_pages = get_page_count(pdf_path)

    for page_num in range(1, total_pages + 1):
        page_bytes = extract_single_page_bytes(pdf_path, page_num)
        yield (page_num, page_bytes)


def get_all_page_bytes(pdf_path: Union[str, Path]) -> List[Tuple[int, bytes]]:
    """
    Extract all pages from a PDF and return as a list.

    Educational Note: Unlike iterate_pages() which is a generator,
    this loads all pages into memory at once. Use this when you need
    all pages upfront (e.g., for batching before parallel processing).

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of (page_number, page_bytes) tuples, 1-indexed
    """
    return list(iterate_pages(pdf_path))


def get_pdf_metadata(pdf_path: Union[str, Path]) -> dict:
    """
    Get metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dict containing PDF metadata (title, author, etc.)
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    metadata = reader.metadata

    if metadata is None:
        return {}

    return {
        "title": metadata.get("/Title", ""),
        "author": metadata.get("/Author", ""),
        "subject": metadata.get("/Subject", ""),
        "creator": metadata.get("/Creator", ""),
        "producer": metadata.get("/Producer", ""),
        "creation_date": str(metadata.get("/CreationDate", "")),
        "modification_date": str(metadata.get("/ModDate", "")),
    }
