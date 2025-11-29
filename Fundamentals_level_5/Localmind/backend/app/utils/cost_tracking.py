"""
Cost Tracking Utility - Track and calculate API costs per project.

Educational Note: This utility tracks Claude API usage costs by model.
Costs are stored cumulatively in project.json and updated after each API call.

Pricing (per 1M tokens):
- Sonnet: $3 input, $15 output
- Haiku: $1 input, $5 output
"""
import json
from typing import Dict, Any, Optional
from threading import Lock

from config import Config


# Pricing per 1M tokens
PRICING = {
    "sonnet": {"input": 3.0, "output": 15.0},
    "haiku": {"input": 1.0, "output": 5.0},
}

# Lock for thread-safe file operations
_lock = Lock()


def _get_model_key(model_string: str) -> str:
    """
    Extract model key (sonnet/haiku) from full model string.

    Args:
        model_string: Full model ID like "claude-sonnet-4-5-20250929"

    Returns:
        "sonnet" or "haiku"
    """
    model_lower = model_string.lower()
    if "sonnet" in model_lower:
        return "sonnet"
    elif "haiku" in model_lower:
        return "haiku"
    else:
        # Default to sonnet pricing for unknown models
        return "sonnet"


def _calculate_cost(model_key: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for a single API call.

    Args:
        model_key: "sonnet" or "haiku"
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    pricing = PRICING.get(model_key, PRICING["sonnet"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def _load_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Load project data from JSON file."""
    project_file = Config.PROJECTS_DIR / f"{project_id}.json"
    if not project_file.exists():
        return None

    try:
        with open(project_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_project(project_id: str, project_data: Dict[str, Any]) -> bool:
    """Save project data to JSON file."""
    project_file = Config.PROJECTS_DIR / f"{project_id}.json"

    try:
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
        return True
    except IOError:
        return False


def _ensure_cost_tracking_structure(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure project data has cost_tracking structure.

    Educational Note: Initializes the cost tracking structure if it
    doesn't exist, preserving any existing data.
    """
    if "cost_tracking" not in project_data:
        project_data["cost_tracking"] = {
            "total_cost": 0.0,
            "by_model": {
                "sonnet": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                },
                "haiku": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                }
            }
        }
    return project_data


def add_usage(
    project_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> Optional[Dict[str, Any]]:
    """
    Add API usage to project cost tracking.

    Educational Note: This function is called after each Claude API call
    to update the cumulative cost tracking in the project file.

    Args:
        project_id: The project UUID
        model: Full model string (e.g., "claude-sonnet-4-5-20250929")
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used

    Returns:
        Updated cost tracking data or None if failed
    """
    with _lock:
        project_data = _load_project(project_id)
        if project_data is None:
            print(f"Cost tracking: Project {project_id} not found")
            return None

        # Ensure structure exists
        project_data = _ensure_cost_tracking_structure(project_data)

        # Get model key and calculate cost
        model_key = _get_model_key(model)
        call_cost = _calculate_cost(model_key, input_tokens, output_tokens)

        # Update model-specific tracking
        model_tracking = project_data["cost_tracking"]["by_model"][model_key]
        model_tracking["input_tokens"] += input_tokens
        model_tracking["output_tokens"] += output_tokens
        model_tracking["cost"] += call_cost

        # Update total cost
        project_data["cost_tracking"]["total_cost"] += call_cost

        # Save updated project
        if _save_project(project_id, project_data):
            return project_data["cost_tracking"]
        else:
            print(f"Cost tracking: Failed to save project {project_id}")
            return None


def get_project_costs(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cost tracking data for a project.

    Args:
        project_id: The project UUID

    Returns:
        Cost tracking data or None if not found
    """
    project_data = _load_project(project_id)
    if project_data is None:
        return None

    # Ensure structure exists (for projects created before cost tracking)
    project_data = _ensure_cost_tracking_structure(project_data)

    return project_data.get("cost_tracking")
