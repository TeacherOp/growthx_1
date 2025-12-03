"""
Quiz endpoints - AI-generated multiple choice questions.

Educational Note: Quizzes demonstrate assessment content generation:
1. Claude analyzes source content
2. Identifies testable concepts
3. Generates questions with answer options
4. Marks correct answers for auto-grading

Question Structure Pattern:
- Each question has: question, options[], correct_answer
- Options are shuffled to prevent pattern recognition
- Difficulty levels can be specified
- Explanations included for learning

Use Cases:
- Self-assessment after reading
- Practice tests from course materials
- Knowledge verification before exams

Routes:
- POST /projects/<id>/studio/quiz           - Start generation
- GET  /projects/<id>/studio/quiz-jobs/<id> - Job status
- GET  /projects/<id>/studio/quiz-jobs      - List jobs
"""
import uuid
from flask import jsonify, request, current_app
from app.api.studio import studio_bp
from app.services.studio_services import studio_index_service
from app.services.studio_services.quiz_service import quiz_service
from app.services.source_services import source_index_service
from app.services.background_services.task_service import task_service


@studio_bp.route('/projects/<project_id>/studio/quiz', methods=['POST'])
def generate_quiz(project_id: str):
    """
    Start quiz generation as a background task.

    Educational Note: Quiz questions are generated from source content using
    Claude to create multiple choice questions for testing knowledge.

    Request Body:
        - source_id: UUID of the source to generate quiz from (required)
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

        direction = data.get('direction', 'Create quiz questions covering the key concepts.')

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
        studio_index_service.create_quiz_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="quiz",
            target_id=job_id,
            callable_func=quiz_service.generate_quiz,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Quiz generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting quiz generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start quiz generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/quiz-jobs/<job_id>', methods=['GET'])
def get_quiz_job_status(project_id: str, job_id: str):
    """
    Get the status of a quiz generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, questions (when ready)
    """
    try:
        job = studio_index_service.get_quiz_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting quiz job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/quiz-jobs', methods=['GET'])
def list_quiz_jobs(project_id: str):
    """
    List all quiz jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_quiz_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing quiz jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500
