"""
API endpoints for Studio features.

Educational Note: Studio features generate content from sources:
- Audio Overview: Generates spoken audio summaries using TTS
- Ad Creative: Generates ad images using Gemini
- Flash Cards: Generates learning flash cards using Claude
- (Future) Deep Dive: Interactive conversation modes
- (Future) Mind Map: Visual representation of content

Studio features run as background tasks:
1. POST creates job and returns job_id immediately
2. Frontend polls GET /jobs/{job_id} for status
3. When status="ready", content is available
"""
import uuid
from flask import jsonify, request, current_app, send_file
from app.api import api_bp
from app.services.studio_services import audio_overview_service, studio_index_service
from app.services.studio_services.ad_creative_service import ad_creative_service, get_studio_creatives_dir
from app.services.studio_services.flash_cards_service import flash_cards_service
from app.services.studio_services.mind_map_service import mind_map_service
from app.services.studio_services.quiz_service import quiz_service
from app.services.studio_services.social_posts_service import social_posts_service, get_studio_social_dir
from app.services.source_services import source_index_service
from app.services.integrations.elevenlabs import tts_service
from app.services.integrations.google.imagen_service import imagen_service
from app.services.background_services.task_service import task_service
from app.utils.path_utils import get_studio_audio_dir


@api_bp.route('/projects/<project_id>/studio/audio-overview', methods=['POST'])
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


@api_bp.route('/projects/<project_id>/studio/jobs/<job_id>', methods=['GET'])
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


@api_bp.route('/projects/<project_id>/studio/jobs', methods=['GET'])
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


@api_bp.route('/projects/<project_id>/studio/audio/<filename>', methods=['GET'])
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


@api_bp.route('/studio/tts/status', methods=['GET'])
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


@api_bp.route('/studio/tts/voices', methods=['GET'])
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


# =============================================================================
# Ad Creative Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/studio/ad-creative', methods=['POST'])
def generate_ad_creative(project_id: str):
    """
    Start ad creative generation as a background task.

    Educational Note: This endpoint is non-blocking:
    1. Creates a job record with status="pending"
    2. Submits background task via task_service
    3. Returns job_id immediately for status polling

    Request Body:
        - product_name: Name of the product to create ads for (required)
        - direction: Optional guidance for the ad style/focus

    Response:
        - success: Boolean
        - job_id: ID for polling status
        - message: Status message
    """
    try:
        data = request.get_json() or {}

        product_name = data.get('product_name')
        if not product_name:
            return jsonify({
                'success': False,
                'error': 'product_name is required'
            }), 400

        direction = data.get('direction', 'Create compelling ad creatives for Facebook and Instagram.')

        # Check if Gemini is configured
        if not imagen_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured. Please add it in App Settings.'
            }), 400

        # Create job record
        job_id = str(uuid.uuid4())
        studio_index_service.create_ad_job(
            project_id=project_id,
            job_id=job_id,
            product_name=product_name,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="ad_creative",
            target_id=job_id,
            callable_func=ad_creative_service.generate_ad_creatives,
            project_id=project_id,
            job_id=job_id,
            product_name=product_name,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Ad creative generation started',
            'product_name': product_name
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting ad creative: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start ad creative generation: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/ad-jobs/<job_id>', methods=['GET'])
def get_ad_job_status(project_id: str, job_id: str):
    """
    Get the status of an ad creative generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, images (when ready)
    """
    try:
        job = studio_index_service.get_ad_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting ad job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/ad-jobs', methods=['GET'])
def list_ad_jobs(project_id: str):
    """
    List all ad creative jobs for a project.

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        jobs = studio_index_service.list_ad_jobs(project_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing ad jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/creatives/<filename>', methods=['GET'])
def get_creative_file(project_id: str, filename: str):
    """
    Serve an ad creative image file.

    Response:
        - Image file (png/jpg) with appropriate headers
    """
    try:
        creatives_dir = get_studio_creatives_dir(project_id)
        filepath = creatives_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Creative file not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(creatives_dir.resolve())
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
        current_app.logger.error(f"Error serving creative file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve creative file: {str(e)}'
        }), 500


@api_bp.route('/studio/gemini/status', methods=['GET'])
def get_gemini_status():
    """
    Check if Gemini (Google AI) is configured.

    Response:
        - configured: Boolean indicating if Gemini API key is set
    """
    try:
        return jsonify({
            'success': True,
            'configured': imagen_service.is_configured()
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking Gemini status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check Gemini status'
        }), 500


# =============================================================================
# Flash Card Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/studio/flash-cards', methods=['POST'])
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


@api_bp.route('/projects/<project_id>/studio/flash-card-jobs/<job_id>', methods=['GET'])
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


@api_bp.route('/projects/<project_id>/studio/flash-card-jobs', methods=['GET'])
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


# =============================================================================
# Mind Map Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/studio/mind-map', methods=['POST'])
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


@api_bp.route('/projects/<project_id>/studio/mind-map-jobs/<job_id>', methods=['GET'])
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


@api_bp.route('/projects/<project_id>/studio/mind-map-jobs', methods=['GET'])
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


# =============================================================================
# Quiz Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/studio/quiz', methods=['POST'])
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


@api_bp.route('/projects/<project_id>/studio/quiz-jobs/<job_id>', methods=['GET'])
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


@api_bp.route('/projects/<project_id>/studio/quiz-jobs', methods=['GET'])
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


# =============================================================================
# Social Post Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/studio/social-posts', methods=['POST'])
def generate_social_posts(project_id: str):
    """
    Start social post generation as a background task.

    Educational Note: Social posts are generated with platform-specific images
    and copy for LinkedIn, Facebook/Instagram, and Twitter/X.

    Request Body:
        - topic: Topic/content to create posts about (required)
        - direction: Optional guidance for the style/focus

    Response:
        - success: Boolean
        - job_id: ID for polling status
        - message: Status message
    """
    try:
        data = request.get_json() or {}

        topic = data.get('topic')
        if not topic:
            return jsonify({
                'success': False,
                'error': 'topic is required'
            }), 400

        direction = data.get('direction', 'Create engaging social media posts for this topic.')

        # Check if Gemini is configured
        if not imagen_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured. Please add it in App Settings.'
            }), 400

        # Create job record
        job_id = str(uuid.uuid4())
        studio_index_service.create_social_post_job(
            project_id=project_id,
            job_id=job_id,
            topic=topic,
            direction=direction
        )

        # Submit background task
        task_service.submit_task(
            task_type="social_posts",
            target_id=job_id,
            callable_func=social_posts_service.generate_social_posts,
            project_id=project_id,
            job_id=job_id,
            topic=topic,
            direction=direction
        )

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Social post generation started',
            'topic': topic
        }), 202  # 202 Accepted - processing started

    except Exception as e:
        current_app.logger.error(f"Error starting social post generation: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start social post generation: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/social-post-jobs/<job_id>', methods=['GET'])
def get_social_post_job_status(project_id: str, job_id: str):
    """
    Get the status of a social post generation job.

    Response:
        - success: Boolean
        - job: Job record with status, progress, posts (when ready)
    """
    try:
        job = studio_index_service.get_social_post_job(project_id, job_id)

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
        current_app.logger.error(f"Error getting social post job status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get job status: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/social-post-jobs', methods=['GET'])
def list_social_post_jobs(project_id: str):
    """
    List all social post jobs for a project.

    Response:
        - success: Boolean
        - jobs: List of job records
    """
    try:
        jobs = studio_index_service.list_social_post_jobs(project_id)

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing social post jobs: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list jobs: {str(e)}'
        }), 500


@api_bp.route('/projects/<project_id>/studio/social/<filename>', methods=['GET'])
def get_social_file(project_id: str, filename: str):
    """
    Serve a social post image file.

    Response:
        - Image file (png/jpg) with appropriate headers
    """
    try:
        social_dir = get_studio_social_dir(project_id)
        filepath = social_dir / filename

        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Social image not found: {filename}'
            }), 404

        # Validate the file is within the expected directory (security)
        try:
            filepath.resolve().relative_to(social_dir.resolve())
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
        current_app.logger.error(f"Error serving social file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to serve social file: {str(e)}'
        }), 500
