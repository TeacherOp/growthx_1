"""
Image Service - Manages image processing and content extraction using tool-based approach.

Educational Note: This service extracts comprehensive content from images using Claude's
vision capabilities. It uses a tool-based approach similar to PDF extraction:
- Images are sent as base64-encoded content blocks
- Claude analyzes the image and calls submit_image_extraction tool
- The tool returns structured data about the image content
- Results are saved as text files for use in chat context

Supported formats: JPEG, PNG, GIF, WebP (max 5MB each per API constraint)
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import threading

from app.services.claude_service import claude_service
from app.services.task_service import task_service
from app.services.tool_loader import tool_loader
from app.services.message_service import message_service
from app.utils.encoding import encode_file_to_base64, get_media_type
from app.utils.tier_config import get_anthropic_config
from config import Config


class ImageService:
    """
    Service class for extracting content from images using Claude's vision.

    Educational Note: This service handles image analysis:
    1. Reads image file and encodes to base64
    2. Sends to Claude with submit_image_extraction tool
    3. Parses structured response (subject, text, visuals, data, etc.)
    4. Saves combined content as text file for chat context
    """

    def __init__(self):
        """Initialize the image service."""
        self.projects_dir = Config.PROJECTS_DIR
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self._prompt_config = None
        self._tool_definition = None
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0.0
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

    def _get_tier_config(self) -> Dict[str, Any]:
        """Get tier configuration for rate limiting."""
        return get_anthropic_config()

    def _rate_limit(self, requests_per_minute: int) -> None:
        """Apply rate limiting to API calls."""
        with self._rate_limit_lock:
            current_time = time.time()

            if current_time - self._minute_start_time >= 60:
                self._requests_this_minute = 0
                self._minute_start_time = current_time

            if self._requests_this_minute >= requests_per_minute:
                wait_time = 60 - (current_time - self._minute_start_time)
                if wait_time > 0:
                    print(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    self._requests_this_minute = 0
                    self._minute_start_time = time.time()

            self._requests_this_minute += 1

    def _load_prompt_config(self) -> Dict[str, Any]:
        """Load the image extraction prompt configuration."""
        if self._prompt_config is None:
            prompt_path = self.prompts_dir / "image_extraction_prompt.json"

            if not prompt_path.exists():
                raise FileNotFoundError(f"Image extraction prompt not found: {prompt_path}")

            with open(prompt_path, "r") as f:
                self._prompt_config = json.load(f)

        return self._prompt_config

    def _load_tool_definition(self) -> Dict[str, Any]:
        """Load the image extraction tool definition."""
        if self._tool_definition is None:
            self._tool_definition = tool_loader.load_tool("image_tools", "image_extraction")
        return self._tool_definition

    def _get_processed_dir(self, project_id: str) -> Path:
        """Get the processed files directory for a project."""
        processed_dir = self.projects_dir / project_id / "sources" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        return processed_dir

    def _parse_tool_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse image extraction tool response from Claude.

        Educational Note: Uses message_service for generic tool parsing,
        then extracts image-specific fields.
        """
        tool_inputs = message_service.extract_tool_inputs(response, "submit_image_extraction")

        if not tool_inputs:
            return {
                "success": False,
                "error": "No tool call received from Claude"
            }

        inputs = tool_inputs[0]
        return {
            "success": True,
            "subject": inputs.get("subject", ""),
            "content_type": inputs.get("content_type", "other"),
            "text_content": inputs.get("text_content", "[NO TEXT]"),
            "visual_description": inputs.get("visual_description", ""),
            "colors_and_style": inputs.get("colors_and_style", ""),
            "data_content": inputs.get("data_content", "[NO DATA]"),
            "summary": inputs.get("summary", "")
        }

    def _format_extraction_as_text(
        self,
        extraction: Dict[str, Any],
        image_name: str
    ) -> str:
        """
        Format extracted image data as readable text for storage.

        Educational Note: Combines all extracted fields into a structured
        text format that can be used as context in chat conversations.
        """
        lines = [
            f"# Image: {image_name}",
            f"# Extracted at: {datetime.now().isoformat()}",
            "",
            f"## Subject",
            extraction.get("subject", ""),
            "",
            f"## Content Type",
            extraction.get("content_type", "other"),
            "",
            f"## Text Content",
            extraction.get("text_content", "[NO TEXT]"),
            "",
            f"## Visual Description",
            extraction.get("visual_description", ""),
            "",
            f"## Colors and Style",
            extraction.get("colors_and_style", ""),
            "",
            f"## Data Content",
            extraction.get("data_content", "[NO DATA]"),
            "",
            f"## Summary",
            extraction.get("summary", ""),
        ]
        return "\n".join(lines)

    def extract_content_from_image(
        self,
        project_id: str,
        source_id: str,
        image_path: Path
    ) -> Dict[str, Any]:
        """
        Extract content from a single image file.

        Educational Note: This is the main entry point for image processing.
        1. Loads image and encodes to base64
        2. Sends to Claude with image content block
        3. Forces tool use for structured extraction
        4. Saves result as text file

        Args:
            project_id: The project UUID
            source_id: The source UUID
            image_path: Path to the image file

        Returns:
            Dict with extraction results
        """
        print(f"Starting image extraction for source: {source_id}")

        processed_dir = self._get_processed_dir(project_id)
        output_path = processed_dir / f"{source_id}.txt"

        try:
            prompt_config = self._load_prompt_config()
            tool_def = self._load_tool_definition()
            tier_config = self._get_tier_config()

            model = prompt_config.get("model", "claude-haiku-4-5-20251001")
            system_prompt = prompt_config.get("system_prompt", "")
            user_message = prompt_config.get("user_message", "")
            max_tokens = prompt_config.get("max_tokens", 4000)
            temperature = prompt_config.get("temperature", 0.2)

            print(f"Using model: {model}")

            image_base64 = encode_file_to_base64(image_path)
            media_type = get_media_type(image_path)

            print(f"Image encoded: {image_path.name} ({media_type})")

            content_blocks = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": user_message
                }
            ]

            messages = [{"role": "user", "content": content_blocks}]

            requests_per_minute = tier_config.get("pages_per_minute", 100)
            self._rate_limit(requests_per_minute)

            response = claude_service.send_message(
                messages=messages,
                system_prompt=system_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=[tool_def],
                tool_choice={"type": "tool", "name": "submit_image_extraction"},
                project_id=project_id
            )

            extraction = self._parse_tool_response(response)

            if not extraction.get("success"):
                raise Exception(extraction.get("error", "Extraction failed"))

            formatted_text = self._format_extraction_as_text(
                extraction,
                image_path.name
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_text)

            print(f"Image extraction complete: {image_path.name}")

            return {
                "success": True,
                "status": "ready",
                "extracted_text_path": str(output_path),
                "character_count": len(formatted_text),
                "content_type": extraction.get("content_type"),
                "summary": extraction.get("summary"),
                "token_usage": response.get("usage", {}),
                "model_used": model,
                "extracted_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Image extraction failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }

    def extract_content_from_images_batch(
        self,
        project_id: str,
        source_id: str,
        image_paths: List[Path]
    ) -> Dict[str, Any]:
        """
        Extract content from multiple images in a single source.

        Educational Note: When multiple images are uploaded together,
        we process each one and combine results into a single output file.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            image_paths: List of paths to image files

        Returns:
            Dict with extraction results for all images
        """
        print(f"Starting batch image extraction for {len(image_paths)} images")

        processed_dir = self._get_processed_dir(project_id)
        output_path = processed_dir / f"{source_id}.txt"

        try:
            prompt_config = self._load_prompt_config()
            tool_def = self._load_tool_definition()
            tier_config = self._get_tier_config()

            model = prompt_config.get("model", "claude-haiku-4-5-20251001")
            system_prompt = prompt_config.get("system_prompt", "")
            max_tokens = prompt_config.get("max_tokens", 4000)
            temperature = prompt_config.get("temperature", 0.2)

            all_extractions = []
            total_input_tokens = 0
            total_output_tokens = 0

            for idx, image_path in enumerate(image_paths, 1):
                if task_service.is_target_cancelled(source_id):
                    print(f"Processing cancelled for source {source_id}")
                    raise Exception("Processing cancelled by user")

                print(f"Processing image {idx}/{len(image_paths)}: {image_path.name}")

                image_base64 = encode_file_to_base64(image_path)
                media_type = get_media_type(image_path)

                user_message = prompt_config.get("user_message", "")

                content_blocks = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]

                messages = [{"role": "user", "content": content_blocks}]

                requests_per_minute = tier_config.get("pages_per_minute", 100)
                self._rate_limit(requests_per_minute)

                response = claude_service.send_message(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=[tool_def],
                    tool_choice={"type": "tool", "name": "submit_image_extraction"},
                    project_id=project_id
                )

                extraction = self._parse_tool_response(response)
                extraction["image_name"] = image_path.name

                all_extractions.append(extraction)

                total_input_tokens += response.get("usage", {}).get("input_tokens", 0)
                total_output_tokens += response.get("usage", {}).get("output_tokens", 0)

            output_lines = [
                f"# Batch Image Extraction",
                f"# Total images: {len(image_paths)}",
                f"# Extracted at: {datetime.now().isoformat()}",
                ""
            ]

            for extraction in all_extractions:
                image_text = self._format_extraction_as_text(
                    extraction,
                    extraction.get("image_name", "unknown")
                )
                output_lines.append(image_text)
                output_lines.append("")
                output_lines.append("---")
                output_lines.append("")

            combined_text = "\n".join(output_lines)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(combined_text)

            print(f"Batch extraction complete: {len(image_paths)} images processed")

            return {
                "success": True,
                "status": "ready",
                "extracted_text_path": str(output_path),
                "images_processed": len(image_paths),
                "character_count": len(combined_text),
                "token_usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens
                },
                "model_used": model,
                "extracted_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Batch image extraction failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }


# Singleton instance
image_service = ImageService()
