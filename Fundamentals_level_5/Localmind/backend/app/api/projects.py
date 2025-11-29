"""
Project management API endpoints.

Educational Note: This module handles all project-related operations:
create, list, open, rename, and delete projects.
We use RESTful conventions for clear, predictable API design.
"""
from flask import request, jsonify
from datetime import datetime
import json
import uuid
from pathlib import Path

from app.api import api_bp
from app.services.data_services import project_service
from app.utils.cost_tracking import get_project_costs
from app.services.ai_services import memory_service


@api_bp.route('/projects', methods=['GET'])
def list_projects():
    """
    List all available projects.

    Returns:
        JSON array of project objects with id, name, created_at, updated_at

    Educational Note: GET requests should never modify data, only retrieve it.
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


@api_bp.route('/projects', methods=['POST'])
def create_project():
    """
    Create a new project.

    Request Body:
        - name: string (required) - The project name
        - description: string (optional) - Project description

    Returns:
        JSON object with project details including generated ID

    Educational Note: POST creates new resources. Always validate input data!
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


@api_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get details of a specific project.

    URL Parameters:
        - project_id: string - The project UUID

    Returns:
        JSON object with full project details

    Educational Note: Use URL parameters for resource identifiers.
    This follows RESTful design: /resource/id
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


@api_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Update a project (rename, update description, etc.).

    URL Parameters:
        - project_id: string - The project UUID

    Request Body:
        - name: string (optional) - New project name
        - description: string (optional) - New description

    Returns:
        JSON object with updated project details

    Educational Note: PUT is for full updates, PATCH for partial updates.
    We use PUT here but only update provided fields for flexibility.
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


@api_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete a project.

    URL Parameters:
        - project_id: string - The project UUID

    Returns:
        Success message or error

    Educational Note: DELETE operations should be idempotent -
    calling DELETE multiple times should have the same effect as calling it once.
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


@api_bp.route('/projects/<project_id>/open', methods=['POST'])
def open_project(project_id):
    """
    Mark a project as opened (update last accessed time).

    URL Parameters:
        - project_id: string - The project UUID

    Returns:
        Project details with updated access time

    Educational Note: This endpoint demonstrates an "action" endpoint.
    Sometimes REST needs action-specific endpoints beyond CRUD.
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


@api_bp.route('/projects/<project_id>/costs', methods=['GET'])
def get_project_costs(project_id):
    """
    Get cost tracking data for a project.

    URL Parameters:
        - project_id: string - The project UUID

    Returns:
        JSON object with cost tracking data:
        - total_cost: float - Total cost in USD
        - by_model: dict - Breakdown by model (sonnet/haiku)
            - input_tokens: int
            - output_tokens: int
            - cost: float

    Educational Note: Cost tracking helps monitor API usage and
    provides transparency about resource consumption per project.
    """
    try:
        # Verify project exists
        project = project_service.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found"
            }), 404

        # Get cost tracking data
        costs = get_project_costs(project_id)

        return jsonify({
            "success": True,
            "costs": costs
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get project costs: {str(e)}"
        }), 500


@api_bp.route('/projects/<project_id>/memory', methods=['GET'])
def get_project_memory(project_id):
    """
    Get memory data for a project (user memory + project memory).

    URL Parameters:
        - project_id: string - The project UUID

    Returns:
        JSON object with memory data:
        - user_memory: string | null - Global user memory
        - project_memory: string | null - Project-specific memory

    Educational Note: Memory helps the AI maintain context across conversations.
    User memory persists across all projects, project memory is specific to this project.
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