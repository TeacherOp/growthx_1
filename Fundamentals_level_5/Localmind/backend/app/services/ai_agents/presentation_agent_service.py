"""
Presentation Agent Service - AI agent for generating PowerPoint presentations.

Educational Note: Agentic loop pattern for multi-slide HTML generation:
1. Agent plans the presentation structure (plan_presentation)
2. Agent creates base-styles.css with brand colors (create_base_styles)
3. Agent creates individual slides as HTML files (create_slide - multiple calls)
4. Agent finalizes when complete (finalize_presentation - termination tool)

After generation:
- Playwright captures screenshots of each slide (1920x1080)
- python-pptx stitches screenshots into a PPTX file

Tools:
- plan_presentation: Client tool - plan slides, content, design system
- create_base_styles: Client tool - create brand CSS file
- create_slide: Client tool - create individual slide HTML files
- finalize_presentation: Termination tool - signals completion
"""

import os
import uuid
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from app.services.integrations.claude import claude_service
from app.config import prompt_loader, tool_loader
from app.utils import claude_parsing_utils
from app.utils.path_utils import get_studio_dir, get_sources_dir
from app.services.data_services import message_service
from app.services.studio_services import studio_index_service


class PresentationAgentService:
    """
    Presentation generation agent with HTML slides workflow.

    Educational Note: This agent demonstrates:
    - Multi-file generation (CSS + multiple HTML slides)
    - Sequential slide creation for consistent styling
    - Screenshot capture for PPTX export
    - Clean separation of brand styles and content
    """

    AGENT_NAME = "presentation_agent"
    MAX_ITERATIONS = 40  # More iterations for presentations with many slides

    def __init__(self):
        """Initialize agent with lazy-loaded config and tools."""
        self._prompt_config = None
        self._tools = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("presentation_agent")
        return self._prompt_config

    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load all 4 presentation agent tools."""
        if self._tools is None:
            self._tools = tool_loader.load_tools_for_agent(self.AGENT_NAME)
        return self._tools

    # =========================================================================
    # Main Agent Execution
    # =========================================================================

    def generate_presentation(
        self,
        project_id: str,
        source_id: str,
        job_id: str,
        direction: str = ""
    ) -> Dict[str, Any]:
        """
        Run the agent to generate a presentation.

        Educational Note: The agent workflow:
        1. Get source content and direction
        2. Agent plans the presentation (slides, design)
        3. Agent creates base-styles.css with brand colors
        4. Agent creates slides sequentially (slide_01.html, slide_02.html, ...)
        5. Agent finalizes when all slides are complete
        6. We capture screenshots and export to PPTX
        """
        config = self._load_config()
        tools = self._load_tools()

        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Update job status
        studio_index_service.update_presentation_job(
            project_id, job_id,
            status="processing",
            status_message="Starting presentation generation...",
            started_at=started_at
        )

        # Get source content
        source_content = self._get_source_content(project_id, source_id)

        # Build initial user message
        user_message = f"""Create a professional presentation based on the following source content.

=== SOURCE CONTENT ===
{source_content}
=== END SOURCE CONTENT ===

Direction from user: {direction if direction else 'No specific direction provided - create a clear, professional presentation based on the content.'}

Please create a complete presentation following the workflow:
1. Plan the presentation structure (slides, content distribution, design)
2. Create base-styles.css with brand colors as CSS variables
3. Create each slide sequentially (slide_01.html, slide_02.html, etc.)
4. Finalize when all slides are complete"""

        messages = [{"role": "user", "content": user_message}]

        total_input_tokens = 0
        total_output_tokens = 0
        created_files = []  # Track created files
        slides_info = []  # Track slide metadata

        print(f"[PresentationAgent] Starting (job_id: {job_id[:8]})")

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            print(f"  Iteration {iteration}/{self.MAX_ITERATIONS}")

            # Call Claude API
            response = claude_service.send_message(
                messages=messages,
                system_prompt=config["system_prompt"],
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                tools=tools["all_tools"] if isinstance(tools, dict) else tools,
                tool_choice={"type": "any"},
                project_id=project_id
            )

            # Track token usage
            total_input_tokens += response["usage"]["input_tokens"]
            total_output_tokens += response["usage"]["output_tokens"]

            # Serialize and add assistant response to messages
            content_blocks = response.get("content_blocks", [])
            serialized_content = claude_parsing_utils.serialize_content_blocks(content_blocks)
            messages.append({"role": "assistant", "content": serialized_content})

            # Process tool calls
            tool_results = []

            for block in content_blocks:
                block_type = getattr(block, "type", None) if hasattr(block, "type") else block.get("type")

                if block_type == "tool_use":
                    tool_name = getattr(block, "name", "") if hasattr(block, "name") else block.get("name", "")
                    tool_input = getattr(block, "input", {}) if hasattr(block, "input") else block.get("input", {})
                    tool_id = getattr(block, "id", "") if hasattr(block, "id") else block.get("id", "")

                    print(f"    Tool: {tool_name}")

                    # Tool 1: Plan the presentation
                    if tool_name == "plan_presentation":
                        result = self._handle_plan_presentation(project_id, job_id, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 2: Create base styles
                    elif tool_name == "create_base_styles":
                        result = self._handle_create_base_styles(
                            project_id, job_id, tool_input, created_files
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 3: Create slide
                    elif tool_name == "create_slide":
                        result = self._handle_create_slide(
                            project_id, job_id, tool_input, created_files, slides_info
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 4: Finalize presentation (TERMINATION)
                    elif tool_name == "finalize_presentation":
                        final_result = self._handle_finalize_presentation(
                            project_id, job_id, source_id, tool_input,
                            created_files, slides_info, iteration,
                            total_input_tokens, total_output_tokens
                        )

                        print(f"  Completed in {iteration} iterations")

                        # Save execution log
                        self._save_execution(
                            project_id, execution_id, job_id, messages,
                            final_result, started_at, source_id
                        )

                        return final_result

            # Add tool results to messages
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        print(f"  Max iterations reached ({self.MAX_ITERATIONS})")
        error_result = {
            "success": False,
            "error_message": f"Agent reached maximum iterations ({self.MAX_ITERATIONS})",
            "iterations": self.MAX_ITERATIONS,
            "usage": {"input_tokens": total_input_tokens, "output_tokens": total_output_tokens}
        }

        studio_index_service.update_presentation_job(
            project_id, job_id,
            status="error",
            error_message=error_result["error_message"]
        )

        self._save_execution(
            project_id, execution_id, job_id, messages,
            error_result, started_at, source_id
        )

        return error_result

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    def _handle_plan_presentation(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle plan_presentation tool call."""
        title = tool_input.get("presentation_title", "Untitled Presentation")
        slides = tool_input.get("slides", [])
        presentation_type = tool_input.get("presentation_type", "business")

        print(f"      Planning: {title} ({len(slides)} slides)")

        # Update job with plan
        studio_index_service.update_presentation_job(
            project_id, job_id,
            presentation_title=title,
            presentation_type=presentation_type,
            target_audience=tool_input.get("target_audience"),
            planned_slides=slides,
            design_system=tool_input.get("design_system"),
            style_notes=tool_input.get("style_notes"),
            status_message=f"Planned {len(slides)}-slide presentation, creating base styles..."
        )

        return f"Presentation plan saved successfully. Title: '{title}', Type: {presentation_type}, Slides: {len(slides)}. Now create base-styles.css with the design system colors."

    def _handle_create_base_styles(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any],
        created_files: List[str]
    ) -> str:
        """Handle create_base_styles tool call."""
        content = tool_input.get("content", "")

        print(f"      Creating: base-styles.css ({len(content)} chars)")

        try:
            # Create slides directory
            slides_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id / "slides"
            slides_dir.mkdir(parents=True, exist_ok=True)

            file_path = slides_dir / "base-styles.css"

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Track created file
            if "base-styles.css" not in created_files:
                created_files.append("base-styles.css")

            # Update job
            studio_index_service.update_presentation_job(
                project_id, job_id,
                files=created_files,
                status_message="Base styles created, generating slides..."
            )

            print(f"      Saved: base-styles.css")

            return f"base-styles.css created successfully ({len(content)} characters). Now create slides starting with slide_01.html."

        except Exception as e:
            return f"Error creating base-styles.css: {str(e)}"

    def _handle_create_slide(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any],
        created_files: List[str],
        slides_info: List[Dict[str, str]]
    ) -> str:
        """Handle create_slide tool call."""
        slide_number = tool_input.get("slide_number", 1)
        slide_type = tool_input.get("slide_type", "bullet_points")
        content = tool_input.get("content", "")

        filename = f"slide_{slide_number:02d}.html"

        print(f"      Creating: {filename} ({slide_type}, {len(content)} chars)")

        try:
            # Get slides directory
            slides_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id / "slides"
            slides_dir.mkdir(parents=True, exist_ok=True)

            file_path = slides_dir / filename

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Track created file
            if filename not in created_files:
                created_files.append(filename)

            # Track slide info (for finalization)
            slides_info.append({
                "filename": filename,
                "slide_number": slide_number,
                "slide_type": slide_type
            })

            # Update job
            slide_count = len([f for f in created_files if f.startswith("slide_")])
            studio_index_service.update_presentation_job(
                project_id, job_id,
                files=created_files,
                slides_created=slide_count,
                status_message=f"Created {filename} ({slide_count} slides so far)"
            )

            print(f"      Saved: {filename}")

            return f"Slide {slide_number} ({filename}) created successfully. Type: {slide_type}, Size: {len(content)} characters."

        except Exception as e:
            return f"Error creating slide {slide_number}: {str(e)}"

    def _handle_finalize_presentation(
        self,
        project_id: str,
        job_id: str,
        source_id: str,
        tool_input: Dict[str, Any],
        created_files: List[str],
        slides_info: List[Dict[str, str]],
        iterations: int,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """Handle finalize_presentation tool call (termination)."""
        summary = tool_input.get("summary", "")
        total_slides = tool_input.get("total_slides", 0)
        slides_created = tool_input.get("slides_created", [])
        design_notes = tool_input.get("design_notes", "")

        print(f"      Finalizing presentation ({total_slides} slides)")

        try:
            # Get job info
            job = studio_index_service.get_presentation_job(project_id, job_id)
            title = job.get("presentation_title", "Presentation") if job else "Presentation"

            # Get list of slide files in order
            slides_dir = Path(get_studio_dir(project_id)) / "presentations" / job_id / "slides"
            slide_files = sorted([
                f for f in created_files
                if f.startswith("slide_") and f.endswith(".html")
            ])

            # Update job to ready (export will happen separately)
            studio_index_service.update_presentation_job(
                project_id, job_id,
                status="ready",
                status_message="Presentation generated! Ready for export.",
                files=created_files,
                slide_files=slide_files,
                slides_metadata=slides_created,
                summary=summary,
                design_notes=design_notes,
                total_slides=len(slide_files),
                preview_url=f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/preview",
                download_url=f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/download",
                iterations=iterations,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completed_at=datetime.now().isoformat()
            )

            return {
                "success": True,
                "job_id": job_id,
                "presentation_title": title,
                "total_slides": len(slide_files),
                "slide_files": slide_files,
                "files": created_files,
                "summary": summary,
                "preview_url": f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/preview",
                "download_url": f"/api/v1/projects/{project_id}/studio/presentations/{job_id}/download",
                "iterations": iterations,
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }

        except Exception as e:
            error_msg = f"Error finalizing presentation: {str(e)}"
            print(f"      {error_msg}")

            studio_index_service.update_presentation_job(
                project_id, job_id,
                status="error",
                error_message=error_msg
            )

            return {
                "success": False,
                "error_message": error_msg,
                "iterations": iterations,
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_source_content(self, project_id: str, source_id: str) -> str:
        """
        Get source content for the presentation.

        Educational Note: Same pattern as other studio services - sample chunks
        for large sources, use full content for small sources.
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
            if len(full_content) < 20000:  # ~5000 tokens
                return full_content

            # For large sources, sample chunks
            chunks_dir = os.path.join(sources_dir, "chunks", source_id)
            if not os.path.exists(chunks_dir):
                # No chunks, return truncated content
                return full_content[:20000] + "\n\n[Content truncated...]"

            # Get all chunks
            chunk_files = sorted([
                f for f in os.listdir(chunks_dir)
                if f.endswith(".txt") and f.startswith(source_id)
            ])

            if not chunk_files:
                return full_content[:20000] + "\n\n[Content truncated...]"

            # Sample up to 12 chunks evenly distributed
            max_chunks = 12
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
            print(f"[PresentationAgent] Error getting source content: {e}")
            return f"Error loading source content: {str(e)}"

    def _save_execution(
        self,
        project_id: str,
        execution_id: str,
        job_id: str,
        messages: List[Dict[str, Any]],
        result: Dict[str, Any],
        started_at: str,
        source_id: str
    ) -> None:
        """Save execution log using message_service."""
        message_service.save_agent_execution(
            project_id=project_id,
            agent_name=self.AGENT_NAME,
            execution_id=execution_id,
            task=f"Generate presentation (job: {job_id[:8]})",
            messages=messages,
            result=result,
            started_at=started_at,
            metadata={"source_id": source_id, "job_id": job_id}
        )


# Singleton instance
presentation_agent_service = PresentationAgentService()
