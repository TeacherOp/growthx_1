"""
Video Prompt Service - AI service for generating optimized video prompts.

Educational Note: This is a simple AI service that uses Claude to generate
detailed, vivid video prompts from source content. The generated prompts are
then used with Google Veo 2.0 for video generation.
"""
import os
from typing import Dict, Any

from app.services.integrations.claude import claude_service
from app.config import prompt_loader
from app.utils import claude_parsing_utils
from app.utils.path_utils import get_sources_dir


class VideoPromptService:
    """
    Simple AI service for generating video prompts.

    Educational Note: Takes source content + user direction, uses Claude to
    craft an optimized prompt for video generation. Single API call, no loop.
    """

    def generate_video_prompt(
        self,
        project_id: str,
        source_id: str,
        direction: str = ""
    ) -> Dict[str, Any]:
        """
        Generate an optimized video prompt from source content.

        Args:
            project_id: Project ID
            source_id: Source to generate prompt from
            direction: User's direction/guidance

        Returns:
            Dict with success status and generated prompt
        """
        print(f"[VideoPromptService] Generating video prompt for source {source_id[:8]}")

        # Load prompt config
        config = prompt_loader.get_prompt_config("video")

        # Get source content (sample for large sources)
        source_content = self._get_source_content(project_id, source_id)

        # Build user message
        user_message = f"""Create a detailed video prompt based on this content:

=== SOURCE CONTENT ===
{source_content}
=== END SOURCE ===

User Direction: {direction if direction else 'Create an engaging video that captures the essence of this content.'}

Generate a clear, vivid video prompt (2-4 sentences) that describes what should be in the video. Include specific visual details, camera movements, lighting, and mood. Remember: the video will be 5-8 seconds, so keep it focused on a single scene or smooth transition."""

        # Call Claude
        try:
            response = claude_service.send_message(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=config["system_prompt"],
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                project_id=project_id
            )

            # Extract text response
            prompt_text = claude_parsing_utils.extract_text(response)

            if not prompt_text:
                return {
                    "success": False,
                    "error": "No prompt generated from Claude"
                }

            # Clean up the prompt (remove any markdown, quotes, etc.)
            prompt_text = prompt_text.strip().strip('"').strip("'")

            print(f"[VideoPromptService] Generated prompt: {prompt_text[:100]}...")

            return {
                "success": True,
                "prompt": prompt_text,
                "usage": response.get("usage", {})
            }

        except Exception as e:
            print(f"[VideoPromptService] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _get_source_content(self, project_id: str, source_id: str) -> str:
        """
        Get source content for prompt generation.

        Educational Note: Sample chunks for large sources, use full content for small ones.
        """
        try:
            from app.services.source_services import source_service

            source = source_service.get_source(project_id, source_id)
            if not source:
                return "Error: Source not found"

            # Get processed content
            sources_dir = get_sources_dir(project_id)
            processed_path = os.path.join(sources_dir, "processed", f"{source_id}.txt")

            if not os.path.exists(processed_path):
                return f"Source: {source.get('name', 'Unknown')}\n(Content not yet processed)"

            with open(processed_path, "r", encoding="utf-8") as f:
                full_content = f.read()

            # If content is small enough, use it all
            if len(full_content) < 10000:  # ~2500 tokens
                return full_content

            # For large sources, sample chunks
            chunks_dir = os.path.join(sources_dir, "chunks", source_id)
            if not os.path.exists(chunks_dir):
                # No chunks, return truncated content
                return full_content[:10000] + "\n\n[Content truncated...]"

            # Get all chunks
            chunk_files = sorted([
                f for f in os.listdir(chunks_dir)
                if f.endswith(".txt") and f.startswith(source_id)
            ])

            if not chunk_files:
                return full_content[:10000] + "\n\n[Content truncated...]"

            # Sample up to 6 chunks evenly distributed
            max_chunks = 6
            if len(chunk_files) <= max_chunks:
                selected_chunks = chunk_files
            else:
                step = len(chunk_files) / max_chunks
                selected_chunks = [chunk_files[int(i * step)] for i in range(max_chunks)]

            # Read selected chunks
            sampled_content = []
            for chunk_file in selected_chunks:
                chunk_path = os.path.join(chunks_dir, chunk_file)
                with open(chunk_path, "r", encoding="utf-8") as f:
                    sampled_content.append(f.read())

            return "\n\n".join(sampled_content)

        except Exception as e:
            print(f"[VideoPromptService] Error getting source content: {e}")
            return f"Error loading source content: {str(e)}"


# Singleton instance
video_prompt_service = VideoPromptService()
