"""
API endpoints for managing application settings and API keys.

Educational Note: This module handles CRUD operations for API keys
stored in the .env file, with automatic Flask app reload when keys change.
"""
from flask import jsonify, request, current_app
from app.api import api_bp
from app.services.env_service import EnvService
from app.services.validation_service import ValidationService

# Initialize services
env_service = EnvService()
validation_service = ValidationService()


@api_bp.route('/settings/api-keys', methods=['GET'])
def get_api_keys():
    """
    Get all API keys (with values masked for security).

    Educational Note: We never send actual API key values to the frontend.
    Instead, we send masked versions (showing only first/last few characters).
    """
    try:
        # Define the API keys we manage
        api_keys_config = [
            {'id': 'ANTHROPIC_API_KEY', 'name': 'Anthropic API', 'description': 'Claude AI models for chat', 'category': 'ai', 'required': True},
            {'id': 'ELEVENLABS_API_KEY', 'name': 'ElevenLabs API', 'description': 'Real-time speech-to-text transcription', 'category': 'ai', 'required': True},
            {'id': 'OPENAI_API_KEY', 'name': 'OpenAI API', 'description': 'OpenAI models for embeddings (text-embedding-3-small)', 'category': 'ai'},
            {'id': 'GEMINI_2_5_API_KEY', 'name': 'Gemini 2.5', 'description': 'Google Gemini 2.5 text generation (may share key with other Google services)', 'category': 'ai'},
            {'id': 'NANO_BANANA_API_KEY', 'name': 'Nano Banana', 'description': 'Gemini 3 Pro Image generation (may share key with other Google services)', 'category': 'ai'},
            {'id': 'VEO_API_KEY', 'name': 'VEO', 'description': 'Google VEO 2.0 video generation (may share key with other Google services)', 'category': 'ai'},
            {'id': 'PINECONE_API_KEY', 'name': 'Pinecone API Key', 'description': 'Vector database - auto-creates "growthxlearn" index on validation', 'category': 'storage'},
            {'id': 'PINECONE_INDEX_NAME', 'name': 'Pinecone Index Name', 'description': 'Auto-managed (set to "growthxlearn" after API key validation)', 'category': 'storage'},
            {'id': 'PINECONE_REGION', 'name': 'Pinecone Region', 'description': 'Auto-managed (set to "us-east-1" after API key validation)', 'category': 'storage'},
            {'id': 'TAVILY_API_KEY', 'name': 'Tavily AI', 'description': 'Web search AI', 'category': 'utility'},
        ]

        # Get current values from .env
        api_keys = []
        for key_config in api_keys_config:
            value = env_service.get_key(key_config['id'])
            masked_value = env_service.mask_key(value) if value else ''

            api_keys.append({
                'id': key_config['id'],
                'name': key_config['name'],
                'description': key_config['description'],
                'category': key_config['category'],
                'required': key_config.get('required', False),
                'value': masked_value,
                'is_set': bool(value)
            })

        return jsonify({
            'success': True,
            'api_keys': api_keys
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting API keys: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/api-keys', methods=['POST'])
def update_api_keys():
    """
    Update API keys in the .env file and trigger Flask reload.

    Educational Note: This endpoint:
    1. Validates the API keys
    2. Updates the .env file
    3. Triggers a Flask app reload to load new keys
    """
    try:
        data = request.get_json()
        if not data or 'api_keys' not in data:
            return jsonify({
                'success': False,
                'error': 'No API keys provided'
            }), 400

        api_keys = data['api_keys']

        current_app.logger.info(f"Received {len(api_keys)} keys to update")

        # Update each API key in .env
        updated_count = 0
        for key_data in api_keys:
            key_id = key_data.get('id')
            value = key_data.get('value', '')

            current_app.logger.info(f"Processing key {key_id}, value length: {len(value)}")

            # Skip if value is masked (starts with asterisks)
            if value and not value.startswith('***'):
                current_app.logger.info(f"Setting key {key_id} in .env file")
                env_service.set_key(key_id, value)
                updated_count += 1
                current_app.logger.info(f"Successfully updated API key: {key_id}")
            else:
                current_app.logger.info(f"Skipping masked/empty key: {key_id}")

        # Save the .env file (though set_key already saves)
        env_service.save()

        # Reload environment variables
        current_app.logger.info(f"Reloading environment variables...")
        env_service.reload_env()

        # Verify the keys were saved
        for key_data in api_keys:
            key_id = key_data.get('id')
            value = key_data.get('value', '')
            if value and not value.startswith('***'):
                saved_value = env_service.get_key(key_id)
                if saved_value:
                    current_app.logger.info(f"Verified {key_id} is saved in environment")
                else:
                    current_app.logger.error(f"Failed to verify {key_id} in environment!")

        current_app.logger.info(f"Updated {updated_count} API keys")

        # If in debug mode with auto-reload, the server will restart automatically
        # Otherwise, we need to signal for a restart
        if current_app.config.get('DEBUG'):
            current_app.logger.info("Environment updated. Flask will auto-reload...")
        else:
            # In production, you might want to handle this differently
            current_app.logger.warning("Environment updated. Manual restart may be required.")

        return jsonify({
            'success': True,
            'message': 'API keys updated successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating API keys: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/api-keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """
    Delete a specific API key from the .env file.

    Educational Note: This removes the key entirely from the .env file,
    not just clearing its value. For Pinecone, we also remove related
    configuration (index name and region).
    """
    try:
        # Delete the main key
        env_service.delete_key(key_id)

        # If deleting Pinecone API key, also delete related config
        if key_id == 'PINECONE_API_KEY':
            current_app.logger.info("Deleting related Pinecone configuration...")
            env_service.delete_key('PINECONE_INDEX_NAME')
            env_service.delete_key('PINECONE_REGION')
            current_app.logger.info("Pinecone configuration deleted")

        env_service.save()
        env_service.reload_env()

        return jsonify({
            'success': True,
            'message': f'API key {key_id} deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting API key {key_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/settings/api-keys/validate', methods=['POST'])
def validate_api_key():
    """
    Validate an API key by making a test request to the service.

    Educational Note: This endpoint tests if an API key works by making
    a minimal request to each service. This helps users verify their keys
    before saving.
    """
    try:
        data = request.get_json()
        if not data or 'key_id' not in data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing key_id or value'
            }), 400

        key_id = data['key_id']
        value = data['value']

        # Skip validation for masked values
        if value.startswith('***'):
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Key already set'
            }), 200

        # Validate based on key type
        is_valid = False
        message = ''

        current_app.logger.info(f"Validating key: {key_id}")

        if key_id == 'ANTHROPIC_API_KEY':
            # Test Anthropic API
            is_valid, message = validation_service.validate_anthropic_key(value)
        elif key_id == 'ELEVENLABS_API_KEY':
            # Test ElevenLabs API
            is_valid, message = validation_service.validate_elevenlabs_key(value)
        elif key_id == 'OPENAI_API_KEY':
            # Test OpenAI API (for embeddings)
            is_valid, message = validation_service.validate_openai_key(value)
        elif key_id == 'GEMINI_2_5_API_KEY':
            # Test Gemini 2.5 text generation
            is_valid, message = validation_service.validate_gemini_2_5_key(value)
        elif key_id == 'NANO_BANANA_API_KEY':
            # Test Nano Banana image generation
            is_valid, message = validation_service.validate_nano_banana_key(value)
        elif key_id == 'VEO_API_KEY':
            # Test VEO video generation
            is_valid, message = validation_service.validate_veo_key(value)
        elif key_id == 'TAVILY_API_KEY':
            # Test Tavily search API
            is_valid, message = validation_service.validate_tavily_key(value)
        elif key_id == 'PINECONE_API_KEY':
            # Test Pinecone API and create/check index
            is_valid, message, index_details = validation_service.validate_pinecone_key(value)

            # If validation succeeds, automatically save index details to .env
            if is_valid and index_details:
                try:
                    current_app.logger.info(f"Saving Pinecone index details: {index_details}")
                    env_service.set_key('PINECONE_INDEX_NAME', index_details['index_name'])
                    env_service.set_key('PINECONE_REGION', index_details['region'])
                    env_service.save()
                    current_app.logger.info("Pinecone index details saved successfully")
                except Exception as e:
                    current_app.logger.error(f"Failed to save Pinecone index details: {e}")
        elif key_id in ['PINECONE_INDEX_NAME', 'PINECONE_REGION']:
            # These are auto-managed, just accept them
            is_valid = bool(value)
            message = 'Configuration accepted (auto-managed)'
        else:
            # Default validation
            is_valid = bool(value)
            message = 'Key provided' if is_valid else 'Key is empty'

        current_app.logger.info(f"Validation result for {key_id}: {is_valid} - {message}")

        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': message
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error validating API key: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Processing Settings Endpoints
# ============================================================================

from app.utils.tier_config import (
    get_tier,
    get_tier_config,
    get_all_tiers,
    APIProvider,
    ANTHROPIC_TIERS,
)


@api_bp.route('/settings/processing', methods=['GET'])
def get_processing_settings():
    """
    Get processing settings including Anthropic tier configuration.

    Educational Note: Processing settings control how parallel operations
    (like PDF page extraction) are performed. The tier determines how
    many concurrent API calls can be made based on rate limits.
    Uses centralized tier_config utility for all API providers.
    """
    try:
        # Get current tier using the centralized utility
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


@api_bp.route('/settings/processing', methods=['POST'])
def update_processing_settings():
    """
    Update processing settings.

    Educational Note: This endpoint saves the selected tier to .env file,
    which affects how parallel PDF processing operates.
    Uses centralized tier_config utility for validation.
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
            if tier not in ANTHROPIC_TIERS:
                return jsonify({
                    'success': False,
                    'error': f'Invalid tier. Must be one of: {list(ANTHROPIC_TIERS.keys())}'
                }), 400

            env_service.set_key('ANTHROPIC_TIER', str(tier))
            current_app.logger.info(f"Updated ANTHROPIC_TIER to {tier}")

        env_service.reload_env()

        # Return updated settings using centralized utility
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