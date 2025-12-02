"""
Ad Creative Service - Generates ad creatives for Facebook/Instagram.

Educational Note: This service implements a two-step AI pipeline:
1. Claude Haiku generates optimized image prompts from product info
2. Google Gemini generates images from those prompts

Flow:
- Input: Product name + direction from chat signal
- Step 1: Haiku creates 3 image prompts (hero, lifestyle, aspirational)
- Step 2: Gemini generates images for each prompt
- Output: 3 ad creative images saved to disk
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.services.integrations.claude import claude_service
from app.services.integrations.google.imagen_service import imagen_service
from app.services.studio_services import studio_index_service
from app.config import prompt_loader
from app.utils.path_utils import get_studio_dir


def get_studio_creatives_dir(project_id: str) -> Path:
    """Get the directory for ad creative images."""
    studio_dir = get_studio_dir(project_id)
    creatives_dir = studio_dir / "creatives"
    creatives_dir.mkdir(parents=True, exist_ok=True)
    return creatives_dir


class AdCreativeService:
    """
    Service for generating ad creatives.

    Educational Note: This service orchestrates the full pipeline:
    1. Haiku generates image prompts from product info
    2. Gemini generates images from each prompt
    """

    def __init__(self):
        """Initialize service with lazy-loaded config."""
        self._prompt_config = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("ad_creative")
        return self._prompt_config

    def generate_ad_creatives(
        self,
        project_id: str,
        job_id: str,
        product_name: str,
        direction: str = ""
    ) -> Dict[str, Any]:
        """
        Generate ad creatives for a product.

        Educational Note: This is the main orchestrator that:
        1. Uses Haiku to generate image prompts
        2. Uses Gemini to generate images
        3. Updates job status throughout

        Args:
            project_id: The project UUID
            job_id: The job ID for status tracking
            product_name: Name of the product to create ads for
            direction: Additional context/direction from the user

        Returns:
            Dict with success status, image paths, and metadata
        """
        started_at = datetime.now()

        # Update job to processing
        studio_index_service.update_ad_job(
            project_id, job_id,
            status="processing",
            progress="Generating image prompts...",
            started_at=datetime.now().isoformat()
        )

        print(f"[AdCreative] Starting job {job_id}")
        print(f"  Product: {product_name}")

        # Step 1: Generate image prompts with Haiku
        prompts_result = self._generate_prompts(
            project_id=project_id,
            product_name=product_name,
            direction=direction,
            job_id=job_id
        )

        if not prompts_result.get("success"):
            studio_index_service.update_ad_job(
                project_id, job_id,
                status="error",
                error=prompts_result.get("error", "Failed to generate prompts"),
                completed_at=datetime.now().isoformat()
            )
            return prompts_result

        prompts = prompts_result.get("prompts", [])
        print(f"  Generated {len(prompts)} prompts")

        # Update progress
        studio_index_service.update_ad_job(
            project_id, job_id,
            progress="Generating images..."
        )

        # Step 2: Generate images with Gemini
        creatives_dir = get_studio_creatives_dir(project_id)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        all_images = []

        for i, prompt_data in enumerate(prompts):
            prompt_type = prompt_data.get("type", f"image_{i+1}")
            prompt_text = prompt_data.get("prompt", "")

            if not prompt_text:
                continue

            print(f"  Generating {prompt_type} image...")

            # Update progress
            studio_index_service.update_ad_job(
                project_id, job_id,
                progress=f"Generating {prompt_type} image ({i+1}/{len(prompts)})..."
            )

            # Generate single image for this prompt
            result = imagen_service.generate_images(
                prompt=prompt_text,
                output_dir=creatives_dir,
                num_images=1,
                filename_prefix=f"ad_{job_id[:8]}_{prompt_type}_{timestamp}"
            )

            if result.get("success") and result.get("images"):
                image_info = result["images"][0]
                image_info["type"] = prompt_type
                image_info["prompt"] = prompt_text
                all_images.append(image_info)

        if not all_images:
            studio_index_service.update_ad_job(
                project_id, job_id,
                status="error",
                error="No images were generated",
                completed_at=datetime.now().isoformat()
            )
            return {
                "success": False,
                "error": "No images were generated"
            }

        # Step 3: Update job as complete
        duration = (datetime.now() - started_at).total_seconds()

        # Build image URLs
        for img in all_images:
            img["url"] = f"/api/v1/projects/{project_id}/studio/creatives/{img['filename']}"

        studio_index_service.update_ad_job(
            project_id, job_id,
            status="ready",
            progress="Complete",
            images=all_images,
            completed_at=datetime.now().isoformat()
        )

        print(f"  Generated {len(all_images)} images in {duration:.1f}s")

        return {
            "success": True,
            "job_id": job_id,
            "product_name": product_name,
            "images": all_images,
            "count": len(all_images),
            "duration_seconds": duration,
            "usage": prompts_result.get("usage", {})
        }

    def _generate_prompts(
        self,
        project_id: str,
        product_name: str,
        direction: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Generate image prompts using Claude Haiku.

        Educational Note: Haiku reads the product info and generates
        optimized prompts for the image generation model.
        """
        config = self._load_config()

        # Build user message
        user_message = config["user_message"].format(
            product_name=product_name,
            direction=direction or "Create compelling ad creatives for Facebook and Instagram."
        )

        messages = [{"role": "user", "content": user_message}]

        try:
            response = claude_service.send_message(
                messages=messages,
                system_prompt=config["system_prompt"],
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                project_id=project_id
            )

            # Extract text from response
            content_blocks = response.get("content_blocks", [])
            text_content = ""
            for block in content_blocks:
                if hasattr(block, "text"):
                    text_content = block.text
                    break
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_content = block.get("text", "")
                    break

            if not text_content:
                return {
                    "success": False,
                    "error": "No text response from Claude"
                }

            # Parse JSON from response
            # Find JSON in the response (might be wrapped in markdown code blocks)
            json_start = text_content.find("{")
            json_end = text_content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                return {
                    "success": False,
                    "error": "No JSON found in Claude response"
                }

            json_str = text_content[json_start:json_end]
            parsed = json.loads(json_str)
            prompts = parsed.get("prompts", [])

            return {
                "success": True,
                "prompts": prompts,
                "usage": response.get("usage", {})
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse Claude response as JSON: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate prompts: {str(e)}"
            }


# Singleton instance
ad_creative_service = AdCreativeService()
