"""
Email Template endpoints - AI-generated HTML email templates.

Educational Note: Email templates demonstrate agent-based generation:
1. email_agent_executor orchestrates the generation
2. Claude creates HTML structure and content
3. Gemini generates header/banner images
4. Complete package: HTML + images

Agent Pattern:
- Uses email_agent_executor for orchestration
- Agent has tools for HTML generation and image creation
- Multi-step process with intermediate results
- Final output is a complete email template

Output Structure:
- HTML file with inline styles (email-safe)
- Image files for headers/banners
- All files stored in job-specific folder
- ZIP download available for full package

Routes:
- POST /projects/<id>/studio/email-template              - Start generation
- GET  /projects/<id>/studio/email-jobs/<id>             - Job status
- GET  /projects/<id>/studio/email-jobs                  - List jobs
- GET  /projects/<id>/studio/email-templates/<file>      - Serve file
- GET  /projects/<id>/studio/email-templates/<id>/preview  - Preview HTML
- GET  /projects/<id>/studio/email-templates/<id>/download - Download ZIP
"""
import io
import zipfile
from pathlib import Path
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.tool_executors.email_agent_executor import email_agent_executor
from app.utils.path_utils import get_studio_dir


@studio_bp.route('/projects/<project_id>/studio/email-template', methods=['POST'])
def generate_email_template(project_id: str):
    """
    Start email template generation via email agent.

    Request Body:
        - source_id: UUID of the source to generate template from (required)
        - direction: User's direction/guidance (optional)

    Response:
        - 202 Accepted with job_id for polling
    """
    try:
        data = request.get_json()

        # Validate input
        source_id = data.get('source_id')
        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400

        direction = data.get('direction', '')

        # Execute via email_agent_executor (creates job and launches agent)
        result = email_agent_executor.execute(
            project_id=project_id,
            source_id=source_id,
            direction=direction
        )

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify({
            'success': True,
            'job_id': result['job_id'],
            'status': result['status'],
            'message': result['message']
        }), 202

    except Exception as e:
        current_app.logger.error(f"Error starting email template generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start email template generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/email-jobs/<job_id>', methods=['GET'])
def get_email_job_status(project_id: str, job_id: str):
    """
    Get the status of an email template generation job.

    Response:
        - Job object with status, progress, and generated content
    """
    try:
        job = studio_index_service.get_email_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Email job {job_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        })

    except Exception as e:
        current_app.logger.error(f"Error getting email job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/email-jobs', methods=['GET'])
def list_email_jobs(project_id: str):
    """
    List all email template jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - List of email jobs (newest first)
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_email_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing email jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/email-templates/<filename>', methods=['GET'])
def get_email_template_file(project_id: str, filename: str):
    """
    Serve an email template file (HTML or image).

    Response:
        - HTML file or image file with appropriate headers
    """
    try:
        email_dir = get_studio_dir(project_id) / "email_templates"
        filepath = email_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'File not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(email_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        # Determine mimetype
        if filename.endswith('.html'):
            mimetype = 'text/html'
        elif filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        else:
            mimetype = 'application/octet-stream'

        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving email template file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve file: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/email-templates/<job_id>/preview', methods=['GET'])
def preview_email_template(project_id: str, job_id: str):
    """
    Serve email template HTML for preview (iframe).

    Response:
        - HTML file for rendering in iframe
    """
    try:
        # Get job to find HTML file
        job = studio_index_service.get_email_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Email job {job_id} not found'
            }), 404

        html_file = job.get('html_file')
        if not html_file:
            return jsonify({
                'success': False,
                'error': 'Email template not yet generated'
            }), 404

        email_dir = get_studio_dir(project_id) / "email_templates"
        filepath = email_dir / html_file

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'HTML file not found: {html_file}'
            }), 404

        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error previewing email template: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview template: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/email-templates/<job_id>/download', methods=['GET'])
def download_email_template(project_id: str, job_id: str):
    """
    Download email template as ZIP file (HTML + images).

    Response:
        - ZIP file containing HTML and all images
    """
    try:
        # Get job to find files
        job = studio_index_service.get_email_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Email job {job_id} not found'
            }), 404

        html_file = job.get('html_file')
        if not html_file:
            return jsonify({
                'success': False,
                'error': 'Email template not yet generated'
            }), 404

        email_dir = get_studio_dir(project_id) / "email_templates"

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add HTML file
            html_path = email_dir / html_file
            if html_path.exists():
                zip_file.write(html_path, html_file)

            # Add image files
            images = job.get('images', [])
            for image_info in images:
                image_filename = image_info.get('filename')
                if image_filename:
                    image_path = email_dir / image_filename
                    if image_path.exists():
                        zip_file.write(image_path, image_filename)

        zip_buffer.seek(0)

        # Generate filename
        template_name = job.get('template_name', 'email_template')
        safe_name = "".join(c for c in template_name if c.isalnum() or c in (' ', '_', '-')).strip()
        zip_filename = f"{safe_name}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading email template: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to download template: {str(e)}'
        }), 500
