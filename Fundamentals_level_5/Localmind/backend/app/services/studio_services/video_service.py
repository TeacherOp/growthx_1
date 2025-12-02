"""
Video Generation Service - Simple video generation using Google Veo 2.0.

Educational Note: This is a simple service (not an agent) that:
1. Uses Claude to generate an optimized video prompt from source content
2. Calls Google Veo API with the generated prompt
3. Saves videos and updates job status
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.services.integrations.google.video_service import google_video_service
from app.services.ai_services.video_prompt_service import video_prompt_service
from app.services.studio_services import studio_index_service
from app.utils.path_utils import get_studio_dir


class VideoService:
    """
    Simple video generation service.

    Educational Note: Takes prompt + parameters, calls Google Veo API,
    saves videos, and updates job status. No agent loop needed.
    """

    def generate_video(
        self,
        project_id: str,
        job_id: str,
        source_id: str,
        direction: str = "",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        number_of_videos: int = 1
    ) -> Dict[str, Any]:
        """
        Generate video(s) from source content.

        Args:
            project_id: Project ID
            job_id: Video job ID
            source_id: Source to generate from
            direction: User's direction/guidance
            aspect_ratio: "16:9" or "16:10"
            duration_seconds: 5-8 seconds
            number_of_videos: 1-4 videos

        Returns:
            Result dict with success status and video info
        """
        print(f"[VideoService] Starting generation for job {job_id[:8]}")

        # Update job to processing
        studio_index_service.update_video_job(
            project_id, job_id,
            status="processing",
            status_message="Generating video prompt with Claude..."
        )

        # Step 1: Generate optimized video prompt using Claude
        prompt_result = video_prompt_service.generate_video_prompt(
            project_id=project_id,
            source_id=source_id,
            direction=direction
        )

        if not prompt_result["success"]:
            # Failed to generate prompt
            studio_index_service.update_video_job(
                project_id, job_id,
                status="error",
                error_message=f"Failed to generate video prompt: {prompt_result.get('error', 'Unknown error')}"
            )
            return prompt_result

        video_prompt = prompt_result["prompt"]
        print(f"[VideoService] Generated prompt: {video_prompt[:100]}...")

        # Update job with generated prompt
        studio_index_service.update_video_job(
            project_id, job_id,
            status_message="Generating video with Google Veo...",
            generated_prompt=video_prompt
        )

        # Prepare output directory
        studio_dir = get_studio_dir(project_id)
        video_dir = Path(studio_dir) / "videos" / job_id
        video_dir.mkdir(parents=True, exist_ok=True)

        # Progress callback
        def on_progress(message: str):
            studio_index_service.update_video_job(
                project_id, job_id,
                status_message=message
            )

        # Step 2: Generate video(s) using Google Veo
        result = google_video_service.generate_video(
            prompt=video_prompt,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            number_of_videos=number_of_videos,
            output_dir=video_dir,
            on_progress=on_progress
        )

        if not result["success"]:
            # Update job to error
            studio_index_service.update_video_job(
                project_id, job_id,
                status="error",
                error_message=result.get("error", "Video generation failed")
            )
            return result

        # Success - update job
        videos = result["videos"]
        print(f"[VideoService] Generated {len(videos)} video(s)")

        # Build video info for job
        video_info = []
        for video in videos:
            video_info.append({
                "filename": video["filename"],
                "path": video["path"],
                "uri": video["uri"],
                "preview_url": f"/api/v1/projects/{project_id}/studio/videos/{job_id}/preview/{video['filename']}",
                "download_url": f"/api/v1/projects/{project_id}/studio/videos/{job_id}/download/{video['filename']}"
            })

        studio_index_service.update_video_job(
            project_id, job_id,
            status="ready",
            status_message="Video generation complete!",
            videos=video_info,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            completed_at=datetime.now().isoformat()
        )

        return {
            "success": True,
            "job_id": job_id,
            "videos": video_info,
            "count": len(video_info)
        }


# Singleton instance
video_service = VideoService()
