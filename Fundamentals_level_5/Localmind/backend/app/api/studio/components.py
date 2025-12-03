"""
Component Generation endpoints - Reusable UI components.

Educational Note: Components demonstrate code generation patterns:
1. component_agent_executor orchestrates generation
2. Claude creates self-contained HTML components
3. Components include inline CSS and JavaScript
4. Ready for copy-paste into any project

Component Pattern:
- Single HTML file per component
- All styles inline or in <style> tags
- JavaScript in <script> tags
- No external dependencies

Use Cases:
- Hero sections from product descriptions
- Feature cards from feature lists
- Testimonial sections from reviews
- Pricing tables from pricing data

Routes:
- POST /projects/<id>/studio/components                      - Start generation
- GET  /projects/<id>/studio/component-jobs/<id>             - Job status
- GET  /projects/<id>/studio/component-jobs                  - List jobs
- GET  /projects/<id>/studio/components/<id>/preview/<file>  - Preview HTML
"""
from pathlib import Path
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.tool_executors.component_agent_executor import component_agent_executor
from app.utils.path_utils import get_studio_dir


@studio_bp.route('/projects/<project_id>/studio/components', methods=['POST'])
def generate_components(project_id: str):
    """
    Start component generation via component agent.

    Request Body:
        - source_id: UUID of the source to generate components from (required)
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

        # Execute via component_agent_executor (creates job and launches agent)
        result = component_agent_executor.execute(
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
        current_app.logger.error(f"Error starting component generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start component generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/component-jobs/<job_id>', methods=['GET'])
def get_component_job_status(project_id: str, job_id: str):
    """
    Get the status of a component generation job.

    Response:
        - Job object with status, progress, and generated components
    """
    try:
        job = studio_index_service.get_component_job(project_id, job_id)

        if not job:
            return jsonify({
                'success': False,
                'error': f'Component job {job_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'job': job
        })

    except Exception as e:
        current_app.logger.error(f"Error getting component job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/component-jobs', methods=['GET'])
def list_component_jobs(project_id: str):
    """
    List all component generation jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - List of component jobs (newest first)
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_component_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs
        })

    except Exception as e:
        current_app.logger.error(f"Error listing component jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@studio_bp.route('/projects/<project_id>/studio/components/<job_id>/preview/<filename>', methods=['GET'])
def preview_component(project_id: str, job_id: str, filename: str):
    """
    Serve component HTML for preview (iframe).

    Response:
        - HTML file for rendering in iframe
    """
    try:
        component_dir = get_studio_dir(project_id) / "components" / job_id
        filepath = component_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Component file not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(component_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        return send_file(
            filepath,
            mimetype='text/html',
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving component preview: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve component: {str(e)}'
        }), 500
