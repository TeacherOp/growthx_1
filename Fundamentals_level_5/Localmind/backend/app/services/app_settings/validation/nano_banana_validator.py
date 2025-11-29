"""
Nano Banana (Image Generation) API key validator.

Educational Note: Validates API keys for Gemini 3 Pro Image Preview model
by making a minimal image generation request.
"""
from typing import Tuple
from google import genai
from google.genai import types


def validate_nano_banana_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Nano Banana (Image Generation) API key.

    Educational Note: This tests if the API key is valid and enabled for
    Gemini 3 Pro Image Preview model. We use minimal settings for fastest test.

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

        model = "gemini-3-pro-image-preview"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Test image")],
            ),
        ]

        # Minimal config for fastest test
        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                image_size="1K",  # Smallest size for fast test
            ),
        )

        # Try to generate a single image as a test
        response = None
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (chunk.candidates and
                chunk.candidates[0].content and
                chunk.candidates[0].content.parts):
                response = chunk
                break  # We only need one chunk to confirm it works

        if response:
            return True, "Valid Nano Banana (Image Gen) API key"
        else:
            return False, "API returned no image data"

    except Exception as e:
        error_message = str(e).lower()

        if 'api key not valid' in error_message or 'invalid' in error_message:
            return False, "Invalid API key"
        elif 'permission' in error_message or 'enabled' in error_message:
            return False, "Image generation API not enabled. Enable Gemini API in Google Cloud Console"
        elif 'quota' in error_message:
            return True, "Valid API key (quota exceeded)"
        elif 'rate' in error_message:
            return True, "Valid API key (rate limited)"
        else:
            print(f"Nano Banana validation error: {type(e).__name__}: {str(e)}")
            return False, f"Validation failed: {str(e)[:100]}"
