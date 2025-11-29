"""
ElevenLabs API key validator.

Educational Note: Validates ElevenLabs API keys by checking user info
via the /user endpoint - a lightweight way to verify the key.
"""
from typing import Tuple
import requests


def validate_elevenlabs_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate an ElevenLabs API key by checking user info.

    Educational Note: We use the /user endpoint which returns
    user subscription info - a lightweight way to verify the key.

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Check user info endpoint - lightweight validation
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api_key},
            timeout=10
        )

        if response.status_code == 200:
            user_data = response.json()
            # Extract subscription tier for more informative message
            subscription = user_data.get('subscription', {})
            tier = subscription.get('tier', 'unknown')
            return True, f"Valid ElevenLabs API key (tier: {tier})"
        elif response.status_code == 401:
            return False, "Invalid API key - authentication failed"
        elif response.status_code == 429:
            return True, "Valid API key (rate limited)"
        else:
            return False, f"Validation failed: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Validation timed out - try again"
    except requests.exceptions.RequestException as e:
        print(f"ElevenLabs validation error: {type(e).__name__}: {str(e)}")
        return False, f"Validation failed: {str(e)}"
