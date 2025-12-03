"""
Project cost tracking endpoint.

Educational Note: Cost tracking is essential for LLM applications because:

1. API calls cost real money - Claude, OpenAI, etc. charge per token
2. Different models have different costs:
   - Sonnet: $3/1M input, $15/1M output tokens
   - Haiku: $1/1M input, $5/1M output tokens
3. Projects can vary wildly in cost based on:
   - Number of sources (affects system prompt size)
   - Chat frequency
   - Source processing (PDF extraction uses many tokens)

Cost Tracking Architecture:
- Each claude_service.send_message() call records usage
- Costs stored in project.json under "costs" key
- Broken down by model for transparency

This helps users understand:
- Which projects consume the most API credits
- Whether to use cheaper models for certain tasks
- Budget planning for production deployments

Routes:
- GET /projects/<id>/costs - Get cost breakdown for project
"""
from flask import jsonify
from app.api.projects import projects_bp
from app.services.data_services import project_service
from app.utils.cost_tracking import get_project_costs


@projects_bp.route('/projects/<project_id>/costs', methods=['GET'])
def get_project_costs_endpoint(project_id):
    """
    Get cost tracking data for a project.

    Educational Note: This endpoint provides transparency about API usage.
    In production apps, this data helps with:
    - Billing users accurately
    - Setting usage quotas
    - Identifying expensive operations to optimize

    URL Parameters:
        project_id: The project UUID

    Returns:
        {
            "success": true,
            "costs": {
                "total_cost": 0.0234,
                "by_model": {
                    "sonnet": {
                        "input_tokens": 5000,
                        "output_tokens": 1500,
                        "cost": 0.0225
                    },
                    "haiku": {
                        "input_tokens": 2000,
                        "output_tokens": 500,
                        "cost": 0.0009
                    }
                }
            }
        }
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
