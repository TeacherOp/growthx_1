"""
Transcription Service - ElevenLabs Speech-to-Text support.

Educational Note: This service generates single-use tokens for the frontend
to connect to ElevenLabs' real-time WebSocket transcription API.

Security Note: We never expose the API key to the frontend. Instead, we
generate a short-lived token that the frontend uses for WebSocket auth.
"""
import os
import requests


class TranscriptionService:
    """
    Service class for ElevenLabs speech-to-text configuration.

    Educational Note: ElevenLabs real-time transcription uses WebSocket
    connections directly from the browser. This service provides the
    configuration needed for the frontend to establish that connection.
    """

    # ElevenLabs WebSocket endpoint and model
    WEBSOCKET_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
    DEFAULT_MODEL = "scribe_v2_realtime"

    # Supported audio configurations for ElevenLabs
    SAMPLE_RATE = 16000  # 16kHz recommended
    ENCODING = "pcm_s16le"  # 16-bit PCM little-endian

    def __init__(self):
        """Initialize the transcription service."""
        pass

    def generate_scribe_token(self) -> str:
        """
        Generate a single-use token for ElevenLabs realtime transcription.

        Educational Note: ElevenLabs requires a single-use token for client-side
        WebSocket connections. This token is generated server-side using the API key,
        and expires after 15 minutes. This keeps the API key secure on the server.

        Returns:
            Single-use token string

        Raises:
            ValueError: If API key is not configured
            Exception: If token generation fails
        """
        api_key = os.getenv('ELEVENLABS_API_KEY')

        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")

        # Request a single-use token from ElevenLabs
        response = requests.post(
            "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
            headers={"xi-api-key": api_key},
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Failed to generate token: {response.text}")

        data = response.json()
        return data.get("token")

    def get_elevenlabs_config(self) -> dict:
        """
        Get ElevenLabs configuration for frontend WebSocket connection.

        Educational Note: This generates a fresh single-use token and provides
        the WebSocket URL with all necessary parameters. The token expires
        after 15 minutes, so the frontend should request a new config when needed.

        Returns:
            Dictionary with token and WebSocket configuration
        """
        # Generate a fresh single-use token
        token = self.generate_scribe_token()

        # Build WebSocket URL with token and parameters
        # Educational Note: Using VAD (Voice Activity Detection) for automatic
        # speech segmentation - commits transcript when silence is detected
        websocket_url = (
            f"{self.WEBSOCKET_URL}"
            f"?model_id={self.DEFAULT_MODEL}"
            f"&token={token}"
            f"&audio_format=pcm_{self.SAMPLE_RATE}"
            f"&commit_strategy=vad"
        )

        # Educational Note: Only return the token and config needed by frontend
        # Never expose the API key to the client - it stays server-side only
        return {
            "websocket_url": websocket_url,
            "model_id": self.DEFAULT_MODEL,
            "sample_rate": self.SAMPLE_RATE,
            "encoding": self.ENCODING,
        }

    def is_configured(self) -> bool:
        """
        Check if ElevenLabs API key is configured.

        Returns:
            True if API key is set, False otherwise
        """
        return bool(os.getenv('ELEVENLABS_API_KEY'))
