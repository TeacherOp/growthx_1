"""
ValidationService - Unified interface for all API key validators.

Educational Note: This class provides a single interface for validating
API keys for various services. Each validator is in its own file to
keep the code manageable.
"""
from typing import Tuple, Dict, Optional

from app.services.app_settings.validation.anthropic_validator import validate_anthropic_key
from app.services.app_settings.validation.elevenlabs_validator import validate_elevenlabs_key
from app.services.app_settings.validation.openai_validator import validate_openai_key
from app.services.app_settings.validation.gemini_validator import validate_gemini_2_5_key
from app.services.app_settings.validation.nano_banana_validator import validate_nano_banana_key
from app.services.app_settings.validation.veo_validator import validate_veo_key
from app.services.app_settings.validation.tavily_validator import validate_tavily_key
from app.services.app_settings.validation.pinecone_validator import validate_pinecone_key


class ValidationService:
    """
    Unified service for validating API keys.

    Educational Note: This class delegates to individual validator functions.
    Each validator makes the smallest possible request to minimize costs
    while verifying the key works.
    """

    def validate_anthropic_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate an Anthropic API key."""
        return validate_anthropic_key(api_key)

    def validate_elevenlabs_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate an ElevenLabs API key."""
        return validate_elevenlabs_key(api_key)

    def validate_openai_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate an OpenAI API key."""
        return validate_openai_key(api_key)

    def validate_gemini_2_5_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate a Gemini 2.5 API key."""
        return validate_gemini_2_5_key(api_key)

    def validate_nano_banana_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate a Nano Banana (Image Gen) API key."""
        return validate_nano_banana_key(api_key)

    def validate_veo_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate a VEO (Video Gen) API key."""
        return validate_veo_key(api_key)

    def validate_tavily_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate a Tavily API key."""
        return validate_tavily_key(api_key)

    def validate_pinecone_key(self, api_key: str) -> Tuple[bool, str, Optional[Dict[str, str]]]:
        """Validate a Pinecone API key and auto-create index if needed."""
        return validate_pinecone_key(api_key)
