"""
Google Drive Service - Fetch and download files from Google Drive.

Educational Note: This service handles Google Drive operations:
1. List files from user's Drive (with optional folder navigation)
2. Download regular files (PDF, images, audio, etc.)
3. Export Google Workspace files (Docs→DOCX, Sheets→CSV, Slides→PPTX)

Google Drive File Types:
- Regular files: Stored as actual files (PDFs, images, etc.)
- Google Workspace files: Not actual files, stored as Google's format
  - Google Docs: Export as DOCX or TXT
  - Google Sheets: Export as CSV or XLSX
  - Google Slides: Export as PPTX or PDF

MIME Type Mapping:
- application/vnd.google-apps.document → Google Doc
- application/vnd.google-apps.spreadsheet → Google Sheet
- application/vnd.google-apps.presentation → Google Slides
- application/vnd.google-apps.folder → Folder
"""

import os
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.services.integrations.google.google_auth_service import google_auth_service


class GoogleDriveService:
    """
    Service class for Google Drive file operations.

    Educational Note: This service uses the Google Drive API v3 to:
    - List files with filtering and pagination
    - Download binary files
    - Export Google Workspace files to standard formats
    """

    # Mapping of Google Workspace MIME types to export formats
    # Educational Note: Google Workspace files must be EXPORTED, not downloaded
    # because they're not stored as regular files
    EXPORT_MIME_TYPES = {
        'application/vnd.google-apps.document': {
            'export_mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'extension': '.docx',
            'name': 'Google Doc'
        },
        'application/vnd.google-apps.spreadsheet': {
            'export_mime': 'text/csv',
            'extension': '.csv',
            'name': 'Google Sheet'
        },
        'application/vnd.google-apps.presentation': {
            'export_mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'extension': '.pptx',
            'name': 'Google Slides'
        },
    }

    # File types we can process (matches our source processing capabilities)
    SUPPORTED_MIME_TYPES = [
        # Documents
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'text/csv',
        # Images
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        # Audio
        'audio/mpeg',  # .mp3
        'audio/mp4',   # .m4a
        'audio/wav',
        'audio/x-m4a',
        'audio/aac',
        'audio/flac',
        # Google Workspace (will be exported)
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.spreadsheet',
        'application/vnd.google-apps.presentation',
        # Folders (for navigation)
        'application/vnd.google-apps.folder',
    ]

    def __init__(self):
        """Initialize the Google Drive service."""
        self._service = None

    def _get_service(self):
        """
        Get or create the Google Drive API service.

        Educational Note: We lazy-load the service to avoid errors
        when credentials aren't available yet.

        Returns:
            Drive API service or None
        """
        creds = google_auth_service.get_credentials()
        if not creds:
            return None

        # Build service (cache it for reuse)
        if self._service is None:
            self._service = build('drive', 'v3', credentials=creds)

        return self._service

    def is_connected(self) -> bool:
        """Check if Google Drive is connected and accessible."""
        return self._get_service() is not None

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files from Google Drive.

        Educational Note: The Drive API uses a query language for filtering.
        Key query operators:
        - 'folder_id' in parents: Files in a specific folder
        - trashed = false: Exclude deleted files
        - mimeType = '...': Filter by file type

        Args:
            folder_id: Optional folder ID to list (None = root/all)
            page_size: Number of files per page (max 1000)
            page_token: Token for pagination

        Returns:
            Dict with files list and pagination info
        """
        service = self._get_service()
        if not service:
            return {
                'success': False,
                'error': 'Google Drive not connected'
            }

        try:
            # Build query
            # Educational Note: We filter for supported file types and exclude trash
            query_parts = ["trashed = false"]

            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")

            query = " and ".join(query_parts)

            # Execute query
            # Educational Note: fields parameter limits response data for efficiency
            # Sort by modified time (newest first). Frontend separates folders/files.
            results = service.files().list(
                q=query,
                pageSize=page_size,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, iconLink, thumbnailLink)",
                orderBy="modifiedTime desc"
            ).execute()

            files = results.get('files', [])

            # Process files to add our metadata
            processed_files = []
            for file in files:
                mime_type = file.get('mimeType', '')

                # Skip unsupported file types (except folders)
                if mime_type not in self.SUPPORTED_MIME_TYPES:
                    continue

                # Determine if it's a Google Workspace file
                is_google_file = mime_type.startswith('application/vnd.google-apps.')
                is_folder = mime_type == 'application/vnd.google-apps.folder'

                # Get export info for Google files
                export_info = self.EXPORT_MIME_TYPES.get(mime_type, {})

                processed_files.append({
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'mime_type': mime_type,
                    'size': int(file.get('size', 0)) if file.get('size') else None,
                    'modified_time': file.get('modifiedTime'),
                    'is_folder': is_folder,
                    'is_google_file': is_google_file and not is_folder,
                    'export_extension': export_info.get('extension'),
                    'google_type': export_info.get('name'),
                    'icon_link': file.get('iconLink'),
                    'thumbnail_link': file.get('thumbnailLink'),
                })

            return {
                'success': True,
                'files': processed_files,
                'next_page_token': results.get('nextPageToken'),
                'folder_id': folder_id
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list files: {str(e)}'
            }

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file.

        Args:
            file_id: The Google Drive file ID

        Returns:
            Dict with file information
        """
        service = self._get_service()
        if not service:
            return {
                'success': False,
                'error': 'Google Drive not connected'
            }

        try:
            file = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, parents, webViewLink"
            ).execute()

            return {
                'success': True,
                'file': file
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get file info: {str(e)}'
            }

    def download_file(self, file_id: str, destination_path: Path) -> Tuple[bool, str]:
        """
        Download a file from Google Drive.

        Educational Note: There are two ways to get file content:
        1. Download: For regular files (PDFs, images, etc.)
        2. Export: For Google Workspace files (Docs, Sheets, Slides)

        This method handles both automatically based on file type.

        Args:
            file_id: The Google Drive file ID
            destination_path: Path where to save the file

        Returns:
            Tuple of (success, message or error)
        """
        service = self._get_service()
        if not service:
            return False, 'Google Drive not connected'

        try:
            # First, get file metadata to determine type
            file_info = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size"
            ).execute()

            mime_type = file_info.get('mimeType', '')
            file_name = file_info.get('name', 'unknown')

            # Check if it's a Google Workspace file that needs export
            if mime_type in self.EXPORT_MIME_TYPES:
                return self._export_google_file(
                    service, file_id, mime_type, destination_path, file_name
                )
            else:
                return self._download_regular_file(
                    service, file_id, destination_path, file_name
                )

        except Exception as e:
            return False, f'Failed to download file: {str(e)}'

    def _download_regular_file(
        self,
        service,
        file_id: str,
        destination_path: Path,
        file_name: str
    ) -> Tuple[bool, str]:
        """
        Download a regular (non-Google) file.

        Educational Note: Regular files are downloaded as-is using
        the media download API with chunked transfer.

        Args:
            service: Drive API service
            file_id: File ID
            destination_path: Where to save
            file_name: Original file name

        Returns:
            Tuple of (success, message)
        """
        try:
            request = service.files().get_media(fileId=file_id)

            # Download to memory buffer first
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            # Write to file
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            with open(destination_path, 'wb') as f:
                f.write(buffer.getvalue())

            return True, f'Downloaded {file_name}'

        except Exception as e:
            return False, f'Download failed: {str(e)}'

    def _export_google_file(
        self,
        service,
        file_id: str,
        mime_type: str,
        destination_path: Path,
        file_name: str
    ) -> Tuple[bool, str]:
        """
        Export a Google Workspace file to a standard format.

        Educational Note: Google Docs, Sheets, and Slides aren't stored
        as regular files. We must use the export API to convert them
        to standard formats like DOCX, CSV, or PPTX.

        Args:
            service: Drive API service
            file_id: File ID
            mime_type: Google Workspace MIME type
            destination_path: Where to save
            file_name: Original file name

        Returns:
            Tuple of (success, message)
        """
        export_info = self.EXPORT_MIME_TYPES.get(mime_type)
        if not export_info:
            return False, f'Unsupported Google file type: {mime_type}'

        try:
            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_info['export_mime']
            )

            # Download to memory buffer first
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            # Write to file
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            with open(destination_path, 'wb') as f:
                f.write(buffer.getvalue())

            return True, f'Exported {file_name} as {export_info["extension"]}'

        except Exception as e:
            return False, f'Export failed: {str(e)}'

    def get_file_extension(self, file_id: str) -> Optional[str]:
        """
        Get the appropriate file extension for a Drive file.

        Educational Note: For Google Workspace files, we return the
        export extension. For regular files, we extract from the name.

        Args:
            file_id: File ID

        Returns:
            File extension (e.g., '.pdf', '.docx') or None
        """
        service = self._get_service()
        if not service:
            return None

        try:
            file = service.files().get(
                fileId=file_id,
                fields="name, mimeType"
            ).execute()

            mime_type = file.get('mimeType', '')

            # Check if Google Workspace file
            if mime_type in self.EXPORT_MIME_TYPES:
                return self.EXPORT_MIME_TYPES[mime_type]['extension']

            # Regular file - get extension from name
            name = file.get('name', '')
            if '.' in name:
                return '.' + name.rsplit('.', 1)[-1].lower()

            return None

        except Exception:
            return None


# Singleton instance
google_drive_service = GoogleDriveService()
