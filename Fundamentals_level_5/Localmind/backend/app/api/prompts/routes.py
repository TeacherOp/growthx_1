"""
Prompt management endpoints.

Educational Note: System prompts are crucial for shaping AI behavior.
These endpoints let users customize how Claude responds in their projects.

The prompt hierarchy:
1. Project custom prompt (if set) -> Used for all chats in project
2. Default prompt (fallback) -> data/prompts/default_prompt.json

Routes:
- GET  /projects/<id>/prompt  - Get project's effective prompt
- PUT  /projects/<id>/prompt  - Set/clear project's custom prompt
- GET  /prompts/default       - Get global default prompt
"""
from flask import jsonify, request, current_app
from app.api.prompts import prompts_bp
from app.config import prompt_loader


@prompts_bp.route('/projects/<project_id>/prompt', methods=['GET'])
def get_project_prompt(project_id):
    """
    Get the system prompt for a project (custom or default).

    Educational Note: Returns the prompt that will be used
    for all AI conversations in this project.

    Response:
        {
            "success": true,
            "prompt": "You are a helpful assistant..."
        }
    """
    try:
        prompt = prompt_loader.get_project_prompt(project_id)

        return jsonify({
            'success': True,
            'prompt': prompt
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting prompt for project {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prompts_bp.route('/projects/<project_id>/prompt', methods=['PUT'])
def update_project_prompt(project_id):
    """
    Update the project's custom system prompt.

    Educational Note: Setting prompt to null/empty reverts to default.
    This allows users to customize AI behavior per-project while
    maintaining a sensible fallback.

    Request Body:
        { "prompt": "Custom instructions..." }  - Set custom prompt
        { "prompt": null }                      - Revert to default
        { "prompt": "" }                        - Revert to default

    Response:
        {
            "success": true,
            "prompt": "...",      # Current effective prompt
            "is_custom": true     # Whether using custom or default
        }
    """
    try:
        data = request.get_json()

        if data is None:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Get the custom prompt (can be null to reset to default)
        custom_prompt = data.get('prompt')

        # Treat empty string as None (use default)
        if custom_prompt == '':
            custom_prompt = None

        # Update via prompt service
        success = prompt_loader.update_project_prompt(project_id, custom_prompt)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404

        # Return the current prompt
        current_prompt = prompt_loader.get_project_prompt(project_id)

        return jsonify({
            'success': True,
            'prompt': current_prompt,
            'is_custom': custom_prompt is not None
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating prompt for project {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prompts_bp.route('/prompts/default', methods=['GET'])
def get_default_prompt():
    """
    Get the global default prompt.

    Educational Note: This is the fallback prompt used when
    projects don't have custom prompts. It's stored in
    data/prompts/default_prompt.json.

    Response:
        {
            "success": true,
            "prompt": "You are a helpful AI assistant..."
        }
    """
    try:
        prompt = prompt_loader.get_default_prompt()

        return jsonify({
            'success': True,
            'prompt': prompt
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting default prompt: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prompts_bp.route('/prompts/all', methods=['GET'])
def list_all_prompts():
    """
    List all prompt configurations.

    Educational Note: This dynamically reads all prompt files from
    data/prompts/ directory. Adding new prompt files automatically
    makes them visible in the UI.

    Response:
        {
            "success": true,
            "prompts": [
                {
                    "name": "default_chat_prompt",
                    "description": "Default system prompt...",
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 16000,
                    "temperature": 0.5,
                    "system_prompt": "...",
                    "user_message": "..." (optional),
                    "filename": "default_prompt.json"
                },
                ...
            ]
        }
    """
    try:
        prompts = prompt_loader.list_all_prompts()

        return jsonify({
            'success': True,
            'prompts': prompts,
            'count': len(prompts)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing prompts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
