"""
Presentation Agent Executor - Handles studio signal execution for presentation generation.

Educational Note: This executor is triggered by studio signals (from main chat)
and launches the presentation agent as a background task. After the agent generates
HTML slides, it captures screenshots and exports to PPTX.
"""

from typing import Dict, Any
import uuid
from pathlib import Path


class PresentationAgentExecutor:
    """
    Executor for presentation generation via studio signals.

    Educational Note: The studio signal flow:
    1. User chats with AI about sources
    2. AI decides to activate studio (sends studio_signal tool call)
    3. studio_signal_executor routes to this executor
    4. We create a job and launch presentation_agent as background task
    5. Agent generates HTML slides
    6. We capture screenshots and export to PPTX
    7. Job status is updated throughout
    """

    def execute(
        self,
        project_id: str,
        source_id: str,
        direction: str = ""
    ) -> Dict[str, Any]:
        """
        Execute presentation generation as a background task.

        Args:
            project_id: The project ID
            source_id: Source to generate presentation from
            direction: User's direction/guidance (optional)

        Returns:
            Job info with status and job_id for polling
        """
        from app.services.studio_services import studio_index_service
        from app.services.background_services import task_service
        from app.services.ai_agents import presentation_agent_service
        from app.services.source_services import source_service
        from app.utils.path_utils import get_studio_dir
        from app.utils.screenshot_utils import capture_slides_as_screenshots
        from app.utils.presentation_export_utils import create_pptx_from_screenshots

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

        studio_index_service.create_presentation_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction
        )

        # Launch agent as background task
        def run_agent():
            """Background task to run the presentation agent and export to PPTX."""
            print(f"[PresentationAgentExecutor] Starting presentation agent for job {job_id[:8]}")
            try:
                # Phase 1: Generate HTML slides
                result = presentation_agent_service.generate_presentation(
                    project_id=project_id,
                    source_id=source_id,
                    job_id=job_id,
                    direction=direction
                )

                if not result.get("success"):
                    print(f"[PresentationAgentExecutor] Agent failed: {result.get('error_message')}")
                    return

                # Phase 2: Capture screenshots and export to PPTX
                slide_files = result.get("slide_files", [])
                if not slide_files:
                    print("[PresentationAgentExecutor] No slides to export")
                    return

                # Update status
                studio_index_service.update_presentation_job(
                    project_id, job_id,
                    status_message="Capturing screenshots...",
                    export_status="exporting"
                )

                # Get paths
                studio_dir = get_studio_dir(project_id)
                slides_dir = Path(studio_dir) / "presentations" / job_id / "slides"
                screenshots_dir = Path(studio_dir) / "presentations" / job_id / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)

                # Capture screenshots
                print(f"[PresentationAgentExecutor] Capturing {len(slide_files)} slides")
                screenshots = capture_slides_as_screenshots(
                    slides_dir=str(slides_dir),
                    output_dir=str(screenshots_dir),
                    slide_files=slide_files
                )

                if not screenshots:
                    print("[PresentationAgentExecutor] Screenshot capture failed")
                    studio_index_service.update_presentation_job(
                        project_id, job_id,
                        export_status="error",
                        status_message="Screenshot capture failed"
                    )
                    return

                # Update with screenshots info
                studio_index_service.update_presentation_job(
                    project_id, job_id,
                    screenshots=screenshots,
                    status_message="Creating PPTX..."
                )

                # Create PPTX
                job = studio_index_service.get_presentation_job(project_id, job_id)
                title = job.get("presentation_title", "Presentation") if job else "Presentation"

                # Sanitize filename
                safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
                if not safe_title:
                    safe_title = "Presentation"
                pptx_filename = f"{safe_title}.pptx"

                pptx_output_dir = Path(studio_dir) / "presentations" / job_id
                pptx_path = pptx_output_dir / pptx_filename

                print(f"[PresentationAgentExecutor] Creating PPTX: {pptx_filename}")
                pptx_result = create_pptx_from_screenshots(
                    screenshots=screenshots,
                    output_path=str(pptx_path),
                    title=title
                )

                if pptx_result:
                    # Success!
                    studio_index_service.update_presentation_job(
                        project_id, job_id,
                        pptx_file=str(pptx_path),
                        pptx_filename=pptx_filename,
                        export_status="ready",
                        status_message="Presentation ready for download!",
                        download_url=f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/download"
                    )
                    print(f"[PresentationAgentExecutor] PPTX created: {pptx_filename}")
                else:
                    studio_index_service.update_presentation_job(
                        project_id, job_id,
                        export_status="error",
                        status_message="PPTX export failed"
                    )
                    print("[PresentationAgentExecutor] PPTX export failed")

            except Exception as e:
                print(f"[PresentationAgentExecutor] Error in presentation agent: {e}")
                import traceback
                traceback.print_exc()
                # Update job on error
                studio_index_service.update_presentation_job(
                    project_id, job_id,
                    status="error",
                    error_message=str(e)
                )

        task_service.submit_task(
            task_type="presentation_generation",
            target_id=job_id,
            callable_func=run_agent
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "message": f"Presentation generation started for '{source_name}'"
        }


# Singleton instance
presentation_agent_executor = PresentationAgentExecutor()
