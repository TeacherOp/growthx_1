"""
Encoding Utilities - Base64 encoding for files.

Educational Note: Claude's API requires binary files (PDFs, images) to be
sent as base64-encoded strings. This utility handles the encoding process
for different file types.

Why base64?
- HTTP/JSON can only transmit text, not binary data
- Base64 converts binary data to ASCII text (about 33% larger)
- Claude decodes it back to binary on the server side
"""
import base64
from pathlib import Path
from typing import Union


def encode_file_to_base64(file_path: Union[str, Path]) -> str:
    """
    Encode a file to base64 string.

    Educational Note: This is the standard way to prepare binary files
    (PDFs, images) for Claude's API. The file is read in binary mode
    and converted to a base64 string.

    Args:
        file_path: Path to the file to encode

    Returns:
        Base64-encoded string of the file contents

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # standard_b64encode returns bytes, decode to string for JSON
    return base64.standard_b64encode(file_bytes).decode("utf-8")


def encode_bytes_to_base64(data: bytes) -> str:
    """
    Encode bytes to base64 string.

    Educational Note: Use this when you already have the file
    contents in memory (e.g., from a file upload).

    Args:
        data: Bytes to encode

    Returns:
        Base64-encoded string
    """
    return base64.standard_b64encode(data).decode("utf-8")


def get_media_type(file_path: Union[str, Path]) -> str:
    """
    Get the MIME type for a file based on extension.

    Educational Note: Claude needs to know the file type to process it
    correctly. We map common extensions to their MIME types.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (e.g., "application/pdf", "image/png")
    """
    extension_to_mime = {
        # Documents
        ".pdf": "application/pdf",
        # Images (supported by Claude vision)
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    ext = Path(file_path).suffix.lower()
    return extension_to_mime.get(ext, "application/octet-stream")


def is_supported_for_encoding(file_path: Union[str, Path]) -> bool:
    """
    Check if a file type is supported for base64 encoding to Claude.

    Educational Note: Only certain file types can be sent to Claude
    as base64-encoded content blocks. PDFs and images are supported.

    Args:
        file_path: Path to check

    Returns:
        True if the file type can be encoded and sent to Claude
    """
    supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
    ext = Path(file_path).suffix.lower()
    return ext in supported_extensions
