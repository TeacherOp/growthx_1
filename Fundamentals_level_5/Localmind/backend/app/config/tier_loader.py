"""
Tier Configuration - Centralized API tier management.

Educational Note: This module manages rate limit tiers for various APIs:
- Anthropic (Claude) - PDF processing, chat
- OpenAI - Embeddings
- Pinecone - Vector database operations
- Future APIs...

Each API has different rate limits based on usage tier (free, paid, enterprise).
This module provides a single source of truth for tier configurations.
"""
import os
from typing import Dict, Any, Optional
from enum import Enum


class APIProvider(Enum):
    """Supported API providers with tier-based rate limits."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    PINECONE = "pinecone"


# Anthropic (Claude) tier configuration
# Educational Note: Based on Anthropic's rate limits per tier
# Workers can be higher than CPU cores because this is I/O-bound
ANTHROPIC_TIERS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Tier 1 (Free)",
        "description": "~12 pages/min (50 RPM, 10K output tokens/min)",
        "max_workers": 4,
        "requests_per_minute": 50,
        "input_tokens_per_minute": 50000,
        "output_tokens_per_minute": 10000,
        "pages_per_minute": 10,  # Conservative estimate for PDF processing
    },
    2: {
        "name": "Tier 2",
        "description": "~130 pages/min (1000 RPM, 90K output tokens/min)",
        "max_workers": 16,
        "requests_per_minute": 1000,
        "input_tokens_per_minute": 450000,
        "output_tokens_per_minute": 90000,
        "pages_per_minute": 100,
    },
    3: {
        "name": "Tier 3",
        "description": "~285 pages/min (2000 RPM, 200K output tokens/min)",
        "max_workers": 24,
        "requests_per_minute": 2000,
        "input_tokens_per_minute": 1000000,
        "output_tokens_per_minute": 200000,
        "pages_per_minute": 200,
    },
    4: {
        "name": "Tier 4+",
        "description": "~1600 pages/min (4000 RPM, 800K output tokens/min)",
        "max_workers": 80,
        "requests_per_minute": 4000,
        "input_tokens_per_minute": 4000000,
        "output_tokens_per_minute": 800000,
        "pages_per_minute": 1500,
    },
}


# OpenAI tier configuration (for embeddings)
# Educational Note: OpenAI has different rate limits for embeddings vs chat
OPENAI_TIERS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Tier 1 (Free)",
        "description": "500 RPM, 10K tokens/min",
        "max_workers": 4,
        "requests_per_minute": 500,
        "tokens_per_minute": 10000,
    },
    2: {
        "name": "Tier 2",
        "description": "5000 RPM, 2M tokens/min",
        "max_workers": 16,
        "requests_per_minute": 5000,
        "tokens_per_minute": 2000000,
    },
    3: {
        "name": "Tier 3",
        "description": "10000 RPM, 5M tokens/min",
        "max_workers": 24,
        "requests_per_minute": 10000,
        "tokens_per_minute": 5000000,
    },
    4: {
        "name": "Tier 4+",
        "description": "30000 RPM, 10M tokens/min",
        "max_workers": 40,
        "requests_per_minute": 30000,
        "tokens_per_minute": 10000000,
    },
}


# Pinecone tier configuration
# Educational Note: Pinecone rate limits depend on pod type and index size
PINECONE_TIERS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Starter (Free)",
        "description": "100 upserts/sec, 5 queries/sec",
        "max_workers": 4,
        "upserts_per_second": 100,
        "queries_per_second": 5,
    },
    2: {
        "name": "Standard",
        "description": "500 upserts/sec, 50 queries/sec",
        "max_workers": 8,
        "upserts_per_second": 500,
        "queries_per_second": 50,
    },
    3: {
        "name": "Enterprise",
        "description": "1000 upserts/sec, 200 queries/sec",
        "max_workers": 16,
        "upserts_per_second": 1000,
        "queries_per_second": 200,
    },
    4: {
        "name": "Enterprise+",
        "description": "5000 upserts/sec, 1000 queries/sec",
        "max_workers": 32,
        "upserts_per_second": 5000,
        "queries_per_second": 1000,
    },
}


# Map provider to tier configs
TIER_CONFIGS: Dict[str, Dict[int, Dict[str, Any]]] = {
    APIProvider.ANTHROPIC.value: ANTHROPIC_TIERS,
    APIProvider.OPENAI.value: OPENAI_TIERS,
    APIProvider.PINECONE.value: PINECONE_TIERS,
}

# Environment variable names for each provider's tier
TIER_ENV_VARS: Dict[str, str] = {
    APIProvider.ANTHROPIC.value: "ANTHROPIC_TIER",
    APIProvider.OPENAI.value: "OPENAI_TIER",
    APIProvider.PINECONE.value: "PINECONE_TIER",
}


def get_tier(provider: str) -> int:
    """
    Get the current tier for a provider from environment.

    Args:
        provider: API provider name (anthropic, openai, pinecone)

    Returns:
        Tier number (1-4), defaults to 1
    """
    env_var = TIER_ENV_VARS.get(provider, f"{provider.upper()}_TIER")
    tier_str = os.getenv(env_var, "1")

    try:
        tier = int(tier_str)
    except ValueError:
        tier = 1

    # Ensure tier is valid
    provider_tiers = TIER_CONFIGS.get(provider, {})
    if tier not in provider_tiers:
        tier = 1

    return tier


def get_tier_config(provider: str, tier: Optional[int] = None) -> Dict[str, Any]:
    """
    Get tier configuration for a provider.

    Args:
        provider: API provider name (anthropic, openai, pinecone)
        tier: Specific tier number, or None to read from environment

    Returns:
        Tier configuration dict with name, description, max_workers, etc.
    """
    if tier is None:
        tier = get_tier(provider)

    provider_tiers = TIER_CONFIGS.get(provider, {})

    # Return tier config or default to tier 1
    return provider_tiers.get(tier, provider_tiers.get(1, {
        "name": "Unknown",
        "description": "Unknown tier",
        "max_workers": 4,
    }))


def get_all_tiers(provider: str) -> Dict[int, Dict[str, Any]]:
    """
    Get all tier configurations for a provider.

    Args:
        provider: API provider name

    Returns:
        Dict mapping tier number to tier config
    """
    return TIER_CONFIGS.get(provider, {})


def get_max_workers(provider: str, tier: Optional[int] = None) -> int:
    """
    Get max workers for a provider's current tier.

    Args:
        provider: API provider name
        tier: Specific tier, or None to read from environment

    Returns:
        Maximum number of parallel workers
    """
    config = get_tier_config(provider, tier)
    return config.get("max_workers", 4)


# Convenience functions for specific providers
def get_anthropic_config(tier: Optional[int] = None) -> Dict[str, Any]:
    """Get Anthropic tier configuration."""
    return get_tier_config(APIProvider.ANTHROPIC.value, tier)


def get_openai_config(tier: Optional[int] = None) -> Dict[str, Any]:
    """Get OpenAI tier configuration."""
    return get_tier_config(APIProvider.OPENAI.value, tier)


def get_pinecone_config(tier: Optional[int] = None) -> Dict[str, Any]:
    """Get Pinecone tier configuration."""
    return get_tier_config(APIProvider.PINECONE.value, tier)
