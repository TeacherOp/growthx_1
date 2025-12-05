"""
Business Report Agent Executor - Handles studio signal execution for business reports.

Educational Note: This executor is triggered by studio signals (from main chat)
and launches the business_report_agent as a background task. The agent orchestrates
data analysis (via csv_analyzer_agent) and report writing.

The key difference from other executors is that business reports can analyze
multiple CSV sources and incorporate context from non-CSV sources.
"""

from typing import Dict, Any, List
import uuid
from datetime import datetime


class BusinessReportAgentExecutor:
    """
    Executor for business report generation via studio signals.

    Educational Note: The studio signal flow:
    1. User chats with AI about sources (including CSV data)
    2. AI decides to generate a business report (sends studio_signal tool call)
    3. studio_signal_executor routes to this executor
    4. We create a job and launch business_report_agent as background task
    5. Agent runs independently, calls csv_analyzer_agent for data, updates job status
    """

    def execute(
        self,
        project_id: str,
        source_id: str,
        direction: str = "",
        report_type: str = "executive_summary",
        csv_source_ids: List[str] = None,
        context_source_ids: List[str] = None,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute business report generation as a background task.

        Args:
            project_id: The project ID
            source_id: Primary source that triggered the signal
            direction: User's direction/guidance (optional)
            report_type: Type of report (default: executive_summary)
            csv_source_ids: List of CSV source IDs to analyze (optional)
            context_source_ids: List of non-CSV source IDs for context (optional)
            focus_areas: List of focus areas/topics (optional)

        Returns:
            Job info with status and job_id for polling
        """
        from app.services.studio_services import studio_index_service
        from app.services.background_services import task_service
        from app.services.ai_agents import business_report_agent_service
        from app.services.source_services import source_service

        csv_source_ids = csv_source_ids or []
        context_source_ids = context_source_ids or []
        focus_areas = focus_areas or []

        # Get source info
        source = source_service.get_source(project_id, source_id)
        if not source:
            return {
                "success": False,
                "error": f"Source {source_id} not found"
            }

        source_name = source.get("name", "Unknown Source")

        # Create job
        job_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        studio_index_service.create_business_report_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction,
            report_type=report_type,
            csv_source_ids=csv_source_ids,
            context_source_ids=context_source_ids,
            focus_areas=focus_areas
        )

        # Launch agent as background task
        def run_agent():
            """Background task to run the business report agent."""
            print(f"[BusinessReportAgentExecutor] Starting agent for job {job_id[:8]}")
            try:
                business_report_agent_service.generate_business_report(
                    project_id=project_id,
                    source_id=source_id,
                    job_id=job_id,
                    direction=direction,
                    report_type=report_type,
                    csv_source_ids=csv_source_ids,
                    context_source_ids=context_source_ids,
                    focus_areas=focus_areas
                )
            except Exception as e:
                print(f"[BusinessReportAgentExecutor] Error in business report agent: {e}")
                import traceback
                traceback.print_exc()
                # Update job on error
                studio_index_service.update_business_report_job(
                    project_id, job_id,
                    status="error",
                    error_message=str(e)
                )

        task_service.submit_task(
            task_type="business_report_generation",
            target_id=job_id,
            callable_func=run_agent
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "message": f"Business report generation started (type: {report_type})"
        }


# Singleton instance
business_report_agent_executor = BusinessReportAgentExecutor()
