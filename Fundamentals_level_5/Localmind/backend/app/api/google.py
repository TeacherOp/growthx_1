"""
API endpoints for Google Drive integration.

Educational Note: This module handles Google OAuth flow and Drive operations:
- /google/status: Check if configured and connected
- /google/auth: Start OAuth flow (returns auth URL)
- /google/callback: Handle OAuth callback (exchange code for tokens)
- /google/disconnect: Remove stored tokens
- /google/files: List files from Drive
- /google/import: Import a file to project sources
"""

from flask import jsonify, request, redirect, current_app
from app.api import api_bp
from app.services.integrations.google import google_auth_service, google_drive_service


@api_bp.route('/google/status', methods=['GET'])
def google_status():
    """
    Check Google Drive configuration and connection status.

    Educational Note: This endpoint checks two things:
    1. Is Google OAuth configured? (client ID + secret set)
    2. Is user connected? (valid tokens stored)

    Returns:
        JSON with configured, connected status, and user email if connected
    """
    try:
        is_configured = google_auth_service.is_configured()
        is_connected, email = google_auth_service.is_connected()

        return jsonify({
            'success': True,
            'configured': is_configured,
            'connected': is_connected,
            'email': email
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking Google status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/google/auth', methods=['GET'])
def google_auth():
    """
    Start Google OAuth flow by returning the authorization URL.

    Educational Note: The frontend will redirect user to this URL.
    After user grants permission, Google redirects back to our callback.

    Returns:
        JSON with auth_url to redirect user to
    """
    try:
        if not google_auth_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Google OAuth not configured. Please add Client ID and Secret in App Settings.'
            }), 400

        auth_url = google_auth_service.get_auth_url()
        if not auth_url:
            return jsonify({
                'success': False,
                'error': 'Failed to generate auth URL'
            }), 500

        return jsonify({
            'success': True,
            'auth_url': auth_url
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error generating auth URL: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    Handle OAuth callback from Google.

    Educational Note: Google redirects here after user grants permission.
    The URL contains an authorization code that we exchange for tokens.
    After successful auth, we redirect to frontend with success message.

    Query Params:
        code: Authorization code from Google
        error: Error message if user denied access

    Returns:
        Redirect to frontend with success/error
    """
    try:
        # Check for error (user denied access)
        error = request.args.get('error')
        if error:
            current_app.logger.warning(f"Google OAuth denied: {error}")
            return redirect(f'http://localhost:5173?google_auth=error&message={error}')

        # Get authorization code
        code = request.args.get('code')
        if not code:
            return redirect('http://localhost:5173?google_auth=error&message=No+authorization+code')

        # Exchange code for tokens
        success, message = google_auth_service.handle_callback(code)

        if success:
            current_app.logger.info(f"Google OAuth successful: {message}")
            return redirect('http://localhost:5173?google_auth=success')
        else:
            current_app.logger.error(f"Google OAuth failed: {message}")
            return redirect(f'http://localhost:5173?google_auth=error&message={message}')

    except Exception as e:
        current_app.logger.error(f"Error in Google callback: {e}")
        return redirect(f'http://localhost:5173?google_auth=error&message={str(e)}')


@api_bp.route('/google/disconnect', methods=['POST'])
def google_disconnect():
    """
    Disconnect Google Drive by removing stored tokens.

    Returns:
        JSON with success status
    """
    try:
        success, message = google_auth_service.disconnect()

        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500

    except Exception as e:
        current_app.logger.error(f"Error disconnecting Google: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/google/files', methods=['GET'])
def google_list_files():
    """
    List files from Google Drive.

    Educational Note: This endpoint supports folder navigation and pagination.
    Files are filtered to only show types we can process.

    Query Params:
        folder_id: Optional folder ID to list (root if not specified)
        page_size: Number of files per page (default 50)
        page_token: Token for next page

    Returns:
        JSON with files list and pagination info
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


@api_bp.route('/projects/<project_id>/sources/google-import', methods=['POST'])
def google_import_file(project_id):
    """
    Import a file from Google Drive to project sources.

    Educational Note: This endpoint:
    1. Downloads/exports the file from Google Drive
    2. Saves it to the project's raw sources folder
    3. Creates source entry using source_service.create_source_from_file()
    4. Processing is automatically triggered (same as regular file upload)

    Body:
        file_id: Google Drive file ID
        name: Optional custom name for the source

    Returns:
        JSON with created source info
    """
    try:
        import uuid
        from pathlib import Path
        from app.services.source_services import source_service

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

        # Determine file extension
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
        category = 'document'
        if mime_type.startswith('image/'):
            category = 'image'
        elif mime_type.startswith('audio/'):
            category = 'audio'
        elif extension == '.csv':
            category = 'data'

        # Ensure directories exist
        source_service._ensure_directories(project_id)

        # Build destination path (same pattern as upload_source)
        raw_dir = source_service._get_raw_dir(project_id)
        stored_filename = f"{source_id}{extension}"
        destination_path = raw_dir / stored_filename

        # Download/export file from Drive
        success, message = google_drive_service.download_file(file_id, destination_path)
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 500

        # Map Google MIME types to our expected types
        actual_mime_type = mime_type
        if mime_type == 'application/vnd.google-apps.document':
            actual_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            actual_mime_type = 'text/csv'
        elif mime_type == 'application/vnd.google-apps.presentation':
            actual_mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

        # Create source entry using the new method
        # This also triggers background processing automatically
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
