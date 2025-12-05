"""
Blog Agent Service - AI agent for generating comprehensive blog posts.

Educational Note: Agentic loop pattern for multi-step content creation:
1. Agent plans the blog structure (plan_blog_post)
2. Agent generates images as needed (generate_blog_image - can be called multiple times)
3. Agent writes the final markdown content (write_blog_post - termination tool)
4. All tools are client tools - we execute them and update job status

Tools:
- plan_blog_post: Client tool - plan structure, outline, images needed
- generate_blog_image: Client tool - generate images via Gemini
- write_blog_post: Termination tool - write final markdown, signals completion
"""

import os
import uuid
from typing import Dict, Any, List
from datetime import datetime

from app.services.integrations.claude import claude_service
from app.services.integrations.google import imagen_service
from app.config import prompt_loader, tool_loader
from app.utils import claude_parsing_utils
from app.utils.path_utils import get_studio_dir, get_sources_dir
from app.services.data_services import message_service
from app.services.studio_services import studio_index_service


class BlogAgentService:
    """
    Blog post generation agent with multi-step creative workflow.

    Educational Note: This agent demonstrates how AI can orchestrate
    a complex content creation process: planning → image generation → writing.
    The blog post includes SEO optimization for the target keyword.
    """

    AGENT_NAME = "blog_agent"
    MAX_ITERATIONS = 20  # More iterations for long-form content

    def __init__(self):
        """Initialize agent with lazy-loaded config and tools."""
        self._prompt_config = None
        self._tools = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("blog_agent")
        return self._prompt_config

    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load all 3 agent tools."""
        if self._tools is None:
            self._tools = tool_loader.load_tools_for_agent(self.AGENT_NAME)
        return self._tools

    # =========================================================================
    # Main Agent Execution
    # =========================================================================

    def generate_blog_post(
        self,
        project_id: str,
        source_id: str,
        job_id: str,
        direction: str = "",
        target_keyword: str = "",
        blog_type: str = "how_to_guide"
    ) -> Dict[str, Any]:
        """
        Run the agent to generate a comprehensive blog post.

        Educational Note: The agent workflow:
        1. Get source content, target keyword, and blog type
        2. Agent plans the blog structure (title, outline, image needs)
        3. Agent generates images for sections that need them
        4. Agent writes the complete markdown blog post (3000+ words)
        5. We save everything and update job status
        """
        config = self._load_config()
        tools = self._load_tools()

        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Update job status
        studio_index_service.update_blog_job(
            project_id, job_id,
            status="processing",
            status_message="Starting blog post generation..."
        )

        # Get source content
        source_content = self._get_source_content(project_id, source_id)

        # Map blog_type to human-readable format
        blog_type_display = self._get_blog_type_display(blog_type)

        # Build initial user message
        user_message = f"""Create a comprehensive, SEO-optimized blog post based on the following source content.

=== SOURCE CONTENT ===
{source_content}
=== END SOURCE CONTENT ===

**Target Keyword:** {target_keyword if target_keyword else 'Use your best judgment based on the content'}
**Blog Type:** {blog_type_display}
**Direction from user:** {direction if direction else 'No specific direction provided - use your best judgment based on the content.'}

Please create a complete blog post following the workflow:
1. Plan the blog structure with SEO-optimized title, meta description, and detailed outline
2. Generate 2-4 images to enhance the post (hero image + section illustrations)
3. Write the complete markdown blog post (3000+ words) with all content, headings, and image placeholders"""

        messages = [{"role": "user", "content": user_message}]

        total_input_tokens = 0
        total_output_tokens = 0
        generated_images = []  # Track generated images

        print(f"[BlogAgent] Starting (job_id: {job_id[:8]}, keyword: {target_keyword[:30] if target_keyword else 'auto'})")

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

                    # Tool 1: Plan the blog post
                    if tool_name == "plan_blog_post":
                        result = self._handle_plan_blog(project_id, job_id, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 2: Generate image
                    elif tool_name == "generate_blog_image":
                        result = self._handle_generate_image(
                            project_id, job_id, tool_input, generated_images
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 3: Write blog post (TERMINATION)
                    elif tool_name == "write_blog_post":
                        final_result = self._handle_write_blog(
                            project_id, job_id, source_id, tool_input,
                            generated_images, iteration, total_input_tokens, total_output_tokens,
                            target_keyword, blog_type
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

        studio_index_service.update_blog_job(
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

    def _handle_plan_blog(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle plan_blog_post tool call."""
        title = tool_input.get("title", "Untitled Blog Post")
        print(f"      Planning: {title[:50]}...")

        # Update job with plan
        studio_index_service.update_blog_job(
            project_id, job_id,
            title=title,
            meta_description=tool_input.get("meta_description"),
            tone=tool_input.get("tone"),
            outline=tool_input.get("outline", []),
            target_word_count=tool_input.get("estimated_word_count", 3000),
            status_message="Blog planned, generating images..."
        )

        outline_sections = len(tool_input.get("outline", []))
        return f"Blog plan saved successfully. Title: '{title}', Sections: {outline_sections}, Target word count: {tool_input.get('estimated_word_count', 3000)}"

    def _handle_generate_image(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any],
        generated_images: List[Dict[str, str]]
    ) -> str:
        """Handle generate_blog_image tool call."""
        purpose = tool_input.get("purpose", "unknown")
        section_heading = tool_input.get("section_heading", "")
        image_prompt = tool_input.get("image_prompt", "")
        alt_text = tool_input.get("alt_text", "Blog image")
        aspect_ratio = tool_input.get("aspect_ratio", "16:9")

        print(f"      Generating image for: {purpose}")

        # Update status
        studio_index_service.update_blog_job(
            project_id, job_id,
            status_message=f"Generating image for {purpose}..."
        )

        try:
            # Prepare output directory
            from pathlib import Path
            studio_dir = get_studio_dir(project_id)
            blog_dir = Path(studio_dir) / "blogs"
            blog_dir.mkdir(parents=True, exist_ok=True)

            # Create filename prefix
            image_index = len(generated_images) + 1
            filename_prefix = f"{job_id}_image_{image_index}"

            # Generate image via Gemini
            image_result = imagen_service.generate_images(
                prompt=image_prompt,
                output_dir=blog_dir,
                num_images=1,
                filename_prefix=filename_prefix,
                aspect_ratio=aspect_ratio
            )

            if not image_result.get("success") or not image_result.get("images"):
                return f"Error generating image for {purpose}: {image_result.get('error', 'Unknown error')}"

            # Get the generated image info
            image_data = image_result["images"][0]
            filename = image_data["filename"]

            # Track generated image
            image_info = {
                "purpose": purpose,
                "section_heading": section_heading,
                "filename": filename,
                "placeholder": f"IMAGE_{image_index}",
                "alt_text": alt_text,
                "url": f"/api/v1/projects/{project_id}/studio/blogs/{filename}"
            }
            generated_images.append(image_info)

            # Update job
            studio_index_service.update_blog_job(
                project_id, job_id,
                images=generated_images
            )

            print(f"      Saved: {filename}")

            return f"Image generated successfully for '{purpose}'. Use placeholder 'IMAGE_{image_index}' in your markdown: ![{alt_text}](IMAGE_{image_index})"

        except Exception as e:
            error_msg = f"Error generating image for {purpose}: {str(e)}"
            print(f"      {error_msg}")
            return error_msg

    def _handle_write_blog(
        self,
        project_id: str,
        job_id: str,
        source_id: str,
        tool_input: Dict[str, Any],
        generated_images: List[Dict[str, str]],
        iterations: int,
        input_tokens: int,
        output_tokens: int,
        target_keyword: str,
        blog_type: str
    ) -> Dict[str, Any]:
        """Handle write_blog_post tool call (termination)."""
        markdown_content = tool_input.get("markdown_content", "")
        word_count = tool_input.get("word_count", 0)
        seo_notes = tool_input.get("seo_notes", "")

        print(f"      Writing markdown ({len(markdown_content)} chars, ~{word_count} words)")

        try:
            # Replace IMAGE_N placeholders with actual URLs
            final_markdown = markdown_content
            for image_info in generated_images:
                placeholder = image_info["placeholder"]
                actual_url = image_info["url"]
                # Handle markdown image syntax: ![alt](IMAGE_N)
                final_markdown = final_markdown.replace(f"({placeholder})", f"({actual_url})")
                # Handle any bare IMAGE_N references
                final_markdown = final_markdown.replace(placeholder, actual_url)

            # Save markdown file
            studio_dir = get_studio_dir(project_id)
            blog_dir = os.path.join(studio_dir, "blogs")
            os.makedirs(blog_dir, exist_ok=True)

            markdown_filename = f"{job_id}.md"
            markdown_path = os.path.join(blog_dir, markdown_filename)

            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)

            print(f"      Saved: {markdown_filename}")

            # Get job info for title
            job = studio_index_service.get_blog_job(project_id, job_id)
            title = job.get("title", "Blog Post")

            # Update job to ready
            studio_index_service.update_blog_job(
                project_id, job_id,
                status="ready",
                status_message="Blog post generated successfully!",
                markdown_file=markdown_filename,
                markdown_url=f"/api/v1/projects/{project_id}/studio/blogs/{markdown_filename}",
                preview_url=f"/api/v1/projects/{project_id}/studio/blogs/{job_id}/preview",
                word_count=word_count,
                iterations=iterations,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completed_at=datetime.now().isoformat()
            )

            return {
                "success": True,
                "job_id": job_id,
                "title": title,
                "markdown_file": markdown_filename,
                "markdown_url": f"/api/v1/projects/{project_id}/studio/blogs/{markdown_filename}",
                "preview_url": f"/api/v1/projects/{project_id}/studio/blogs/{job_id}/preview",
                "images": generated_images,
                "word_count": word_count,
                "target_keyword": target_keyword,
                "blog_type": blog_type,
                "seo_notes": seo_notes,
                "iterations": iterations,
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }

        except Exception as e:
            error_msg = f"Error saving blog post: {str(e)}"
            print(f"      {error_msg}")

            studio_index_service.update_blog_job(
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

    def _get_blog_type_display(self, blog_type: str) -> str:
        """Convert blog_type slug to human-readable format."""
        type_map = {
            "case_study": "Case Study",
            "listicle": "Listicle",
            "how_to_guide": "How-To Guide",
            "opinion": "Opinion/Thought Leadership",
            "product_review": "Product Review",
            "news": "News/Announcement",
            "tutorial": "Tutorial",
            "comparison": "Comparison",
            "interview": "Interview",
            "roundup": "Roundup"
        }
        return type_map.get(blog_type, blog_type.replace("_", " ").title())

    def _get_source_content(self, project_id: str, source_id: str) -> str:
        """
        Get source content for the blog post.

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
            if len(full_content) < 15000:  # ~3500 tokens
                return full_content

            # For large sources, sample chunks (same logic as other services)
            chunks_dir = os.path.join(sources_dir, "chunks", source_id)
            if not os.path.exists(chunks_dir):
                # No chunks, return truncated content
                return full_content[:15000] + "\n\n[Content truncated...]"

            # Get all chunks
            chunk_files = sorted([
                f for f in os.listdir(chunks_dir)
                if f.endswith(".txt") and f.startswith(source_id)
            ])

            if not chunk_files:
                return full_content[:15000] + "\n\n[Content truncated...]"

            # Sample up to 12 chunks evenly distributed (more for longer blog posts)
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
            print(f"[BlogAgent] Error getting source content: {e}")
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
            task=f"Generate blog post (job: {job_id[:8]})",
            messages=messages,
            result=result,
            started_at=started_at,
            metadata={"source_id": source_id, "job_id": job_id}
        )


# Singleton instance
blog_agent_service = BlogAgentService()
