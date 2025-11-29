"""
VEO (Video Generation) API key validator.

Educational Note: Validates API keys for VEO 2.0 video generation model
by starting a minimal video generation request.
"""
from typing import Tuple
from google import genai
from google.genai import types


def validate_veo_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate VEO (Video Generation) API key.

    Educational Note: This tests if the API key is valid and enabled for
    VEO 2.0 video generation model. We use minimal settings for fastest test.

    Args:
        api_key: The Google API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Create client with the provided key
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key
        )

        MODEL = "veo-2.0-generate-001"

        # Minimal config for fastest test
        video_config = types.GenerateVideosConfig(
            aspect_ratio="16:9",
            number_of_videos=1,
            duration_seconds=5,  # Minimum duration for fastest test
            person_generation="ALLOW_ALL",
        )

        # Start video generation (we don't wait for completion, just check if it starts)
        operation = client.models.generate_videos(
            model=MODEL,
            prompt="Test video",
            config=video_config,
        )

        # If we get an operation object, the key is valid
        if operation:
            return True, "Valid VEO (Video Gen) API key"
        else:
            return False, "API did not accept video generation request"

    except Exception as e:
        error_message = str(e).lower()

        if 'api key not valid' in error_message or 'invalid' in error_message:
            return False, "Invalid API key"
        elif 'permission' in error_message or 'enabled' in error_message:
            return False, "Video generation API not enabled. Enable VEO API in Google Cloud Console"
        elif 'quota' in error_message:
            return True, "Valid API key (quota exceeded)"
        elif 'rate' in error_message:
            return True, "Valid API key (rate limited)"
        else:
            print(f"VEO validation error: {type(e).__name__}: {str(e)}")
            return False, f"Validation failed: {str(e)[:100]}"
