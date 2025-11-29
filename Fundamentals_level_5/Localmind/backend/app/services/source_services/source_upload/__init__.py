"""
Source Upload Module - Handles different types of source uploads.

Educational Note: Upload logic is separated by type for cleaner code:
- file_upload: File uploads (PDF, DOCX, images, audio, etc.)
- url_upload: URL sources (websites, YouTube links)
- text_upload: Pasted text content
"""
from app.services.source_services.source_upload.file_upload import (
    upload_file,
    create_from_existing_file
)
from app.services.source_services.source_upload.url_upload import upload_url
from app.services.source_services.source_upload.text_upload import upload_text

__all__ = [
    "upload_file",
    "create_from_existing_file",
    "upload_url",
    "upload_text"
]
