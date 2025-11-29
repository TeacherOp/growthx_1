"""
Anthropic API key validator.

Educational Note: Validates Anthropic API keys using the token counting API.
This is free (no cost) and fast - much better than making a full message request.
"""
from typing import Tuple
import anthropic


def validate_anthropic_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate an Anthropic API key using the token counting API.

    Educational Note: We use count_tokens instead of messages.create because:
    - Token counting is FREE (no cost)
    - It's faster than generating a response
    - It still validates the API key works

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key == '':
        return False, "API key is empty"

    try:
        # Create client with the provided key
        client = anthropic.Anthropic(api_key=api_key)

        # Use count_tokens API - this is FREE and validates the key
        response = client.messages.count_tokens(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        )

        # If we get here with a token count, the key is valid
        print(f"Validation successful: {response.input_tokens} tokens counted")
        return True, "Valid Anthropic API key"

    except anthropic.AuthenticationError as e:
        return False, "Invalid API key - authentication failed"
    except anthropic.PermissionDeniedError as e:
        return False, "API key lacks required permissions"
    except anthropic.RateLimitError as e:
        # Rate limit actually means the key is valid but rate limited
        return True, "Valid API key (rate limited)"
    except Exception as e:
        # Log the actual error for debugging
        print(f"Anthropic validation error: {type(e).__name__}: {str(e)}")
        return False, f"Validation failed: {str(e)}"
