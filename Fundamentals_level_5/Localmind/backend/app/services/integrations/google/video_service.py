"""
Google Video Service - Integration with Google Veo 2.0 for video generation.

Educational Note: This is a thin wrapper around Google's Veo API.
The service handles video generation requests and file downloads.
"""
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path


class GoogleVideoService:
    """
    Google Veo 2.0 video generation integration.

    Educational Note: Veo 2.0 generates high-quality videos from text prompts.
    Supports aspect ratios (16:9, 16:10), durations (5-8 seconds), and batch generation (1-4 videos).
    """

    MODEL = "veo-2.0-generate-001"

    def __init__(self):
        """Initialize with API key from environment."""
        self.api_key = os.getenv("VEO_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy load the Google GenAI client."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(
                    http_options={"api_version": "v1beta"},
                    api_key=self.api_key,
                )
            except ImportError:
                raise ImportError(
                    "google-genai package not installed. "
                    "Install with: pip install google-genai"
                )
        return self._client

    def is_configured(self) -> bool:
        """Check if VEO_API_KEY is set."""
        return bool(self.api_key)

    def generate_video(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        number_of_videos: int = 1,
        person_generation: str = "ALLOW_ALL",
        output_dir: Path = None,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate video(s) using Google Veo 2.0.

        Args:
            prompt: Text prompt describing the video to generate
            aspect_ratio: "16:9" or "16:10"
            duration_seconds: 5-8 seconds
            number_of_videos: 1-4 videos
            person_generation: "ALLOW_ALL" or other policy
            output_dir: Directory to save generated videos
            on_progress: Optional callback for progress updates

        Returns:
            Dict with success status and video file paths
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "VEO_API_KEY not configured"
            }

        try:
            from google.genai import types

            client = self._get_client()

            # Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=number_of_videos,
                duration_seconds=duration_seconds,
                person_generation=person_generation,
            )

            # Start generation operation
            print(f"[VideoService] Starting video generation: {prompt[:50]}...")
            operation = client.models.generate_videos(
                model=self.MODEL,
                prompt=prompt,
                config=video_config,
            )

            # Poll for completion
            poll_count = 0
            max_polls = 120  # 20 minutes max (10 sec intervals)

            while not operation.done:
                poll_count += 1
                if poll_count > max_polls:
                    return {
                        "success": False,
                        "error": "Video generation timed out after 20 minutes"
                    }

                progress_msg = f"Generating video... (check {poll_count})"
                print(f"[VideoService] {progress_msg}")

                if on_progress:
                    on_progress(progress_msg)

                time.sleep(10)
                operation = client.operations.get(operation)

            # Get result
            result = operation.result
            if not result:
                return {
                    "success": False,
                    "error": "No result returned from video generation"
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "success": False,
                    "error": "No videos were generated"
                }

            # Download videos
            print(f"[VideoService] Generated {len(generated_videos)} video(s)")
            video_files = []

            for idx, generated_video in enumerate(generated_videos):
                video_uri = generated_video.video.uri
                print(f"[VideoService] Downloading: {video_uri}")

                # Download file
                client.files.download(file=generated_video.video)

                # Save to output directory
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"video_{idx + 1}.mp4"
                    file_path = output_dir / filename
                    generated_video.video.save(str(file_path))
                    print(f"[VideoService] Saved: {file_path}")

                    video_files.append({
                        "filename": filename,
                        "path": str(file_path),
                        "uri": video_uri,
                        "index": idx + 1
                    })
                else:
                    # Just save with default name
                    filename = f"video_{idx}.mp4"
                    generated_video.video.save(filename)
                    video_files.append({
                        "filename": filename,
                        "path": filename,
                        "uri": video_uri,
                        "index": idx
                    })

            return {
                "success": True,
                "videos": video_files,
                "count": len(video_files)
            }

        except Exception as e:
            print(f"[VideoService] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
google_video_service = GoogleVideoService()
