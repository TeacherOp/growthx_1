"""
Wireframe Service - Generates UI/UX wireframes using Excalidraw elements.

Educational Note: This service uses Claude to generate Excalidraw-compatible
element definitions for wireframe creation. The AI generates structured JSON
that describes shapes, text, and layout which the frontend renders using the
Excalidraw React component.

Excalidraw provides:
- Hand-drawn aesthetic perfect for wireframes
- Interactive canvas (users can edit after generation)
- Export to PNG/SVG
- Well-maintained React library
"""
import uuid
from typing import Dict, Any, List
from datetime import datetime

from app.services.integrations.claude import claude_service
from app.services.source_services import source_index_service
from app.services.studio_services import studio_index_service
from app.config import prompt_loader, tool_loader
from app.utils import claude_parsing_utils
from app.utils.path_utils import get_chunks_dir, get_processed_dir


class WireframeService:
    """
    Service for generating UI/UX wireframes from source content.

    Educational Note: Wireframes are generated in a single Claude call
    using the generate_wireframe tool for structured Excalidraw output.
    """

    def __init__(self):
        """Initialize service with lazy-loaded config and tools."""
        self._prompt_config = None
        self._tool = None

    def _load_config(self) -> Dict[str, Any]:
        """Lazy load prompt configuration."""
        if self._prompt_config is None:
            self._prompt_config = prompt_loader.get_prompt_config("wireframe")
        return self._prompt_config

    def _load_tool(self) -> Dict[str, Any]:
        """Load the wireframe tool definition."""
        if self._tool is None:
            self._tool = tool_loader.load_tool("studio_tools", "wireframe_tool")
        return self._tool

    def _get_source_content(
        self,
        project_id: str,
        source_id: str,
        max_tokens: int = 6000
    ) -> str:
        """
        Get source content for wireframe generation.

        Educational Note: For large sources, we sample chunks evenly
        to stay within token limits while covering the full content.
        """
        # Get source metadata
        source = source_index_service.get_source_from_index(project_id, source_id)
        if not source:
            return ""

        token_count = source.get("token_count", 0)

        # For small sources, read the processed file directly
        if token_count < max_tokens:
            processed_dir = get_processed_dir(project_id)
            processed_file = processed_dir / f"{source_id}.txt"
            if processed_file.exists():
                return processed_file.read_text(encoding='utf-8')

        # For large sources, sample chunks evenly
        chunks_dir = get_chunks_dir(project_id, source_id)
        if not chunks_dir.exists():
            return ""

        chunk_files = sorted(chunks_dir.glob("*.txt"))
        if not chunk_files:
            return ""

        # Sample evenly across chunks
        total_chunks = len(chunk_files)
        sample_count = min(15, total_chunks)  # Max 15 chunks for wireframes
        step = max(1, total_chunks // sample_count)

        content_parts = []
        for i in range(0, total_chunks, step):
            if len(content_parts) >= sample_count:
                break
            chunk_content = chunk_files[i].read_text(encoding='utf-8')
            # Skip the metadata header (lines starting with #)
            lines = chunk_content.split('\n')
            content_lines = [line for line in lines if not line.startswith('#')]
            content_parts.append('\n'.join(content_lines).strip())

        return '\n\n---\n\n'.join(content_parts)

    def _convert_to_excalidraw_elements(
        self,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert simplified element format to full Excalidraw element format.

        Educational Note: Excalidraw elements require specific properties.
        We add defaults and generate unique IDs for each element.
        """
        excalidraw_elements = []

        for elem in elements:
            element_id = str(uuid.uuid4())[:8]
            elem_type = elem.get("type", "rectangle")

            # Base element properties
            base = {
                "id": element_id,
                "type": elem_type,
                "x": elem.get("x", 0),
                "y": elem.get("y", 0),
                "strokeColor": elem.get("strokeColor", "#000000"),
                "backgroundColor": elem.get("backgroundColor", "transparent"),
                "fillStyle": elem.get("fillStyle", "hachure"),
                "strokeWidth": elem.get("strokeWidth", 1),
                "roughness": 1,  # Hand-drawn effect
                "opacity": 100,
                "seed": hash(element_id) % 1000000,  # Random seed for roughness
                "version": 1,
                "isDeleted": False,
                "groupIds": [],
                "boundElements": None,
                "locked": False,
            }

            if elem_type == "text":
                # Text element
                text_content = elem.get("text", "Text")
                font_size = elem.get("fontSize", 16)
                base.update({
                    "text": text_content,
                    "fontSize": font_size,
                    "fontFamily": 1,  # Virgil (hand-drawn)
                    "textAlign": "left",
                    "verticalAlign": "top",
                    "baseline": font_size,
                    "width": len(text_content) * font_size * 0.6,
                    "height": font_size * 1.2,
                    "containerId": None,
                    "originalText": text_content,
                })
            elif elem_type in ["line", "arrow"]:
                # Line or arrow
                points = elem.get("points", [[0, 0], [100, 0]])
                base.update({
                    "points": points,
                    "lastCommittedPoint": points[-1] if points else [0, 0],
                    "startBinding": None,
                    "endBinding": None,
                    "startArrowhead": None,
                    "endArrowhead": "arrow" if elem_type == "arrow" else None,
                })
            else:
                # Rectangle, ellipse, diamond
                base.update({
                    "width": elem.get("width", 100),
                    "height": elem.get("height", 50),
                })

            excalidraw_elements.append(base)

            # If element has a label, add it as a separate text element
            label = elem.get("label")
            if label and elem_type in ["rectangle", "ellipse", "diamond"]:
                label_id = str(uuid.uuid4())[:8]
                label_x = elem.get("x", 0) + elem.get("width", 100) / 2 - len(label) * 4
                label_y = elem.get("y", 0) + elem.get("height", 50) / 2 - 8
                label_elem = {
                    "id": label_id,
                    "type": "text",
                    "x": label_x,
                    "y": label_y,
                    "text": label,
                    "fontSize": 14,
                    "fontFamily": 1,
                    "textAlign": "center",
                    "verticalAlign": "middle",
                    "strokeColor": "#666666",
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": 1,
                    "roughness": 1,
                    "opacity": 100,
                    "seed": hash(label_id) % 1000000,
                    "version": 1,
                    "isDeleted": False,
                    "groupIds": [],
                    "boundElements": None,
                    "locked": False,
                    "width": len(label) * 8,
                    "height": 18,
                    "baseline": 14,
                    "containerId": None,
                    "originalText": label,
                }
                excalidraw_elements.append(label_elem)

        return excalidraw_elements

    def generate_wireframe(
        self,
        project_id: str,
        source_id: str,
        job_id: str,
        direction: str = "Create a wireframe for the main page layout."
    ) -> Dict[str, Any]:
        """
        Generate a wireframe for a source.

        Args:
            project_id: The project UUID
            source_id: The source UUID
            job_id: The job ID for status tracking
            direction: User's direction for what to wireframe

        Returns:
            Dict with success status, elements, and metadata
        """
        started_at = datetime.now()

        # Update job to processing
        studio_index_service.update_wireframe_job(
            project_id, job_id,
            status="processing",
            progress="Reading source content...",
            started_at=datetime.now().isoformat()
        )

        print(f"[Wireframe] Starting job {job_id}")

        try:
            # Get source metadata
            source = source_index_service.get_source_from_index(project_id, source_id)
            if not source:
                raise ValueError(f"Source {source_id} not found")

            source_name = source.get("name", "Unknown")

            # Get source content
            studio_index_service.update_wireframe_job(
                project_id, job_id,
                progress="Analyzing content..."
            )

            content = self._get_source_content(project_id, source_id)
            if not content:
                raise ValueError("No content found for source")

            # Load config and tool
            config = self._load_config()
            tool = self._load_tool()

            # Build the user message
            user_message = config["user_message_template"].format(
                direction=direction,
                content=content[:12000]  # Limit content
            )

            # Call Claude with the wireframe tool
            studio_index_service.update_wireframe_job(
                project_id, job_id,
                progress="Generating wireframe..."
            )

            response = claude_service.send_message(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=config["system_prompt"],
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                tools=[tool],
                tool_choice={"type": "tool", "name": "generate_wireframe"},
                project_id=project_id
            )

            # Extract tool use result
            tool_inputs_list = claude_parsing_utils.extract_tool_inputs(
                response, "generate_wireframe"
            )

            if not tool_inputs_list or "elements" not in tool_inputs_list[0]:
                raise ValueError("Failed to generate wireframe - no elements returned")

            tool_inputs = tool_inputs_list[0]
            raw_elements = tool_inputs["elements"]
            title = tool_inputs.get("title", "Wireframe")
            description = tool_inputs.get("description", "")
            canvas_width = tool_inputs.get("canvas_width", 1200)
            canvas_height = tool_inputs.get("canvas_height", 800)

            # Convert to Excalidraw format
            studio_index_service.update_wireframe_job(
                project_id, job_id,
                progress="Formatting wireframe..."
            )

            excalidraw_elements = self._convert_to_excalidraw_elements(raw_elements)

            # Calculate generation time
            generation_time = (datetime.now() - started_at).total_seconds()

            # Update job with results
            studio_index_service.update_wireframe_job(
                project_id, job_id,
                status="ready",
                progress="Complete",
                title=title,
                description=description,
                elements=excalidraw_elements,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
                element_count=len(excalidraw_elements),
                generation_time_seconds=round(generation_time, 1),
                completed_at=datetime.now().isoformat()
            )

            print(f"[Wireframe] Generated {len(excalidraw_elements)} elements in {generation_time:.1f}s")

            return {
                "success": True,
                "title": title,
                "description": description,
                "elements": excalidraw_elements,
                "element_count": len(excalidraw_elements),
                "source_name": source_name,
                "generation_time": generation_time
            }

        except Exception as e:
            print(f"[Wireframe] Error: {e}")
            studio_index_service.update_wireframe_job(
                project_id, job_id,
                status="error",
                error=str(e),
                completed_at=datetime.now().isoformat()
            )
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
wireframe_service = WireframeService()
