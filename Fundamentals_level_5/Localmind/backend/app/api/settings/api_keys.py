"""
API Key management endpoints.

Educational Note: Managing API keys securely is critical for any LLM application.
This module demonstrates several security patterns:

1. Key Masking:
   - Never send full API keys to frontend
   - Show only first/last few characters: "sk-...xyz"
   - Detect masked values on update (skip re-saving)

2. Key Validation:
   - Test keys before saving by making minimal API calls
   - Each service has its own validation logic
   - Validation happens server-side (keys never leave backend)

3. .env Storage:
   - Keys stored in .env file (not database)
   - .env is gitignored (never committed)
   - Changes trigger environment reload

4. Auto-Configuration:
   - Some keys trigger automatic setup (e.g., Pinecone creates index)
   - Related settings saved automatically (index name, region)

Supported API Keys:
- ANTHROPIC_API_KEY: Claude AI models
- ELEVENLABS_API_KEY: Speech-to-text
- OPENAI_API_KEY: Embeddings
- PINECONE_API_KEY: Vector database (+ auto-creates index)
- TAVILY_API_KEY: Web search
- GOOGLE_CLIENT_ID/SECRET: Google Drive OAuth
- GEMINI/VEO/NANO_BANANA: Google AI services

Routes:
- GET    /settings/api-keys           - List all keys (masked)
- POST   /settings/api-keys           - Update keys
- DELETE /settings/api-keys/<key_id>  - Delete a key
- POST   /settings/api-keys/validate  - Validate a key
"""
from flask import jsonify, request, current_app
from app.api.settings import settings_bp
from app.services.app_settings import EnvService, ValidationService

# Initialize services
env_service = EnvService()
validation_service = ValidationService()

# API keys configuration - defines all managed keys
API_KEYS_CONFIG = [
    {
        'id': 'ANTHROPIC_API_KEY',
        'name': 'Anthropic API',
        'description': 'Claude AI models for chat',
        'category': 'ai',
        'required': True
    },
    {
        'id': 'ELEVENLABS_API_KEY',
        'name': 'ElevenLabs API',
        'description': 'Real-time speech-to-text transcription',
        'category': 'ai',
        'required': True
    },
    {
        'id': 'OPENAI_API_KEY',
        'name': 'OpenAI API',
        'description': 'OpenAI models for embeddings (text-embedding-3-small)',
        'category': 'ai'
    },
    {
        'id': 'GEMINI_2_5_API_KEY',
        'name': 'Gemini 2.5',
        'description': 'Google Gemini 2.5 text generation',
        'category': 'ai'
    },
    {
        'id': 'NANO_BANANA_API_KEY',
        'name': 'Nano Banana',
        'description': 'Gemini 3 Pro Image generation',
        'category': 'ai'
    },
    {
        'id': 'VEO_API_KEY',
        'name': 'VEO',
        'description': 'Google VEO 2.0 video generation',
        'category': 'ai'
    },
    {
        'id': 'PINECONE_API_KEY',
        'name': 'Pinecone API Key',
        'description': 'Vector database - auto-creates index on validation',
        'category': 'storage'
    },
    {
        'id': 'PINECONE_INDEX_NAME',
        'name': 'Pinecone Index Name',
        'description': 'Auto-managed (set after API key validation)',
        'category': 'storage'
    },
    {
        'id': 'PINECONE_REGION',
        'name': 'Pinecone Region',
        'description': 'Auto-managed (set after API key validation)',
        'category': 'storage'
    },
    {
        'id': 'TAVILY_API_KEY',
        'name': 'Tavily AI',
        'description': 'Web search AI',
        'category': 'utility'
    },
    {
        'id': 'GOOGLE_CLIENT_ID',
        'name': 'Google Client ID',
        'description': 'Google OAuth client ID for Drive integration',
        'category': 'utility'
    },
    {
        'id': 'GOOGLE_CLIENT_SECRET',
        'name': 'Google Client Secret',
        'description': 'Google OAuth client secret for Drive integration',
        'category': 'utility'
    },
]


@settings_bp.route('/settings/api-keys', methods=['GET'])
def get_api_keys():
    """
    Get all API keys (with values masked for security).

    Educational Note: We never send actual API key values to the frontend.
    Instead, we send masked versions (showing only first/last few characters).
    This prevents accidental exposure via browser dev tools, logs, etc.

    Returns:
        {
            "success": true,
            "api_keys": [
                {
                    "id": "ANTHROPIC_API_KEY",
                    "name": "Anthropic API",
                    "description": "...",
                    "category": "ai",
                    "required": true,
                    "value": "sk-a...xyz",  # masked
                    "is_set": true
                },
                ...
            ]
        }
    """
    try:
        api_keys = []
        for key_config in API_KEYS_CONFIG:
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


@settings_bp.route('/settings/api-keys', methods=['POST'])
def update_api_keys():
    """
    Update API keys in the .env file and trigger Flask reload.

    Educational Note: This endpoint demonstrates safe key update pattern:
    1. Skip masked values (haven't changed)
    2. Save new values to .env file
    3. Reload environment variables
    4. Verify keys were saved correctly

    The skip-masked pattern is important: when frontend loads keys,
    it gets masked values. If user doesn't change a key, it stays masked.
    We detect this and don't overwrite with the mask.

    Request Body:
        {
            "api_keys": [
                {"id": "ANTHROPIC_API_KEY", "value": "sk-ant-..."},
                {"id": "OPENAI_API_KEY", "value": "***masked***"}  # skipped
            ]
        }

    Returns:
        { "success": true, "message": "API keys updated successfully" }
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

            # Skip if value is masked (starts with asterisks)
            if value and not value.startswith('***'):
                env_service.set_key(key_id, value)
                updated_count += 1
                current_app.logger.info(f"Updated API key: {key_id}")

        # Save and reload
        env_service.save()
        env_service.reload_env()

        # Verify keys were saved
        for key_data in api_keys:
            key_id = key_data.get('id')
            value = key_data.get('value', '')
            if value and not value.startswith('***'):
                saved_value = env_service.get_key(key_id)
                if not saved_value:
                    current_app.logger.error(f"Failed to verify {key_id} in environment!")

        current_app.logger.info(f"Updated {updated_count} API keys")

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


@settings_bp.route('/settings/api-keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """
    Delete a specific API key from the .env file.

    Educational Note: This removes the key entirely from the .env file,
    not just clearing its value. For some keys, we also clean up
    related configuration (e.g., Pinecone index name and region).

    URL Parameters:
        key_id: The environment variable name (e.g., "ANTHROPIC_API_KEY")

    Returns:
        { "success": true, "message": "API key ... deleted successfully" }
    """
    try:
        # Delete the main key
        env_service.delete_key(key_id)

        # If deleting Pinecone API key, also delete related config
        if key_id == 'PINECONE_API_KEY':
            current_app.logger.info("Deleting related Pinecone configuration...")
            env_service.delete_key('PINECONE_INDEX_NAME')
            env_service.delete_key('PINECONE_REGION')

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


@settings_bp.route('/settings/api-keys/validate', methods=['POST'])
def validate_api_key():
    """
    Validate an API key by making a test request to the service.

    Educational Note: Validation tests if a key actually works by making
    a minimal API call to each service. This prevents users from saving
    invalid keys and only discovering the problem later.

    Each service has custom validation:
    - Anthropic: Makes a minimal completion request
    - OpenAI: Tests the embeddings endpoint
    - Pinecone: Checks/creates the index (auto-configures settings)
    - ElevenLabs: Tests token generation
    - Tavily: Makes a test search

    For Pinecone specifically, successful validation automatically:
    1. Creates the "growthxlearn" index if it doesn't exist
    2. Saves index name and region to .env

    Request Body:
        { "key_id": "ANTHROPIC_API_KEY", "value": "sk-ant-..." }

    Returns:
        {
            "success": true,
            "valid": true,
            "message": "API key is valid"
        }
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

        # Skip validation for masked values (already validated)
        if value.startswith('***'):
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Key already set'
            }), 200

        # Validate based on key type
        is_valid, message = _validate_key(key_id, value)

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


def _validate_key(key_id: str, value: str) -> tuple[bool, str]:
    """
    Validate a specific API key using the appropriate validator.

    Educational Note: Each API service has different validation requirements.
    This function routes to the correct validator and handles special cases
    like Pinecone's auto-configuration.
    """
    if key_id == 'ANTHROPIC_API_KEY':
        return validation_service.validate_anthropic_key(value)

    elif key_id == 'ELEVENLABS_API_KEY':
        return validation_service.validate_elevenlabs_key(value)

    elif key_id == 'OPENAI_API_KEY':
        return validation_service.validate_openai_key(value)

    elif key_id == 'GEMINI_2_5_API_KEY':
        return validation_service.validate_gemini_2_5_key(value)

    elif key_id == 'NANO_BANANA_API_KEY':
        return validation_service.validate_nano_banana_key(value)

    elif key_id == 'VEO_API_KEY':
        return validation_service.validate_veo_key(value)

    elif key_id == 'TAVILY_API_KEY':
        return validation_service.validate_tavily_key(value)

    elif key_id == 'PINECONE_API_KEY':
        # Pinecone validation also creates/checks index
        is_valid, message, index_details = validation_service.validate_pinecone_key(value)

        # Auto-save index details on successful validation
        if is_valid and index_details:
            try:
                current_app.logger.info(f"Saving Pinecone index details: {index_details}")
                env_service.set_key('PINECONE_INDEX_NAME', index_details['index_name'])
                env_service.set_key('PINECONE_REGION', index_details['region'])
                env_service.save()
            except Exception as e:
                current_app.logger.error(f"Failed to save Pinecone index details: {e}")

        return is_valid, message

    elif key_id in ['PINECONE_INDEX_NAME', 'PINECONE_REGION']:
        # Auto-managed fields - just accept them
        is_valid = bool(value)
        message = 'Configuration accepted (auto-managed)'
        return is_valid, message

    else:
        # Default validation - just check if value exists
        is_valid = bool(value)
        message = 'Key provided' if is_valid else 'Key is empty'
        return is_valid, message
