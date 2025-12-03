"""
Infographic endpoints - AI-generated visual summaries.

Educational Note: Infographics demonstrate visual content synthesis:
1. Claude analyzes source and extracts key points
2. Creates structured visual descriptions
3. Gemini Imagen generates the infographic image
4. Single comprehensive image output

Visual Design Pattern:
- Infographics organize information visually
- Include icons, sections, and visual flow
- Colors indicate categories/importance
- Text is minimal, visual is primary

Generation Pipeline:
1. Extract key facts and statistics
2. Organize into visual hierarchy
3. Generate image prompt for Gemini
4. Create and store image file

Routes:
- POST /projects/<id>/studio/infographic           - Start generation
- GET  /projects/<id>/studio/infographic-jobs/<id> - Job status
- GET  /projects/<id>/studio/infographic-jobs      - List jobs
- GET  /projects/<id>/studio/infographics/<file>   - Serve image file
"""
import uuid
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.studio_services.infographic_service import infographic_service, get_studio_infographics_dir
from app.services.source_services import source_index_service
from app.services.integrations.google.imagen_service import imagen_service
from app.services.background_services.task_service import task_service


@studio_bp.route('/projects/<project_id>/studio/infographic', methods=['POST'])
def generate_infographic(project_id: str):
    """
    Start infographic generation as a background task.

    Educational Note: Infographics are visual summaries that organize source
    content in an educational format with icons, sections, and visual flow.

    Request Body:
        - source_id: UUID of the source to generate infographic from (required)
        - direction: Optional guidance for what to focus on

    Response:
        - success: Boolean
        - job_id: ID for polling status
        - message: Status message
    """
    try:
        data = request.get_json() or {}

        source_id = data.get('source_id')
        if not source_id:
            return jsonify({
                'success': False,
                'error': 'source_id is required'
            }), 400

        direction = data.get('direction', 'Create an informative infographic summarizing the key concepts.')

        # Check if Gemini is configured
        if not imagen_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured. Please add it in App Settings.'
            }), 400

        # Get source info for the job record
        source = source_index_service.get_source_from_index(project_id, source_id)
        if not source:
            return jsonify({
                'success': False,
                'error': f'Source not found: {source_id}'
            }), 404

        source_name = source.get('name', 'Unknown')

        # Create job record
        job_id = str(uuid.uuid4())
        studio_index_service.create_infographic_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="infographic",
            target_id=job_id,
            callable_func=infographic_service.generate_infographic,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Infographic generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting infographic generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start infographic generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/infographic-jobs/<job_id>', methods=['GET'])
def get_infographic_job_status(project_id: str, job_id: str):
    """
    Get the status of an infographic generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, image (when ready)
    """
    try:
        job = studio_index_service.get_infographic_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Job not found: {job_id}'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting infographic job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/infographic-jobs', methods=['GET'])
def list_infographic_jobs(project_id: str):
    """
    List all infographic jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_infographic_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing infographic jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/infographics/<filename>', methods=['GET'])
def get_infographic_file(project_id: str, filename: str):
    """
    Serve an infographic image file.

    Response:
        - Image file (png/jpg) with appropriate headers
    """
    try:
        infographics_dir = get_studio_infographics_dir(project_id)
        filepath = infographics_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Infographic not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(infographics_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        # Determine mimetype
        mimetype = 'image/png' if filename.endswith('.png') else 'image/jpeg'

        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving infographic file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve infographic file: {str(e)}'
        }), 500
