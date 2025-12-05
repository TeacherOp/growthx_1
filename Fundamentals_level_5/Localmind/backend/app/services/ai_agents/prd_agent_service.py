"""
PRD Agent Service - AI agent for generating Product Requirements Documents.

Educational Note: Agentic loop pattern for document generation:
1. Agent plans the PRD structure (plan_prd tool)
2. Agent writes sections incrementally (write_prd_section tool - can be called multiple times)
3. Agent signals completion via is_last_section=true flag

The markdown output can be rendered on frontend and exported to PDF.
"""

import os
import uuid
from typing import Dict, Any, List
from datetime import datetime

from app.services.integrations.claude import claude_service
from app.config import prompt_loader, tool_loader
from app.utils import claude_parsing_utils
from app.utils.path_utils import get_studio_dir, get_sources_dir
from app.services.data_services import message_service
from app.services.studio_services import studio_index_service


class PRDAgentService:
    """
    PRD generation agent with multi-step document writing workflow.

    Educational Note: This agent demonstrates how AI can create structured
    documents incrementally: planning -> writing sections -> completion.
    """

    AGENT_NAME = "prd_agent"
    MAX_ITERATIONS = 10  # Brief PRDs: 1 plan + ~5 sections

    def __init__(self):
        """Initialize agent with lazy-loaded config and tools."""
        self._prompt_config = None
        self._tools = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("prd_agent")
        return self._prompt_config

    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load all agent tools."""
        if self._tools is None:
            self._tools = tool_loader.load_tools_for_agent(self.AGENT_NAME)
        return self._tools

    # =========================================================================
    # Main Agent Execution
    # =========================================================================

    def generate_prd(
        self,
        project_id: str,
        source_id: str,
        job_id: str,
        direction: str = ""
    ) -> Dict[str, Any]:
        """
        Run the agent to generate a PRD document.

        Educational Note: The agent workflow:
        1. Get source content and direction
        2. Agent plans the document (sections, structure)
        3. Agent writes sections incrementally to markdown file
        4. Agent signals completion with is_last_section=true
        5. We finalize and update job status
        """
        config = self._load_config()
        tools = self._load_tools()

        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Update job status
        studio_index_service.update_prd_job(
            project_id, job_id,
            status="processing",
            status_message="Starting PRD generation...",
            started_at=started_at
        )

        # Get source content
        source_content = self._get_source_content(project_id, source_id)

        # Build initial user message
        user_message = f"""Create a comprehensive Product Requirements Document (PRD) based on the following source content.

=== SOURCE CONTENT ===
{source_content}
=== END SOURCE CONTENT ===

Direction from user: {direction if direction else 'No specific direction provided - create a complete PRD covering all relevant aspects of the product/feature.'}

Please create a complete PRD following the workflow:
1. First, plan the document structure using the plan_prd tool
2. Then write each section one at a time using the write_prd_section tool
3. Set is_last_section=true when you write the final section"""

        messages = [{"role": "user", "content": user_message}]

        total_input_tokens = 0
        total_output_tokens = 0
        sections_written = 0
        markdown_file_path = None

        print(f"[PRDAgent] Starting (job_id: {job_id[:8]})")

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

                    # Tool 1: Plan the PRD
                    if tool_name == "plan_prd":
                        result = self._handle_plan_prd(project_id, job_id, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 2: Write PRD section (also handles termination)
                    elif tool_name == "write_prd_section":
                        result, is_complete, file_path = self._handle_write_section(
                            project_id, job_id, tool_input, sections_written
                        )
                        sections_written += 1
                        if file_path:
                            markdown_file_path = file_path

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                        # Check if this was the last section (TERMINATION)
                        if is_complete:
                            final_result = self._finalize_prd(
                                project_id, job_id, source_id, markdown_file_path,
                                sections_written, iteration, total_input_tokens, total_output_tokens
                            )

                            print(f"  Completed in {iteration} iterations, {sections_written} sections")

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
            "sections_written": sections_written,
            "usage": {"input_tokens": total_input_tokens, "output_tokens": total_output_tokens}
        }

        studio_index_service.update_prd_job(
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

    def _handle_plan_prd(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle plan_prd tool call."""
        document_title = tool_input.get("document_title", "Product Requirements Document")
        product_name = tool_input.get("product_name", "Unknown Product")
        sections = tool_input.get("sections", [])

        print(f"      Planning: {document_title} ({len(sections)} sections)")

        # Update job with plan
        studio_index_service.update_prd_job(
            project_id, job_id,
            document_title=document_title,
            product_name=product_name,
            target_audience=tool_input.get("target_audience"),
            planned_sections=sections,
            planning_notes=tool_input.get("planning_notes"),
            total_sections=len(sections),
            status_message=f"Planned {len(sections)} sections, starting to write..."
        )

        return f"PRD plan saved successfully. Document: '{document_title}', Product: '{product_name}', Sections planned: {len(sections)}. Now proceed to write each section using the write_prd_section tool."

    def _handle_write_section(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any],
        current_sections_written: int
    ) -> tuple:
        """
        Handle write_prd_section tool call.

        Educational Note: We use our own counter (current_sections_written + 1)
        instead of trusting the LLM's section_number. This prevents duplicate
        sections if the LLM sends the same section_number repeatedly.

        Returns:
            tuple: (result_message, is_complete, file_path)
        """
        # Use our own counter - don't trust LLM's section_number to avoid duplicates
        actual_section_number = current_sections_written + 1
        agent_section_number = tool_input.get("section_number", actual_section_number)

        operation = tool_input.get("operation", "append")
        is_last_section = tool_input.get("is_last_section", False)
        section_title = tool_input.get("section_title", "")
        markdown_content = tool_input.get("markdown_content", "")

        # Log if there's a mismatch (for debugging)
        if agent_section_number != actual_section_number:
            print(f"      Note: Agent sent section {agent_section_number}, using actual count {actual_section_number}")

        print(f"      Writing section {actual_section_number}: {section_title} (is_last: {is_last_section})")

        try:
            # Prepare output directory
            studio_dir = get_studio_dir(project_id)
            prd_dir = os.path.join(studio_dir, "prds")
            os.makedirs(prd_dir, exist_ok=True)

            # File path
            markdown_filename = f"{job_id}.md"
            file_path = os.path.join(prd_dir, markdown_filename)

            # Get job info for document title and total sections
            job = studio_index_service.get_prd_job(project_id, job_id)
            document_title = job.get("document_title", "Product Requirements Document") if job else "Product Requirements Document"
            total_sections = job.get("total_sections", 0) if job else 0

            # Write or append content
            if operation == "write":
                # First section - create file with title
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# {document_title}\n\n")
                    f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
                    f.write("---\n\n")
                    f.write(markdown_content)
                    f.write("\n\n")
            else:
                # Subsequent sections - append
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(markdown_content)
                    f.write("\n\n")

            studio_index_service.update_prd_job(
                project_id, job_id,
                sections_written=actual_section_number,
                current_section=section_title,
                markdown_file=markdown_filename,
                status_message=f"Writing section {actual_section_number}/{total_sections}: {section_title}..."
            )

            # Provide clear feedback to help Claude know what to do next
            result_msg = f"Section {actual_section_number} '{section_title}' written successfully."
            if is_last_section:
                result_msg += " PRD document is now complete."
            elif total_sections > 0:
                remaining = total_sections - actual_section_number
                result_msg += f" Progress: {actual_section_number}/{total_sections} sections complete. {remaining} section(s) remaining."

            return result_msg, is_last_section, file_path

        except Exception as e:
            error_msg = f"Error writing section {actual_section_number}: {str(e)}"
            print(f"      {error_msg}")
            return error_msg, False, None

    def _finalize_prd(
        self,
        project_id: str,
        job_id: str,
        source_id: str,
        file_path: str,
        sections_written: int,
        iterations: int,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """Finalize the PRD document and update job status."""
        try:
            # Get job info
            job = studio_index_service.get_prd_job(project_id, job_id)
            document_title = job.get("document_title", "PRD") if job else "PRD"
            markdown_filename = f"{job_id}.md"

            # Update job to ready
            studio_index_service.update_prd_job(
                project_id, job_id,
                status="ready",
                status_message="PRD generated successfully!",
                markdown_file=markdown_filename,
                markdown_filename=markdown_filename,
                preview_url=f"/api/v1/projects/{project_id}/studio/prds/{job_id}/preview",
                download_url=f"/api/v1/projects/{project_id}/studio/prds/{job_id}/download",
                iterations=iterations,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completed_at=datetime.now().isoformat()
            )

            return {
                "success": True,
                "job_id": job_id,
                "document_title": document_title,
                "markdown_file": markdown_filename,
                "preview_url": f"/api/v1/projects/{project_id}/studio/prds/{job_id}/preview",
                "download_url": f"/api/v1/projects/{project_id}/studio/prds/{job_id}/download",
                "sections_written": sections_written,
                "iterations": iterations,
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }

        except Exception as e:
            error_msg = f"Error finalizing PRD: {str(e)}"
            print(f"      {error_msg}")

            studio_index_service.update_prd_job(
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
        Get source content for PRD generation.

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
            if len(full_content) < 15000:  # ~3750 tokens
                return full_content

            # For large sources, sample chunks
            chunks_dir = os.path.join(sources_dir, "chunks", source_id)
            if not os.path.exists(chunks_dir):
                return full_content[:15000] + "\n\n[Content truncated...]"

            # Get all chunks
            chunk_files = sorted([
                f for f in os.listdir(chunks_dir)
                if f.endswith(".txt") and f.startswith(source_id)
            ])

            if not chunk_files:
                return full_content[:15000] + "\n\n[Content truncated...]"

            # Sample up to 10 chunks evenly distributed
            max_chunks = 10
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
            print(f"[PRDAgent] Error getting source content: {e}")
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
            task=f"Generate PRD (job: {job_id[:8]})",
            messages=messages,
            result=result,
            started_at=started_at,
            metadata={"source_id": source_id, "job_id": job_id}
        )


# Singleton instance
prd_agent_service = PRDAgentService()
