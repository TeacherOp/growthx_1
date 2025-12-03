"""
Audio Overview endpoints - TTS-based audio summaries.

Educational Note: Audio overviews demonstrate text-to-speech (TTS) integration:
1. AI generates a conversational script from source content
2. ElevenLabs API converts script to natural-sounding audio
3. Audio file is stored and served for playback

TTS Integration Pattern:
- ElevenLabs provides high-quality voice synthesis
- Voices can be selected from their library (professional narrators)
- Audio is generated in MP3 format for web playback

Background Job Flow:
1. POST /audio-overview creates job, returns job_id
2. audio_overview_service runs in background thread
3. Frontend polls GET /jobs/{job_id} for status
4. When ready, audio_url points to GET /audio/<filename>

Routes:
- POST /projects/<id>/studio/audio-overview  - Start generation
- GET  /projects/<id>/studio/jobs/<id>       - Job status
- GET  /projects/<id>/studio/jobs            - List jobs
- GET  /projects/<id>/studio/audio/<file>    - Serve audio file
- GET  /studio/tts/status                    - Check TTS config
- GET  /studio/tts/voices                    - List available voices
"""
import uuid
from flask import jsonify, request, current_app, send_file
from app.api.studio import studio_bp
from app.services.studio_services import audio_overview_service, studio_index_service
from app.services.source_services import source_index_service
from app.services.integrations.elevenlabs import tts_service
from app.services.background_services.task_service import task_service
from app.utils.path_utils import get_studio_audio_dir


@studio_bp.route('/projects/<project_id>/studio/audio-overview', methods=['POST'])
def generate_audio_overview(project_id: str):
    """
    Start audio overview generation as a background task.

    Educational Note: This endpoint is non-blocking:
    1. Creates a job record with status="pending"
    2. Submits background task via task_service
    3. Returns job_id immediately for status polling

    Request Body:
        - source_id: UUID of the source to generate overview for (required)
        - direction: Optional guidance for the script style/focus

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

        direction = data.get('direction', 'Create an engaging audio overview of this content.')

        # Check if TTS is configured
        if not tts_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'ElevenLabs API key not configured. Please add it in App Settings.'
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
        studio_index_service.create_audio_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="audio_overview",
            target_id=job_id,
            callable_func=audio_overview_service.generate_audio_overview,
            project_id=project_id,
            source_id=source_id,
            job_id=job_id,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Audio generation started',
            'source_name': source_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting audio overview: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start audio generation: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/jobs/<job_id>', methods=['GET'])
def get_audio_job_status(project_id: str, job_id: str):
    """
    Get the status of an audio generation job.

    Educational Note: Frontend polls this endpoint to check progress.
    When status="ready", the audio_url field contains the playback URL.

    Response:
        - success: Boolean
        - job: Job record with status, progress, audio_url (when ready)
    """
    try:
        job = studio_index_service.get_audio_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/jobs', methods=['GET'])
def list_audio_jobs(project_id: str):
    """
    List all audio generation jobs for a project.

    Query Parameters:
        - source_id: Optional filter by source

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        source_id = request.args.get('source_id')
        jobs = studio_index_service.list_audio_jobs(project_id, source_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@studio_bp.route('/projects/<project_id>/studio/audio/<filename>', methods=['GET'])
def get_audio_file(project_id: str, filename: str):
    """
    Serve an audio file from the studio audio directory.

    Educational Note: This endpoint serves generated audio files for playback.
    The frontend can use this URL as the src for an <audio> element.

    Response:
        - Audio file (mp3) with appropriate headers for streaming
    """
    try:
        audio_dir = get_studio_audio_dir(project_id)
        audio_path = audio_dir / filename

        if not audio_path.exists():
            return jsonify({
                'success': False,
                'error': f'Audio file not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            audio_path.resolve().relative_to(audio_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        return send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False
        )

    except Exception as e:
        current_app.logger.error(f"Error serving audio file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve audio file: {str(e)}'
        }), 500


@studio_bp.route('/studio/tts/status', methods=['GET'])
def get_tts_status():
    """
    Check if TTS (ElevenLabs) is configured.

    Educational Note: This endpoint allows the frontend to check
    if audio generation is available before showing the option.

    Response:
        - configured: Boolean indicating if ElevenLabs API key is set
    """
    try:
        return jsonify({
            'success': True,
            'configured': tts_service.is_configured()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking TTS status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check TTS status'
        }), 500


@studio_bp.route('/studio/tts/voices', methods=['GET'])
def list_tts_voices():
    """
    List available TTS voices from ElevenLabs.

    Educational Note: This endpoint allows users to choose
    their preferred voice for audio overviews.

    Response:
        - success: Boolean
        - voices: List of voice info (id, name, category, preview_url)
    """
    try:
        if not tts_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'ElevenLabs API key not configured'
            }), 400

        result = tts_service.list_voices()
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        current_app.logger.error(f"Error listing TTS voices: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list voices: {str(e)}'
        }), 500
