"""
Business Report Agent Service - AI agent for generating data-driven business reports.

Educational Note: Multi-agent orchestration pattern for comprehensive reports:
1. This agent plans the report structure (plan_business_report)
2. Calls csv_analyzer_agent internally for each data analysis need (analyze_csv_data)
3. Searches non-CSV sources for context (search_source_content)
4. Writes the final markdown report (write_business_report - termination tool)

Key Pattern: Agent-to-agent communication where business_report_agent
orchestrates csv_analyzer_agent for data analysis and chart generation.

Tools:
- plan_business_report: Client tool - plan structure and identify data needs
- analyze_csv_data: Client tool - wrapper that calls csv_analyzer_agent
- search_source_content: Client tool - search non-CSV sources for context
- write_business_report: Termination tool - write final markdown report
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
from app.services.ai_agents.csv_analyzer_agent import csv_analyzer_agent


class BusinessReportAgentService:
    """
    Business report generation agent with multi-agent orchestration.

    Educational Note: This agent demonstrates how to orchestrate another agent
    (csv_analyzer_agent) to perform specialized tasks (data analysis with charts)
    while maintaining control over the overall workflow.
    """

    AGENT_NAME = "business_report_agent"
    MAX_ITERATIONS = 10  # Reduced for simpler, concise reports

    def __init__(self):
        """Initialize agent with lazy-loaded config and tools."""
        self._prompt_config = None
        self._tools = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("business_report_agent")
        return self._prompt_config

    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load all 4 agent tools."""
        if self._tools is None:
            self._tools = tool_loader.load_tools_for_agent(self.AGENT_NAME)
        return self._tools

    # =========================================================================
    # Main Agent Execution
    # =========================================================================

    def generate_business_report(
        self,
        project_id: str,
        source_id: str,
        job_id: str,
        direction: str = "",
        report_type: str = "executive_summary",
        csv_source_ids: List[str] = None,
        context_source_ids: List[str] = None,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run the agent to generate a comprehensive business report.

        Educational Note: The agent workflow:
        1. Agent plans report structure and identifies data needs
        2. Agent calls analyze_csv_data for each analysis (we call csv_analyzer_agent)
        3. Agent optionally searches context sources for supporting info
        4. Agent writes the complete markdown report with embedded charts
        5. We save everything and update job status
        """
        config = self._load_config()
        tools = self._load_tools()

        csv_source_ids = csv_source_ids or []
        context_source_ids = context_source_ids or []
        focus_areas = focus_areas or []

        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Update job status
        studio_index_service.update_business_report_job(
            project_id, job_id,
            status="processing",
            status_message="Starting business report generation...",
            started_at=started_at
        )

        # Get source information for the prompt
        source_info = self._get_source_info(project_id, csv_source_ids, context_source_ids)

        # Map report_type to human-readable format
        report_type_display = self._get_report_type_display(report_type)

        # Build initial user message
        user_message = self._build_user_message(
            source_info, report_type_display, direction, focus_areas
        )

        messages = [{"role": "user", "content": user_message}]

        total_input_tokens = 0
        total_output_tokens = 0
        collected_charts = []  # Track all charts from analyses
        collected_analyses = []  # Track all analysis results

        print(f"[BusinessReportAgent] Starting (job_id: {job_id[:8]}, type: {report_type})")
        print(f"  CSV sources: {len(csv_source_ids)}, Context sources: {len(context_source_ids)}")

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

                    # Tool 1: Plan the report
                    if tool_name == "plan_business_report":
                        result = self._handle_plan_report(project_id, job_id, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 2: Analyze CSV data (calls csv_analyzer_agent)
                    elif tool_name == "analyze_csv_data":
                        result = self._handle_analyze_csv(
                            project_id, job_id, tool_input,
                            collected_charts, collected_analyses
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 3: Search source content
                    elif tool_name == "search_source_content":
                        result = self._handle_search_content(
                            project_id, job_id, tool_input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    # Tool 4: Write business report (TERMINATION)
                    elif tool_name == "write_business_report":
                        final_result = self._handle_write_report(
                            project_id, job_id, source_id, tool_input,
                            collected_charts, collected_analyses,
                            iteration, total_input_tokens, total_output_tokens,
                            report_type
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

        studio_index_service.update_business_report_job(
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

    def _handle_plan_report(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle plan_business_report tool call."""
        title = tool_input.get("title", "Business Report")
        print(f"      Planning: {title[:50]}...")

        # Update job with plan
        studio_index_service.update_business_report_job(
            project_id, job_id,
            title=title,
            sections=tool_input.get("sections", []),
            status_message="Report planned, analyzing data..."
        )

        num_sections = len(tool_input.get("sections", []))

        return f"Report plan saved. Title: '{title}', Sections: {num_sections}. Proceed to analyze data and write the report."

    def _handle_analyze_csv(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any],
        collected_charts: List[Dict[str, str]],
        collected_analyses: List[Dict[str, Any]]
    ) -> str:
        """
        Handle analyze_csv_data tool call.

        Educational Note: This is where we call csv_analyzer_agent internally.
        The csv_analyzer_agent runs its own agentic loop with run_analysis tool
        and returns summary + chart paths.
        """
        csv_source_id = tool_input.get("csv_source_id", "")
        analysis_query = tool_input.get("analysis_query", "")
        section_context = tool_input.get("section_context", "")

        print(f"      Analyzing CSV {csv_source_id[:8]}... for: {section_context or 'general'}")

        # Update status
        studio_index_service.update_business_report_job(
            project_id, job_id,
            status_message=f"Analyzing data for {section_context or 'report'}..."
        )

        try:
            # Call csv_analyzer_agent directly
            result = csv_analyzer_agent.run(
                project_id=project_id,
                source_id=csv_source_id,
                query=analysis_query
            )

            if not result.get("success"):
                error_msg = result.get("error", "Analysis failed")
                return f"Error analyzing data: {error_msg}"

            # Extract results
            summary = result.get("summary", "No summary available")
            chart_paths = result.get("image_paths", [])

            # Track analysis
            analysis_info = {
                "query": analysis_query,
                "summary": summary,
                "chart_paths": chart_paths,
                "section_context": section_context
            }
            collected_analyses.append(analysis_info)

            # Track charts with metadata
            for chart_path in chart_paths:
                chart_info = {
                    "filename": chart_path,
                    "title": f"Chart for {section_context}" if section_context else "Data Chart",
                    "section": section_context,
                    "url": f"/api/v1/projects/{project_id}/ai-images/{chart_path}"
                }
                collected_charts.append(chart_info)

            # Update job with analyses
            studio_index_service.update_business_report_job(
                project_id, job_id,
                analyses=collected_analyses,
                charts=collected_charts
            )

            # Build response for Claude
            response_parts = [f"Analysis complete for: {section_context or 'data analysis'}"]
            response_parts.append(f"\nSummary: {summary}")

            if chart_paths:
                response_parts.append(f"\nGenerated {len(chart_paths)} chart(s):")
                for chart_path in chart_paths:
                    response_parts.append(f"  - {chart_path}")
                response_parts.append("\nUse these exact filenames in your markdown: ![Description](filename.png)")

            print(f"      Charts generated: {len(chart_paths)}")

            return "\n".join(response_parts)

        except Exception as e:
            error_msg = f"Error during CSV analysis: {str(e)}"
            print(f"      {error_msg}")
            return error_msg

    def _handle_search_content(
        self,
        project_id: str,
        job_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """
        Handle search_source_content tool call.

        Educational Note: This searches non-CSV sources for context.
        Uses a simple approach - reads source content and returns relevant excerpts.
        """
        source_id = tool_input.get("source_id", "")
        search_query = tool_input.get("search_query", "")
        section_context = tool_input.get("section_context", "")

        print(f"      Searching source {source_id[:8]}... for: {search_query[:30]}")

        try:
            # Get processed source content
            sources_dir = get_sources_dir(project_id)
            processed_path = os.path.join(sources_dir, "processed", f"{source_id}.txt")

            if not os.path.exists(processed_path):
                return f"Source content not found for {source_id}"

            with open(processed_path, "r", encoding="utf-8") as f:
                content = f.read()

            # For now, return a sample of the content
            # In a more sophisticated version, we could use embeddings/search
            max_length = 3000
            if len(content) > max_length:
                # Return first part with truncation note
                content = content[:max_length] + "\n\n[Content truncated for context...]"

            return f"Content from source (for {section_context or 'context'}):\n\n{content}"

        except Exception as e:
            error_msg = f"Error searching source content: {str(e)}"
            print(f"      {error_msg}")
            return error_msg

    def _handle_write_report(
        self,
        project_id: str,
        job_id: str,
        source_id: str,
        tool_input: Dict[str, Any],
        collected_charts: List[Dict[str, str]],
        collected_analyses: List[Dict[str, Any]],
        iterations: int,
        input_tokens: int,
        output_tokens: int,
        report_type: str
    ) -> Dict[str, Any]:
        """Handle write_business_report tool call (termination)."""
        markdown_content = tool_input.get("markdown_content", "")
        charts_included = tool_input.get("charts_included", [])

        # Estimate word count from content
        word_count = len(markdown_content.split()) if markdown_content else 0

        print(f"      Writing markdown ({len(markdown_content)} chars, ~{word_count} words)")

        try:
            # Replace chart filenames with full URLs
            final_markdown = markdown_content
            for chart_info in collected_charts:
                filename = chart_info["filename"]
                url = chart_info["url"]
                # Handle markdown image syntax: ![alt](filename)
                final_markdown = final_markdown.replace(f"({filename})", f"({url})")

            # Save markdown file
            studio_dir = get_studio_dir(project_id)
            reports_dir = os.path.join(studio_dir, "business_reports")
            os.makedirs(reports_dir, exist_ok=True)

            markdown_filename = f"{job_id}.md"
            markdown_path = os.path.join(reports_dir, markdown_filename)

            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(final_markdown)

            print(f"      Saved: {markdown_filename}")

            # Get job info for title
            job = studio_index_service.get_business_report_job(project_id, job_id)
            title = job.get("title", "Business Report")

            # Update job to ready
            studio_index_service.update_business_report_job(
                project_id, job_id,
                status="ready",
                status_message="Business report generated successfully!",
                markdown_file=markdown_filename,
                markdown_url=f"/api/v1/projects/{project_id}/studio/business-reports/{markdown_filename}",
                preview_url=f"/api/v1/projects/{project_id}/studio/business-reports/{job_id}/preview",
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
                "markdown_url": f"/api/v1/projects/{project_id}/studio/business-reports/{markdown_filename}",
                "preview_url": f"/api/v1/projects/{project_id}/studio/business-reports/{job_id}/preview",
                "charts": collected_charts,
                "analyses_count": len(collected_analyses),
                "word_count": word_count,
                "report_type": report_type,
                "iterations": iterations,
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }

        except Exception as e:
            error_msg = f"Error saving business report: {str(e)}"
            print(f"      {error_msg}")

            studio_index_service.update_business_report_job(
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

    def _get_report_type_display(self, report_type: str) -> str:
        """Convert report_type slug to human-readable format."""
        type_map = {
            "executive_summary": "Executive Summary",
            "financial_report": "Financial Report",
            "performance_analysis": "Performance Analysis",
            "market_research": "Market Research Report",
            "operations_report": "Operations Report",
            "sales_report": "Sales Report",
            "quarterly_review": "Quarterly Review",
            "annual_report": "Annual Report"
        }
        return type_map.get(report_type, report_type.replace("_", " ").title())

    def _get_source_info(
        self,
        project_id: str,
        csv_source_ids: List[str],
        context_source_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Get information about available sources.

        Educational Note: We provide source metadata to help the agent
        understand what data is available for analysis.
        """
        try:
            from app.services.source_services import source_service

            csv_sources = []
            for source_id in csv_source_ids:
                source = source_service.get_source(project_id, source_id)
                if source:
                    csv_sources.append({
                        "source_id": source_id,
                        "name": source.get("name", "Unknown"),
                        "type": "csv"
                    })

            context_sources = []
            for source_id in context_source_ids:
                source = source_service.get_source(project_id, source_id)
                if source:
                    context_sources.append({
                        "source_id": source_id,
                        "name": source.get("name", "Unknown"),
                        "type": source.get("file_extension", "unknown")
                    })

            return {
                "csv_sources": csv_sources,
                "context_sources": context_sources
            }

        except Exception as e:
            print(f"[BusinessReportAgent] Error getting source info: {e}")
            return {"csv_sources": [], "context_sources": []}

    def _build_user_message(
        self,
        source_info: Dict[str, Any],
        report_type_display: str,
        direction: str,
        focus_areas: List[str]
    ) -> str:
        """Build the initial user message for the agent."""
        parts = [
            f"Create a concise {report_type_display} (500-1000 words) based on the available data."
        ]

        # Add CSV sources info
        csv_sources = source_info.get("csv_sources", [])
        if csv_sources:
            parts.append("\n\nCSV DATA SOURCES:")
            for src in csv_sources:
                parts.append(f"- {src['name']} (source_id: {src['source_id']})")

        # Add context sources info (only if present)
        context_sources = source_info.get("context_sources", [])
        if context_sources:
            parts.append("\n\nCONTEXT SOURCES (optional):")
            for src in context_sources:
                parts.append(f"- {src['name']} (source_id: {src['source_id']})")

        # Add focus areas
        if focus_areas:
            parts.append("\n\nFOCUS ON: " + ", ".join(focus_areas))

        # Add user direction
        if direction:
            parts.append(f"\n\nNOTE: {direction}")

        parts.append("\n\nWorkflow: plan_business_report -> analyze_csv_data (1-2 times) -> write_business_report")
        parts.append("Keep the report SHORT and focused with only 1-2 charts.")

        return "\n".join(parts)

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
            task=f"Generate business report (job: {job_id[:8]})",
            messages=messages,
            result=result,
            started_at=started_at,
            metadata={"source_id": source_id, "job_id": job_id}
        )


# Singleton instance
business_report_agent_service = BusinessReportAgentService()
