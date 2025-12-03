"""
Mind Map endpoints - AI-generated concept hierarchies.

Educational Note: Mind maps demonstrate hierarchical content extraction:
1. Claude analyzes source content
2. Identifies main topics and subtopics
3. Creates a tree structure of concepts
4. Returns structured JSON for visual rendering

Node Structure Pattern:
- Each node has: id, label, children[]
- Root node is the main topic
- Branches represent subtopics/details
- Frontend renders as interactive diagram

Visualization:
- Frontend uses libraries like react-flow or d3
- Nodes are positioned using layout algorithms
- Users can expand/collapse branches
- Colors indicate topic categories

Routes:
- POST /projects/<id>/studio/mind-map           - Start generation
- GET  /projects/<id>/studio/mind-map-jobs/<id> - Job status
- GET  /projects/<id>/studio/mind-map-jobs      - List jobs
"""
import uuid
from flask import jsonify, request, current_app
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.studio_services.mind_map_service import mind_map_service
from app.services.source_services import source_index_service
from app.services.background_services.task_service import task_service


@studio_bp.route('/projects/<project_id>/studio/mind-map', methods=['POST'])
def generate_mind_map(project_id: str):
    """
    Start mind map generation as a background task.

    Educational Note: Mind maps are generated from source content using
    Claude to create hierarchical node structures for visual concept mapping.

    Request Body:
        - source_id: UUID of the source to generate mind map from (required)
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

        direction = data.get('direction', 'Create a mind map covering the key concepts and their relationships.')

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
        studio_index_service.create_mind_map_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="mind_map",
            target_id=job_id,
            callable_func=mind_map_service.generate_mind_map,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Mind map generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting mind map generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start mind map generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/mind-map-jobs/<job_id>', methods=['GET'])
def get_mind_map_job_status(project_id: str, job_id: str):
    """
    Get the status of a mind map generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, nodes (when ready)
    """
    try:
        job = studio_index_service.get_mind_map_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting mind map job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/mind-map-jobs', methods=['GET'])
def list_mind_map_jobs(project_id: str):
    """
    List all mind map jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_mind_map_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing mind map jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500
