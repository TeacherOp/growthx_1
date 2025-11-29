"""
Gemini 2.5 API key validator.

Educational Note: Validates Gemini API keys by making a minimal
text generation request to test if the key is valid.
"""
from typing import Tuple
from google import genai


def validate_gemini_2_5_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Gemini 2.5 API key by making a test text generation request.

    Educational Note: This tests if the API key is valid and enabled for
    Gemini 2.5 (text generation) model.

    Args:
        api_key: The Google API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Create client with the provided key
        client = genai.Client(api_key=api_key)

        # Make a minimal test request with Gemini 2.5 Flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Test"
        )

        # If we get here with a response, the key is valid
        if response.text:
            return True, "Valid Gemini 2.5 API key"
        else:
            return False, "API returned empty response"

    except Exception as e:
        error_message = str(e).lower()

        # Check for common error types
        if 'api key not valid' in error_message or 'invalid' in error_message:
            return False, "Invalid API key"
        elif 'permission' in error_message or 'enabled' in error_message:
            return False, "API not enabled for this key. Enable Gemini API in Google Cloud Console"
        elif 'quota' in error_message:
            return True, "Valid API key (quota exceeded)"
        elif 'rate' in error_message:
            return True, "Valid API key (rate limited)"
        else:
            print(f"Gemini 2.5 validation error: {type(e).__name__}: {str(e)}")
            return False, f"Validation failed: {str(e)[:100]}"
