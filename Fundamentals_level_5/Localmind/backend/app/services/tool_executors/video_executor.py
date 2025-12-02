"""
Video Executor - Handles studio signal execution for video generation.

Educational Note: This executor is triggered by studio signals (from main chat)
and launches video generation as a background task.
"""
import uuid
from datetime import datetime
from typing import Dict, Any


class VideoExecutor:
    """
    Executor for video generation via studio signals.

    Educational Note: The studio signal flow:
    1. User chats with AI about creating videos
    2. AI decides to activate studio (sends studio_signal tool call)
    3. studio_signal_executor routes to this executor
    4. We create a job and launch video generation as background task
    5. Service runs and updates job status
    """

    def execute(
        self,
        project_id: str,
        source_id: str,
        direction: str = "",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        number_of_videos: int = 1
    ) -> Dict[str, Any]:
        """
        Execute video generation as a background task.

        Args:
            project_id: The project ID
            source_id: Source to generate video from (for context)
            direction: User's direction/guidance for the video
            aspect_ratio: "16:9" or "16:10" (default: "16:9")
            duration_seconds: 5-8 seconds (default: 8)
            number_of_videos: 1-4 videos (default: 1)

        Returns:
            Job info with status and job_id for polling
        """
        from app.services.studio_services import studio_index_service
        from app.services.background_services import task_service
        from app.services.studio_services.video_service import video_service
        from app.services.source_services import source_service

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

        studio_index_service.create_video_job(
            project_id=project_id,
            job_id=job_id,
            source_id=source_id,
            source_name=source_name,
            direction=direction,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            number_of_videos=number_of_videos
        )

        # Launch video generation as background task
        def run_video_generation():
            """Background task to generate video."""
            print(f"[VideoExecutor] Starting video generation for job {job_id[:8]}")
            try:
                video_service.generate_video(
                    project_id=project_id,
                    job_id=job_id,
                    source_id=source_id,
                    direction=direction,
                    aspect_ratio=aspect_ratio,
                    duration_seconds=duration_seconds,
                    number_of_videos=number_of_videos
                )
            except Exception as e:
                print(f"[VideoExecutor] Error in video generation: {e}")
                import traceback
                traceback.print_exc()
                # Update job on error
                studio_index_service.update_video_job(
                    project_id, job_id,
                    status="error",
                    error_message=str(e)
                )

        task_service.submit_task(
            task_type="video_generation",
            target_id=job_id,
            callable_func=run_video_generation
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "message": f"Video generation started for '{source_name}'"
        }


# Singleton instance
video_executor = VideoExecutor()
