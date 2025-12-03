"""
Project memory endpoint.

Educational Note: Memory is a key concept in LLM applications that
allows the AI to maintain context across conversations.

Memory Types in NoobBook:

1. User Memory (data/user_memory.json)
   - Global preferences that apply to ALL projects
   - Example: "User prefers concise responses"
   - Persists across all conversations, all projects

2. Project Memory (data/projects/{id}/memory.json)
   - Context specific to THIS project
   - Example: "This project is about a React e-commerce app"
   - Deleted when project is deleted

How Memory Works:
1. During chat, Claude can call the `store_memory` tool
2. New memory is merged with existing using Haiku (AI-powered)
3. Merging keeps total under 150 tokens (fits in context)
4. Memory is injected into system prompt via context_loader

Why Two Levels?
- User memory = "who the user is" (preferences, background)
- Project memory = "what we're working on" (project context)
- This separation helps the AI provide more relevant responses

Routes:
- GET /projects/<id>/memory - Get both memory types for project
"""
from flask import jsonify
from app.api.projects import projects_bp
from app.services.data_services import project_service
from app.services.ai_services.memory_service import memory_service


@projects_bp.route('/projects/<project_id>/memory', methods=['GET'])
def get_project_memory(project_id):
    """
    Get memory data for a project (user memory + project memory).

    Educational Note: This endpoint returns both memory types so the UI
    can display what context the AI "remembers". This transparency helps
    users understand why the AI responds the way it does.

    Memory is included in every chat system prompt, so showing it helps
    users debug unexpected AI behavior ("Oh, it thinks I prefer Python
    because I mentioned that last week").

    URL Parameters:
        project_id: The project UUID

    Returns:
        {
            "success": true,
            "memory": {
                "user_memory": "User is a frontend developer...",
                "project_memory": "Working on an e-commerce site..."
            }
        }

    Note: Either memory field may be null if not yet stored.
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        # Get memory data
        user_memory = memory_service.get_user_memory()
        project_memory = memory_service.get_project_memory(project_id)

        return jsonify({
            "success": True,
            "memory": {
                "user_memory": user_memory,
                "project_memory": project_memory
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get memory: {str(e)}"
        }), 500
