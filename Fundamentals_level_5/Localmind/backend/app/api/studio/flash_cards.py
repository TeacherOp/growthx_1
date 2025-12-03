"""
Flash Card endpoints - AI-generated learning cards.

Educational Note: Flash cards demonstrate structured content extraction:
1. Claude analyzes source content
2. Identifies key concepts and facts
3. Generates question/answer pairs
4. Returns structured JSON for frontend rendering

Tool-Based Extraction Pattern:
- Claude is given a tool for submitting flash cards
- Tool enforces JSON structure: {front, back, category}
- This ensures consistent, parseable output
- Typically generates 10-20 cards per source

Use Cases:
- Study material from lecture notes
- Key terms from technical documents
- Concept review from research papers

Routes:
- POST /projects/<id>/studio/flash-cards           - Start generation
- GET  /projects/<id>/studio/flash-card-jobs/<id>  - Job status
- GET  /projects/<id>/studio/flash-card-jobs       - List jobs
"""
import uuid
from flask import jsonify, request, current_app
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.studio_services.flash_cards_service import flash_cards_service
from app.services.source_services import source_index_service
from app.services.background_services.task_service import task_service


@studio_bp.route('/projects/<project_id>/studio/flash-cards', methods=['POST'])
def generate_flash_cards(project_id: str):
    """
    Start flash card generation as a background task.

    Educational Note: Flash cards are generated from source content using
    Claude to create question/answer pairs for learning and memorization.

    Request Body:
        - source_id: UUID of the source to generate cards from (required)
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

        direction = data.get('direction', 'Create flash cards covering the key concepts.')

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
        studio_index_service.create_flash_card_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="flash_cards",
            target_id=job_id,
            callable_func=flash_cards_service.generate_flash_cards,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Flash card generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting flash card generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start flash card generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/flash-card-jobs/<job_id>', methods=['GET'])
def get_flash_card_job_status(project_id: str, job_id: str):
    """
    Get the status of a flash card generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, cards (when ready)
    """
    try:
        job = studio_index_service.get_flash_card_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting flash card job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/flash-card-jobs', methods=['GET'])
def list_flash_card_jobs(project_id: str):
    """
    List all flash card jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_flash_card_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing flash card jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500
