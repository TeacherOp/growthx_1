"""
API endpoints for managing project sources.

Educational Note: These endpoints handle uploading, listing, and managing
raw source files for projects. Sources are documents, images, audio, and
data files that provide context for AI conversations.
"""
from flask import jsonify, request, current_app, send_file
from app.api import api_bp
from app.services.source_service import SourceService

# Initialize service
source_service = SourceService()


@api_bp.route('/projects/<project_id>/sources', methods=['GET'])
def list_sources(project_id: str):
    """
    List all sources for a project.

    Educational Note: Returns metadata for all uploaded sources,
    sorted by most recent first.
    """
    try:
        sources = source_service.list_sources(project_id)

        return jsonify({
            'success': True,
            'sources': sources,
            'count': len(sources)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing sources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources', methods=['POST'])
def upload_source(project_id: str):
    """
    Upload a new source file to a project.

    Educational Note: Accepts multipart/form-data with:
    - file: The source file (required)
    - name: Display name (optional, defaults to filename)
    - description: Description of the source (optional)

    Supported file types: PDF, TXT, MD, MP3, images (PNG, JPG, etc.), CSV
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Get optional fields from form data
        name = request.form.get('name')
        description = request.form.get('description', '')

        # Upload the source
        source = source_service.upload_source(
            project_id=project_id,
            file=file,
            name=name,
            description=description
        )

        return jsonify({
            'success': True,
            'source': source,
            'message': 'Source uploaded successfully'
        }), 201

    except ValueError as e:
        # Validation errors (file type not allowed, etc.)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error uploading source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources/<source_id>', methods=['GET'])
def get_source(project_id: str, source_id: str):
    """
    Get a specific source's metadata.

    Educational Note: Returns full metadata for a single source,
    including processing status and details.
    """
    try:
        source = source_service.get_source(project_id, source_id)

        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404

        return jsonify({
            'success': True,
            'source': source
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources/<source_id>', methods=['PUT'])
def update_source(project_id: str, source_id: str):
    """
    Update a source's metadata.

    Educational Note: Allows updating display name and description.
    The raw file cannot be updated - delete and re-upload instead.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        source = source_service.update_source(
            project_id=project_id,
            source_id=source_id,
            name=data.get('name'),
            description=data.get('description')
        )

        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404

        return jsonify({
            'success': True,
            'source': source,
            'message': 'Source updated successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources/<source_id>', methods=['DELETE'])
def delete_source(project_id: str, source_id: str):
    """
    Delete a source and its raw file.

    Educational Note: This is a hard delete - the raw file
    and all metadata are permanently removed.
    """
    try:
        deleted = source_service.delete_source(project_id, source_id)

        if not deleted:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Source deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources/<source_id>/download', methods=['GET'])
def download_source(project_id: str, source_id: str):
    """
    Download the raw source file.

    Educational Note: Returns the original uploaded file
    for download or viewing.
    """
    try:
        source = source_service.get_source(project_id, source_id)

        if not source:
            return jsonify({
                'success': False,
                'error': 'Source not found'
            }), 404

        file_path = source_service.get_source_file_path(project_id, source_id)

        if not file_path or not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Source file not found on disk'
            }), 404

        # Send file with appropriate MIME type
        return send_file(
            file_path,
            mimetype=source.get('mime_type', 'application/octet-stream'),
            as_attachment=True,
            download_name=source.get('original_filename', source.get('name'))
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/sources/summary', methods=['GET'])
def get_sources_summary(project_id: str):
    """
    Get a summary of sources for a project.

    Educational Note: Returns aggregate statistics about sources,
    useful for dashboard displays.
    """
    try:
        summary = source_service.get_sources_summary(project_id)

        return jsonify({
            'success': True,
            'summary': summary
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting sources summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sources/allowed-types', methods=['GET'])
def get_allowed_types():
    """
    Get the list of allowed file types for upload.

    Educational Note: Returns allowed extensions grouped by category.
    Useful for frontend validation and UI display.
    """
    try:
        extensions = source_service.get_allowed_extensions()

        # Group by category for easier frontend use
        by_category = {}
        for ext, category in extensions.items():
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(ext)

        return jsonify({
            'success': True,
            'allowed_extensions': extensions,
            'by_category': by_category
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting allowed types: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
