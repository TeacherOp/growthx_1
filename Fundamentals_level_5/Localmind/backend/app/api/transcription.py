"""
API endpoints for ElevenLabs speech-to-text configuration.

Educational Note: These endpoints provide configuration for the frontend
to connect directly to ElevenLabs' real-time WebSocket transcription API.
The actual transcription happens client-side for lowest latency.
"""
from flask import jsonify, current_app
from app.api import api_bp
from app.services.integrations.elevenlabs import TranscriptionService

# Initialize service
transcription_service = TranscriptionService()


@api_bp.route('/transcription/config', methods=['GET'])
def get_transcription_config():
    """
    Get ElevenLabs configuration for real-time transcription.

    Educational Note: This endpoint generates a single-use token and embeds it
    in the WebSocket URL. The token expires after 15 minutes. Frontend should
    request new config for each recording session.

    Security Note: The API key never leaves the server. Only the single-use
    token is embedded in the WebSocket URL for authentication.

    Response:
        - websocket_url: Full WebSocket URL with embedded token
        - model_id: The transcription model ID
        - sample_rate: Recommended audio sample rate (16000 Hz)
        - encoding: Audio encoding format (pcm_s16le)
    """
    try:
        config = transcription_service.get_elevenlabs_config()

        return jsonify({
            'success': True,
            **config
        }), 200

    except ValueError as e:
        # API key not configured
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error getting transcription config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get transcription configuration'
        }), 500


@api_bp.route('/transcription/status', methods=['GET'])
def get_transcription_status():
    """
    Check if ElevenLabs transcription is configured.

    Educational Note: This is a lightweight endpoint to check if the
    ElevenLabs API key is set without exposing the actual key.
    Useful for UI to show/hide transcription features.

    Response:
        - configured: Boolean indicating if API key is set
    """
    try:
        is_configured = transcription_service.is_configured()

        return jsonify({
            'success': True,
            'configured': is_configured
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking transcription status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check transcription status'
        }), 500
