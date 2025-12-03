"""
Processing settings endpoints - API tier configuration.

Educational Note: API providers have rate limits that vary by subscription tier.
This module lets users configure their tier so the app can optimize:

1. Parallel Processing:
   - Higher tiers = more concurrent workers
   - Affects PDF extraction, PPTX processing, etc.
   - Tier 1 (free): 4 workers, 10 pages/min
   - Tier 4 (enterprise): 80 workers, 1500 pages/min

2. Rate Limiting:
   - Each tier has different requests-per-minute limits
   - App automatically throttles to stay within limits
   - Prevents 429 (rate limit) errors

Why Tiers Matter for LLM Apps:
- Free tier users get slow but functional experience
- Paid tier users get faster processing
- Enterprise users can process large PDFs quickly

Anthropic Tier Limits (as of 2024):
- Tier 1: 60 RPM, 40K output tokens/min
- Tier 2: 4000 RPM, 400K output/min
- Tier 3: 8000 RPM, 800K output/min
- Tier 4: 16000 RPM, 1.6M output/min

The tier config is stored in .env as ANTHROPIC_TIER (1-4).

Routes:
- GET  /settings/processing - Get current tier config
- POST /settings/processing - Update tier
"""
from flask import jsonify, request, current_app
from app.api.settings import settings_bp
from app.services.app_settings import EnvService
from app.config import (
    get_tier,
    get_tier_config,
    APIProvider,
    ANTHROPIC_TIERS,
)

# Initialize service
env_service = EnvService()


@settings_bp.route('/settings/processing', methods=['GET'])
def get_processing_settings():
    """
    Get processing settings including Anthropic tier configuration.

    Educational Note: Returns current tier and all available tiers so
    the UI can show a tier selector with descriptions of each level.

    Returns:
        {
            "success": true,
            "settings": {
                "anthropic_tier": 2,
                "tier_config": {
                    "max_workers": 16,
                    "pages_per_minute": 100,
                    "description": "Standard tier"
                }
            },
            "available_tiers": [
                {"tier": 1, "max_workers": 4, ...},
                {"tier": 2, "max_workers": 16, ...},
                ...
            ]
        }
    """
    try:
        # Get current tier using centralized config
        current_tier = get_tier(APIProvider.ANTHROPIC.value)
        tier_config = get_tier_config(APIProvider.ANTHROPIC.value, current_tier)

        return jsonify({
            'success': True,
            'settings': {
                'anthropic_tier': current_tier,
                'tier_config': tier_config,
            },
            'available_tiers': [
                {'tier': tier, **config}
                for tier, config in ANTHROPIC_TIERS.items()
            ]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting processing settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/settings/processing', methods=['POST'])
def update_processing_settings():
    """
    Update processing settings.

    Educational Note: Saves the selected tier to .env file. The tier
    affects how parallel processing operates - higher tier = more
    concurrent API calls allowed.

    Important: Changing tier takes effect immediately after env reload.
    No app restart required.

    Request Body:
        { "anthropic_tier": 2 }

    Returns:
        {
            "success": true,
            "message": "Processing settings updated successfully",
            "settings": { ... updated config ... }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Update Anthropic tier if provided
        if 'anthropic_tier' in data:
            tier = int(data['anthropic_tier'])

            # Validate tier
            if tier not in ANTHROPIC_TIERS:
                return jsonify({
                    'success': False,
                    'error': f'Invalid tier. Must be one of: {list(ANTHROPIC_TIERS.keys())}'
                }), 400

            env_service.set_key('ANTHROPIC_TIER', str(tier))
            current_app.logger.info(f"Updated ANTHROPIC_TIER to {tier}")

        # Reload to pick up changes
        env_service.reload_env()

        # Return updated settings
        current_tier = get_tier(APIProvider.ANTHROPIC.value)
        tier_config = get_tier_config(APIProvider.ANTHROPIC.value, current_tier)

        return jsonify({
            'success': True,
            'message': 'Processing settings updated successfully',
            'settings': {
                'anthropic_tier': current_tier,
                'tier_config': tier_config,
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating processing settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
