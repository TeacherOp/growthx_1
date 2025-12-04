"""
Presentation Generator endpoints - AI-generated PowerPoint presentations.

Educational Note: Presentation generation demonstrates HTML-to-PPTX workflow:
1. presentation_agent generates HTML slides with Tailwind CSS
2. Playwright captures screenshots at 1920x1080
3. python-pptx stitches screenshots into a PPTX file

Agent Architecture:
- Uses presentation_agent_executor for orchestration
- Agent has tools for planning, styling, and slide creation
- Sequential slide generation for design consistency
- Export pipeline: HTML -> PNG -> PPTX

Output Structure:
- slides/base-styles.css (brand colors/fonts)
- slides/slide_01.html, slide_02.html, ... (HTML slides)
- screenshots/slide_01.png, slide_02.png, ... (captured screenshots)
- Presentation.pptx (final output)

Routes:
- POST /projects/<id>/studio/presentation                      - Start generation
- GET  /projects/<id>/studio/presentation-jobs/<id>            - Job status
- GET  /projects/<id>/studio/presentation-jobs                 - List jobs
- GET  /projects/<id>/studio/presentations/<id>/slides/<file>  - Serve slide HTML
- GET  /projects/<id>/studio/presentations/<id>/preview        - Preview slide
- GET  /projects/<id>/studio/presentations/<id>/download       - Download PPTX
"""
import io
import zipfile
from pathlib import Path
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.utils.path_utils import get_studio_dir


@studio_bp.route('/projects/<project_id>/studio/presentation', methods=['POST'])
def generate_presentation(project_id: str):
    """
    Start presentation generation (background task).

    Request body:
        {
            "source_id": "source-uuid",
            "direction": "optional user direction/preferences"
        }

    Returns:
        202 Accepted with job_id for polling
    """
    from app.services.tool_executors import presentation_agent_executor

    try:
        data = request.get_json()
        source_id = data.get('source_id')

        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400

        direction = data.get('direction', '')

        # Execute presentation generation (background task)
        result = presentation_agent_executor.execute(
            project_id=project_id,
            source_id=source_id,
            direction=direction
        )

        if not result.get('success'):
            return jsonify(result), 400

        return jsonify(result), 202  # Accepted

    except Exception as e:
        current_app.logger.error(f"Error starting presentation generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start presentation generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentation-jobs/<job_id>', methods=['GET'])
def get_presentation_job_status(project_id: str, job_id: str):
    """
    Get status of a presentation generation job.

    Returns:
        Job object with current status, progress, and results if complete
    """
    try:
        job = studio_index_service.get_presentation_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting presentation job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentation-jobs', methods=['GET'])
def list_presentation_jobs(project_id: str):
    """
    List all presentation jobs for a project, optionally filtered by source.

    Query params:
        source_id (optional): Filter by source ID

    Returns:
        List of presentation jobs sorted by created_at descending
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_presentation_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing presentation jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentations/<job_id>/slides/<path:filename>', methods=['GET'])
def get_presentation_slide(project_id: str, job_id: str, filename: str):
    """
    Serve a slide file (HTML or CSS).

    Supports:
        - HTML slides: slide_01.html, slide_02.html, etc.
        - Stylesheets: base-styles.css
    """
    try:
        # Get slides directory
        slides_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id / "slides"

        # Build file path
        file_path = slides_dir / filename

        # Security: Ensure file is within slides directory
        if not file_path.resolve().is_relative_to(slides_dir.resolve()):
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

        return send_file(file_path, mimetype=mime_type)

    except Exception as e:
        current_app.logger.error(f"Error serving slide file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve file: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentations/<job_id>/screenshots/<path:filename>', methods=['GET'])
def get_presentation_screenshot(project_id: str, job_id: str, filename: str):
    """
    Serve a screenshot image file (PNG).

    Educational Note: Screenshots are captured by Playwright at 1920x1080
    and used to create the PPTX. They provide a reliable preview.
    """
    try:
        # Get screenshots directory
        screenshots_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id / "screenshots"

        # Build file path
        file_path = screenshots_dir / filename

        # Security: Ensure file is within screenshots directory
        if not file_path.resolve().is_relative_to(screenshots_dir.resolve()):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Screenshot not found'
            }), 404

        return send_file(file_path, mimetype='image/png')

    except Exception as e:
        current_app.logger.error(f"Error serving screenshot file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve screenshot: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentations/<job_id>/preview', methods=['GET'])
def preview_presentation(project_id: str, job_id: str):
    """
    Preview presentation by returning slide info and first slide.

    Query params:
        slide (optional): Slide number to preview (default: 1)

    Returns:
        JSON with slide info and file URL for iframe viewing
    """
    try:
        job = studio_index_service.get_presentation_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        slide_files = job.get('slide_files', [])
        if not slide_files:
            return jsonify({
                'success': False,
                'error': 'No slides available'
            }), 404

        # Get requested slide number (1-indexed)
        slide_num = request.args.get('slide', 1, type=int)
        slide_num = max(1, min(slide_num, len(slide_files)))

        slide_file = slide_files[slide_num - 1]
        slide_url = f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/slides/{slide_file}"

        return jsonify({
            'success': True,
            'total_slides': len(slide_files),
            'current_slide': slide_num,
            'slide_file': slide_file,
            'slide_url': slide_url,
            'presentation_title': job.get('presentation_title', 'Presentation'),
            'export_status': job.get('export_status'),
            'pptx_available': job.get('pptx_file') is not None
        })

    except Exception as e:
        current_app.logger.error(f"Error previewing presentation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview presentation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentations/<job_id>/download', methods=['GET'])
def download_presentation(project_id: str, job_id: str):
    """
    Download presentation as PPTX file.

    Query params:
        format (optional): 'pptx' (default) or 'zip' (includes HTML source)

    Returns:
        PPTX file or ZIP file with all assets
    """
    try:
        # Get job info
        job = studio_index_service.get_presentation_job(project_id, job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        download_format = request.args.get('format', 'pptx')

        if download_format == 'pptx':
            # Download PPTX file
            pptx_file = job.get('pptx_file')
            if not pptx_file:
                return jsonify({
                    'success': False,
                    'error': 'PPTX file not ready yet. Export may still be processing.'
                }), 400

            pptx_path = Path(pptx_file)
            if not pptx_path.exists():
                return jsonify({
                    'success': False,
                    'error': 'PPTX file not found'
                }), 404

            pptx_filename = job.get('pptx_filename', 'Presentation.pptx')

            return send_file(
                pptx_path,
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                as_attachment=True,
                download_name=pptx_filename
            )

        elif download_format == 'zip':
            # Download as ZIP with all source files
            presentation_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id

            if not presentation_dir.exists():
                return jsonify({
                    'success': False,
                    'error': 'Presentation files not found'
                }), 404

            title = job.get('presentation_title', 'Presentation')
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            if not safe_title:
                safe_title = "Presentation"
            zip_filename = f"{safe_title}_source.zip"

            # Create ZIP in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add all files recursively
                for file_path in presentation_dir.rglob('*'):
                    if file_path.is_file():
                        # Get relative path from presentation_dir
                        arcname = file_path.relative_to(presentation_dir)
                        zip_file.write(file_path, arcname)

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=zip_filename
            )

        else:
            return jsonify({
                'success': False,
                'error': f'Invalid format: {download_format}. Use "pptx" or "zip".'
            }), 400

    except Exception as e:
        current_app.logger.error(f"Error downloading presentation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to download presentation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/presentations/<job_id>', methods=['DELETE'])
def delete_presentation(project_id: str, job_id: str):
    """
    Delete a presentation and its files.

    Returns:
        Success status
    """
    try:
        import shutil

        # Get job to verify it exists
        job = studio_index_service.get_presentation_job(project_id, job_id)
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        # Delete files
        presentation_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id
        if presentation_dir.exists():
            shutil.rmtree(presentation_dir)

        # Delete from index
        deleted = studio_index_service.delete_presentation_job(project_id, job_id)

        return jsonify({
            'success': deleted,
            'message': 'Presentation deleted' if deleted else 'Failed to delete from index'
        })

    except Exception as e:
        current_app.logger.error(f"Error deleting presentation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete presentation: {str(e)}'
        }), 500
