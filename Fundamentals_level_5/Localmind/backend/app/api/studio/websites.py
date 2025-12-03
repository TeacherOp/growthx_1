"""
Website Generator endpoints - AI-generated multi-page websites.

Educational Note: Website generation demonstrates complex agent workflows:
1. website_agent_executor orchestrates the entire process
2. Claude generates HTML, CSS, and JavaScript
3. Gemini generates images for the site
4. Complete package: multiple pages + assets

Agent Architecture:
- Uses website_agent_executor for orchestration
- Agent has tools for page creation, styling, scripting
- Multi-page sites with navigation
- Responsive design patterns

Output Structure:
- index.html (main page)
- Additional pages (about.html, etc.)
- styles.css (stylesheet)
- script.js (JavaScript)
- assets/ folder for images
- All served via Flask endpoints

Routes:
- POST /projects/<id>/studio/website                        - Start generation
- GET  /projects/<id>/studio/website-jobs/<id>              - Job status
- GET  /projects/<id>/studio/website-jobs                   - List jobs
- GET  /projects/<id>/studio/websites/<id>/<path:file>      - Serve files
- GET  /projects/<id>/studio/websites/<id>/preview          - Preview site
- GET  /projects/<id>/studio/websites/<id>/download         - Download ZIP
"""
import io
import zipfile
from pathlib import Path
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.utils.path_utils import get_studio_dir


@studio_bp.route('/projects/<project_id>/studio/website', methods=['POST'])
def generate_website(project_id: str):
    """
    Start website generation (background task).

    Request body:
        {
            "source_id": "source-uuid",
            "direction": "optional user direction/preferences"
        }

    Returns:
        202 Accepted with job_id for polling
    """
    from app.services.tool_executors import website_agent_executor

    try:
        data = request.get_json()
        source_id = data.get('source_id')

        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400

        direction = data.get('direction', '')

        # Execute website generation (background task)
        result = website_agent_executor.execute(
            project_id=project_id,
            source_id=source_id,
            direction=direction
        )

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify(result), 202  # Accepted

    except Exception as e:
        current_app.logger.error(f"Error starting website generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start website generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/website-jobs/<job_id>', methods=['GET'])
def get_website_job_status(project_id: str, job_id: str):
    """
    Get status of a website generation job.

    Returns:
        Job object with current status, progress, and results if complete
    """
    try:
        job = studio_index_service.get_website_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        })

    except Exception as e:
        current_app.logger.error(f"Error getting website job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/website-jobs', methods=['GET'])
def list_website_jobs(project_id: str):
    """
    List all website jobs for a project, optionally filtered by source.

    Query params:
        source_id (optional): Filter by source ID

    Returns:
        List of website jobs sorted by created_at descending
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_website_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing website jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/websites/<job_id>/<path:filename>', methods=['GET'])
def get_website_file(project_id: str, job_id: str, filename: str):
    """
    Serve a website file (HTML, CSS, JS, or image asset).

    Supports:
        - HTML pages: index.html, about.html, etc.
        - Stylesheets: styles.css
        - Scripts: script.js
        - Assets: assets/image_1.png, etc.
    """
    try:
        # Get website directory
        website_dir = Path(get_studio_dir(project_id)) / "websites" / job_id

        # Build file path (handles subdirectories like assets/)
        file_path = website_dir / filename

        # Security: Ensure file is within website directory
        if not file_path.resolve().is_relative_to(website_dir.resolve()):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        # Determine MIME type
        mime_type = 'text/html'
        if filename.endswith('.css'):
            mime_type = 'text/css'
        elif filename.endswith('.js'):
            mime_type = 'application/javascript'
        elif filename.endswith('.png'):
            mime_type = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.endswith('.gif'):
            mime_type = 'image/gif'
        elif filename.endswith('.svg'):
            mime_type = 'image/svg+xml'
        elif filename.endswith('.webp'):
            mime_type = 'image/webp'

        return send_file(file_path, mimetype=mime_type)

    except Exception as e:
        current_app.logger.error(f"Error serving website file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve file: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/websites/<job_id>/preview', methods=['GET'])
def preview_website(project_id: str, job_id: str):
    """
    Preview website by serving index.html.

    This endpoint serves the index.html file which will load other files
    (CSS, JS, images) via relative paths that are handled by get_website_file.
    """
    try:
        # Get website directory
        website_dir = Path(get_studio_dir(project_id)) / "websites" / job_id
        index_path = website_dir / "index.html"

        if not index_path.exists():
            return jsonify({
                'success': False,
                'error': 'Website not ready yet or index.html not found'
            }), 404

        return send_file(index_path, mimetype='text/html')

    except Exception as e:
        current_app.logger.error(f"Error previewing website: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview website: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/websites/<job_id>/download', methods=['GET'])
def download_website(project_id: str, job_id: str):
    """
    Download website as ZIP file containing all files.

    Returns:
        ZIP file with all HTML pages, CSS, JS, and image assets
    """
    try:
        # Get job info
        job = studio_index_service.get_website_job(project_id, job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        if job['status'] != 'ready':
            return jsonify({
                'success': False,
                'error': 'Website not ready yet'
            }), 400

        site_name = job.get('site_name', 'Website')
        zip_filename = f"{site_name.replace(' ', '_')}.zip"

        # Get website directory
        website_dir = Path(get_studio_dir(project_id)) / "websites" / job_id

        if not website_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Website files not found'
            }), 404

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files recursively
            for file_path in website_dir.rglob('*'):
                if file_path.is_file():
                    # Get relative path from website_dir
                    arcname = file_path.relative_to(website_dir)
                    zip_file.write(file_path, arcname)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading website: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to download website: {str(e)}'
        }), 500
