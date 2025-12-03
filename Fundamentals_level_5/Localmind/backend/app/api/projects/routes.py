"""
Project CRUD endpoints.

Educational Note: These endpoints demonstrate RESTful API design principles:

HTTP Methods and Their Meanings:
- GET: Retrieve data (safe, idempotent, cacheable)
- POST: Create new resource (not idempotent)
- PUT: Update/replace resource (idempotent)
- DELETE: Remove resource (idempotent)

Idempotent = calling multiple times has same effect as calling once.

Status Codes Used:
- 200: OK (successful GET, PUT, DELETE)
- 201: Created (successful POST)
- 400: Bad Request (validation failed)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error (unexpected failure)

Routes:
- GET    /projects           - List all projects
- POST   /projects           - Create new project
- GET    /projects/<id>      - Get project details
- PUT    /projects/<id>      - Update project
- DELETE /projects/<id>      - Delete project
- POST   /projects/<id>/open - Mark project as opened
"""
from flask import request, jsonify
from app.api.projects import projects_bp
from app.services.data_services import project_service


@projects_bp.route('/projects', methods=['GET'])
def list_projects():
    """
    List all available projects.

    Educational Note: GET requests should never modify data, only retrieve it.
    This is a "safe" HTTP method.

    Returns:
        {
            "success": true,
            "projects": [...],
            "count": 5
        }
    """
    try:
        projects = project_service.list_all_projects()
        return jsonify({
            "success": True,
            "projects": projects,
            "count": len(projects)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@projects_bp.route('/projects', methods=['POST'])
def create_project():
    """
    Create a new project.

    Educational Note: POST creates new resources.
    Always validate input data before processing!

    Request Body:
        {
            "name": "My Project",        # required
            "description": "Optional"    # optional
        }

    Returns:
        {
            "success": true,
            "project": { ... },
            "message": "Project 'My Project' created successfully"
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "error": "Project name is required"
            }), 400

        # Validate name is not empty
        name = data['name'].strip()
        if not name:
            return jsonify({
                "success": False,
                "error": "Project name cannot be empty"
            }), 400

        # Create the project
        project = project_service.create_project(
            name=name,
            description=data.get('description', '')
        )

        return jsonify({
            "success": True,
            "project": project,
            "message": f"Project '{name}' created successfully"
        }), 201  # 201 = Created

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to create project: {str(e)}"
        }), 500


@projects_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get details of a specific project.

    Educational Note: Use URL parameters for resource identifiers.
    This follows RESTful design: /resource/{id}

    URL Parameters:
        project_id: The project UUID

    Returns:
        {
            "success": true,
            "project": { id, name, description, created_at, ... }
        }
    """
    try:
        project = project_service.get_project(project_id)

        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        return jsonify({
            "success": True,
            "project": project
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@projects_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Update a project (rename, update description, etc.).

    Educational Note: PUT is traditionally for full replacement,
    PATCH for partial updates. We use PUT but only update provided
    fields for flexibility (a common pragmatic choice).

    URL Parameters:
        project_id: The project UUID

    Request Body:
        {
            "name": "New Name",           # optional
            "description": "New desc"     # optional
        }

    Returns:
        {
            "success": true,
            "project": { ... updated ... },
            "message": "Project updated successfully"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No update data provided"
            }), 400

        # Update the project
        updated_project = project_service.update_project(
            project_id=project_id,
            name=data.get('name'),
            description=data.get('description')
        )

        if not updated_project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        return jsonify({
            "success": True,
            "project": updated_project,
            "message": "Project updated successfully"
        }), 200

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to update project: {str(e)}"
        }), 500


@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete a project and all its data.

    Educational Note: DELETE operations should be idempotent -
    calling DELETE multiple times should have the same effect
    as calling it once. Deleting a non-existent resource returns 404.

    WARNING: This deletes all project data including:
    - All sources (files, embeddings in Pinecone)
    - All chats and messages
    - Project memory

    URL Parameters:
        project_id: The project UUID

    Returns:
        {
            "success": true,
            "message": "Project {id} deleted successfully"
        }
    """
    try:
        success = project_service.delete_project(project_id)

        if not success:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        return jsonify({
            "success": True,
            "message": f"Project {project_id} deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete project: {str(e)}"
        }), 500


@projects_bp.route('/projects/<project_id>/open', methods=['POST'])
def open_project(project_id):
    """
    Mark a project as opened (update last accessed time).

    Educational Note: This is an "action" endpoint - sometimes REST
    needs endpoints that don't fit pure CRUD. Using POST for actions
    is a common pattern. The verb is in the URL (/open) which some
    consider non-RESTful, but it's pragmatic and clear.

    Alternative designs:
    - PATCH /projects/{id} with { "last_accessed": "now" }
    - POST /projects/{id}/events with { "type": "open" }

    URL Parameters:
        project_id: The project UUID

    Returns:
        {
            "success": true,
            "project": { ... with updated last_accessed ... },
            "message": "Project opened successfully"
        }
    """
    try:
        project = project_service.open_project(project_id)

        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        return jsonify({
            "success": True,
            "project": project,
            "message": "Project opened successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to open project: {str(e)}"
        }), 500
