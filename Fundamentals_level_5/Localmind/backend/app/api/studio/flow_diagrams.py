"""
Flow Diagram endpoints - AI-generated Mermaid diagrams.

Educational Note: Flow diagrams demonstrate visual representation of processes
and relationships using Mermaid.js syntax:
1. Claude analyzes source content
2. Identifies processes, workflows, or relationships
3. Creates appropriate Mermaid diagram syntax
4. Frontend renders using Mermaid library

Diagram Types:
- Flowcharts (graph TD/LR)
- Sequence diagrams
- State diagrams
- ER diagrams
- Class diagrams
- Pie charts, Gantt charts, etc.

Routes:
- POST /projects/<id>/studio/flow-diagram           - Start generation
- GET  /projects/<id>/studio/flow-diagram-jobs/<id> - Job status
- GET  /projects/<id>/studio/flow-diagram-jobs      - List jobs
"""
import uuid
from flask import jsonify, request, current_app
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.studio_services.flow_diagram_service import flow_diagram_service
from app.services.source_services import source_index_service
from app.services.background_services.task_service import task_service


@studio_bp.route('/projects/<project_id>/studio/flow-diagram', methods=['POST'])
def generate_flow_diagram(project_id: str):
    """
    Start flow diagram generation as a background task.

    Educational Note: Flow diagrams are generated from source content using
    Claude to create Mermaid diagram syntax for visual process mapping.

    Request Body:
        - source_id: UUID of the source to generate diagram from (required)
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

        direction = data.get('direction', 'Create a diagram showing the key processes and relationships.')

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
        studio_index_service.create_flow_diagram_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="flow_diagram",
            target_id=job_id,
            callable_func=flow_diagram_service.generate_flow_diagram,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Flow diagram generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting flow diagram generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start flow diagram generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/flow-diagram-jobs/<job_id>', methods=['GET'])
def get_flow_diagram_job_status(project_id: str, job_id: str):
    """
    Get the status of a flow diagram generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, mermaid_syntax (when ready)
    """
    try:
        job = studio_index_service.get_flow_diagram_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting flow diagram job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/flow-diagram-jobs', methods=['GET'])
def list_flow_diagram_jobs(project_id: str):
    """
    List all flow diagram jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_flow_diagram_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing flow diagram jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500
