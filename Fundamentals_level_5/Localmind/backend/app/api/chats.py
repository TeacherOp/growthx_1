"""
API endpoints for chat management and conversations.

Educational Note: These endpoints handle chat operations including
creating chats, sending messages, and managing conversations within projects.

Routes are thin - all logic is delegated to services:
- chat_service: Chat CRUD operations
- main_chat_service: Message processing and AI responses
- prompt_loader: Prompt management
"""
from flask import jsonify, request, current_app
from app.api import api_bp
from app.services.data_services import chat_service
from app.services.chat_services import main_chat_service
from app.config import prompt_loader


# =============================================================================
# Chat CRUD Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/chats', methods=['GET'])
def list_project_chats(project_id):
    """
    Get all chats for a specific project.

    Educational Note: Returns chat metadata only (not full messages)
    for efficient loading of the chat list in the UI.
    """
    try:
        chats = chat_service.list_chats(project_id)
        return jsonify({
            'success': True,
            'chats': chats,
            'count': len(chats)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing chats for project {project_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/chats', methods=['POST'])
def create_chat(project_id):
    """
    Create a new chat in a project.

    Educational Note: Initializes an empty conversation.
    Messages are added via the send_message endpoint.
    """
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Chat')

        chat = chat_service.create_chat(project_id, title)

        return jsonify({
            'success': True,
            'chat': chat
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error creating chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/chats/<chat_id>', methods=['GET'])
def get_chat(project_id, chat_id):
    """
    Get full chat data including all messages.

    Educational Note: Loads the complete conversation history
    for display in the chat interface.
    """
    try:
        chat = chat_service.get_chat(project_id, chat_id)

        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat not found'
            }), 404

        return jsonify({
            'success': True,
            'chat': chat
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting chat {chat_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/chats/<chat_id>', methods=['PUT'])
def update_chat(project_id, chat_id):
    """
    Update chat metadata (currently only title).

    Educational Note: Allows users to rename chats for better organization.
    """
    try:
        data = request.get_json()

        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400

        chat = chat_service.update_chat(project_id, chat_id, {"title": data['title']})

        if not chat:
            return jsonify({
                'success': False,
                'error': 'Chat not found'
            }), 404

        return jsonify({
            'success': True,
            'chat': chat
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating chat {chat_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/projects/<project_id>/chats/<chat_id>', methods=['DELETE'])
def delete_chat(project_id, chat_id):
    """
    Delete a chat and all its messages.

    Educational Note: This is a hard delete. In production,
    consider soft delete with archive functionality.
    """
    try:
        success = chat_service.delete_chat(project_id, chat_id)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Chat not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Chat deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting chat {chat_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# Message Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/chats/<chat_id>/messages', methods=['POST'])
def send_message(project_id, chat_id):
    """
    Send a message in a chat and get AI response.

    Educational Note: This endpoint is kept thin - all logic is delegated
    to main_chat_service. The service handles:
    1. Storing user message
    2. Building context with system prompt
    3. Calling Claude API
    4. Storing assistant response
    5. Syncing chat index
    """
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        user_message_text = data['message']

        # Delegate all processing to main_chat_service
        user_msg, assistant_msg = main_chat_service.send_message(
            project_id=project_id,
            chat_id=chat_id,
            user_message_text=user_message_text
        )

        return jsonify({
            'success': True,
            'user_message': user_msg,
            'assistant_message': assistant_msg
        }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error sending message: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# Prompt Endpoints
# =============================================================================

@api_bp.route('/projects/<project_id>/prompt', methods=['GET'])
def get_project_prompt(project_id):
    """
    Get the system prompt for a project (custom or default).

    Educational Note: Returns the prompt that will be used
    for all AI conversations in this project.
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


@api_bp.route('/projects/<project_id>/prompt', methods=['PUT'])
def update_project_prompt(project_id):
    """
    Update the project's custom system prompt.

    Educational Note: Setting prompt to null/empty reverts to default.
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


@api_bp.route('/prompts/default', methods=['GET'])
def get_default_prompt():
    """
    Get the global default prompt.

    Educational Note: This is the fallback prompt used when
    projects don't have custom prompts.
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
