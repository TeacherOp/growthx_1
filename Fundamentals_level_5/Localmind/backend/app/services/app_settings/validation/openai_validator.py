"""
OpenAI API key validator.

Educational Note: Validates OpenAI API keys by making a minimal
embeddings request - this is cost-effective and tests the key.
"""
from typing import Tuple
import openai


def validate_openai_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate an OpenAI API key by making a test embeddings request.

    Educational Note: We use the embeddings endpoint since that's what
    we'll use this key for (text-embedding-3-small model for RAG).
    This is a lightweight way to verify the key works.

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Create client with the provided key
        client = openai.OpenAI(api_key=api_key)

        # Make a minimal embeddings request to test the key
        # Using text-embedding-3-small which is cost-effective
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test",
            encoding_format="float"
        )

        # If we get here with data, the key is valid
        if response.data and len(response.data) > 0:
            return True, "Valid OpenAI API key"
        else:
            return False, "API returned empty response"

    except openai.AuthenticationError as e:
        return False, "Invalid API key - authentication failed"
    except openai.PermissionDeniedError as e:
        return False, "API key lacks required permissions"
    except openai.RateLimitError as e:
        # Rate limit actually means the key is valid but rate limited
        return True, "Valid API key (rate limited)"
    except openai.InsufficientQuotaError as e:
        # Insufficient quota means the key is valid but has no credits
        return True, "Valid API key (insufficient quota)"
    except Exception as e:
        # Log the actual error for debugging
        print(f"OpenAI validation error: {type(e).__name__}: {str(e)}")
        return False, f"Validation failed: {str(e)}"
