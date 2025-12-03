"""
Google Drive file operations endpoints.

Educational Note: These endpoints handle listing and importing files
from Google Drive. This demonstrates:

1. Paginated API responses - Drive can have thousands of files
2. File type handling - Different MIME types need different processing
3. Google Workspace exports - Docs/Sheets/Slides need conversion

Google Workspace File Exports:
- Google Docs -> DOCX (Word)
- Google Sheets -> CSV
- Google Slides -> PPTX (PowerPoint)

Regular files (PDF, images, etc.) are downloaded directly.

Routes:
- GET  /google/files                              - List files from Drive
- POST /projects/<id>/sources/google-import       - Import file to project
"""
import uuid
from flask import jsonify, request, current_app
from app.api.google import google_bp
from app.services.integrations.google import google_drive_service
from app.services.source_services import source_service
from app.utils.path_utils import get_raw_dir


@google_bp.route('/google/files', methods=['GET'])
def google_list_files():
    """
    List files from Google Drive.

    Educational Note: This endpoint demonstrates paginated API design:
    - page_size: How many items per page
    - page_token: Opaque token for the next page (from Google)

    Files are filtered to only show types we can process.
    Folders are always included for navigation.

    Query Params:
        folder_id: Optional folder ID to list (root if not specified)
        page_size: Number of files per page (default 50)
        page_token: Token for next page (from previous response)

    Returns:
        {
            "success": true,
            "files": [...],
            "next_page_token": "..." or null
        }
    """
    try:
        folder_id = request.args.get('folder_id')
        page_size = int(request.args.get('page_size', 50))
        page_token = request.args.get('page_token')

        result = google_drive_service.list_files(
            folder_id=folder_id,
            page_size=page_size,
            page_token=page_token
        )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.error(f"Error listing Google files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@google_bp.route('/projects/<project_id>/sources/google-import', methods=['POST'])
def google_import_file(project_id):
    """
    Import a file from Google Drive to project sources.

    Educational Note: This endpoint demonstrates file processing pipeline:
    1. Get file metadata from Drive API
    2. Determine appropriate export format (for Workspace files)
    3. Download/export file to local storage
    4. Create source entry (triggers processing pipeline)

    The source_service.create_source_from_file() handles:
    - Creating source metadata in sources_index.json
    - Triggering background processing (extraction, embedding)

    Request Body:
        {
            "file_id": "abc123...",     # Google Drive file ID
            "name": "Optional name"      # Custom display name
        }

    Returns:
        {
            "success": true,
            "source": { ... source object ... },
            "message": "Imported example.pdf from Google Drive"
        }
    """
    try:
        data = request.get_json()
        if not data or 'file_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing file_id'
            }), 400

        file_id = data['file_id']
        custom_name = data.get('name')

        # Get file info from Drive
        file_info = google_drive_service.get_file_info(file_id)
        if not file_info['success']:
            return jsonify(file_info), 400

        file = file_info['file']
        file_name = custom_name or file.get('name', 'unknown')
        mime_type = file.get('mimeType', '')

        # Determine file extension (handles Workspace file exports)
        extension = google_drive_service.get_file_extension(file_id)
        if not extension:
            return jsonify({
                'success': False,
                'error': 'Could not determine file type'
            }), 400

        # Ensure file name has correct extension
        if not file_name.lower().endswith(extension):
            base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            file_name = base_name + extension

        # Generate source ID for file naming
        source_id = str(uuid.uuid4())

        # Determine category based on MIME type
        category = _get_category_from_mime_type(mime_type, extension)

        # Build destination path
        # Note: get_raw_dir auto-creates directories if they don't exist
        raw_dir = get_raw_dir(project_id)
        stored_filename = f"{source_id}{extension}"
        destination_path = raw_dir / stored_filename

        # Download/export file from Drive
        success, message = google_drive_service.download_file(file_id, destination_path)
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 500

        # Map Google MIME types to standard types
        actual_mime_type = _map_google_mime_type(mime_type)

        # Create source entry (also triggers background processing)
        created_source = source_service.create_source_from_file(
            project_id=project_id,
            file_path=destination_path,
            name=file_name,
            original_filename=file_name,
            category=category,
            mime_type=actual_mime_type,
            description='Imported from Google Drive'
        )

        return jsonify({
            'success': True,
            'source': created_source,
            'message': f'Imported {file_name} from Google Drive'
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error importing from Google Drive: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_category_from_mime_type(mime_type: str, extension: str) -> str:
    """
    Determine source category from MIME type.

    Educational Note: Categories help the UI display appropriate icons
    and help the processing pipeline choose the right extractor.
    """
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif extension == '.csv':
        return 'data'
    else:
        return 'document'


def _map_google_mime_type(mime_type: str) -> str:
    """
    Map Google Workspace MIME types to standard MIME types.

    Educational Note: Google Workspace files (Docs, Sheets, Slides)
    have special MIME types that we need to map to their exported formats.
    """
    mime_type_mapping = {
        'application/vnd.google-apps.document':
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.google-apps.spreadsheet':
            'text/csv',
        'application/vnd.google-apps.presentation':
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    return mime_type_mapping.get(mime_type, mime_type)
