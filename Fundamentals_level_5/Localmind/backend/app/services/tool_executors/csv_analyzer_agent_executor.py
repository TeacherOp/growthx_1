"""
CSV Analyzer Agent Executor - Executes analyze_csv_agent tool calls from main chat.

Educational Note: This executor bridges main_chat and csv_analyzer_agent.
When main chat calls analyze_csv_agent tool, this executor:
1. Receives source_id and query from tool input
2. Calls csv_analyzer_agent.run() with the parameters
3. Formats and returns the result for main chat
"""

from typing import Dict, Any

from app.services.ai_agents.csv_analyzer_agent import csv_analyzer_agent


def execute(
    project_id: str,
    source_id: str,
    query: str
) -> Dict[str, Any]:
    """
    Execute CSV analyzer agent for a user query.

    Educational Note: This function is called by main_chat_service
    when Claude uses the analyze_csv_agent tool.

    Args:
        project_id: Project ID for file paths and cost tracking
        source_id: Source ID of the CSV file to analyze
        query: User's question about the CSV data

    Returns:
        Dict with analysis result or error
    """
    if not source_id:
        return {
            "success": False,
            "error": "source_id is required"
        }

    if not query:
        return {
            "success": False,
            "error": "query is required"
        }

    result = csv_analyzer_agent.run(
        project_id=project_id,
        source_id=source_id,
        query=query
    )

    if result.get("success"):
        response = {
            "success": True,
            "content": result.get("summary", "No analysis result"),
            "data": result.get("data"),
            "iterations": result.get("iterations", 0)
        }

        # Include image paths if any plots were generated
        if result.get("image_paths"):
            response["image_paths"] = result["image_paths"]

        return response
    else:
        return {
            "success": False,
            "error": result.get("error", "Analysis failed")
        }
