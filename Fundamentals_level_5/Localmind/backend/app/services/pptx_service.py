"""
PPTX Service - Manages PowerPoint presentation processing using LibreOffice and Claude vision.

Educational Note: This service processes PPTX files in three stages:
1. Convert PPTX to PDF using LibreOffice headless mode
2. Extract PDF pages as base64 (reusing existing pdf_utils)
3. Send to Claude vision for slide analysis

The conversion approach allows us to leverage the existing PDF infrastructure
while providing presentation-specific prompts that understand slides, not documents.

Why LibreOffice?
- Free, open-source, cross-platform (macOS, Windows, Linux)
- Headless mode allows server-side conversion without GUI
- Accurate rendering of PowerPoint presentations

Processing Flow:
    PPTX → PDF (LibreOffice) → base64 pages → Claude vision → extracted content
"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import platform

from app.services.claude_service import claude_service
from app.services.task_service import task_service
from app.services.tool_loader import tool_loader
from app.services.message_service import message_service
from app.utils.encoding import encode_bytes_to_base64
from app.utils.pdf_utils import get_page_count, extract_single_page_bytes
from app.utils.tier_config import get_anthropic_config
from config import Config


# Maximum slides per batch - same as PDF for consistency
MAX_SLIDES_PER_BATCH = 5


class CancelledException(Exception):
    """Raised when processing is cancelled by user."""
    pass


class PPTXService:
    """
    Service class for processing PowerPoint presentations.

    Educational Note: This service orchestrates PPTX processing:
    1. Converts PPTX to PDF using LibreOffice headless
    2. Splits PDF into batches of slides (max 5 per batch)
    3. Sends each batch to Claude API for visual analysis
    4. Claude uses submit_slide_extraction tool for each slide
    5. Collects results, writes to file in slide order
    """

    def __init__(self):
        """Initialize the PPTX service."""
        self.projects_dir = Config.PROJECTS_DIR
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self._prompt_config = None
        self._tool_definition = None
        # Rate limiting state
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0.0
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

    def _get_libreoffice_path(self) -> str:
        """
        Get the LibreOffice executable path based on OS.

        Educational Note: LibreOffice is installed in different locations
        on different operating systems. We detect the OS and return the
        appropriate path.

        Returns:
            Path to LibreOffice executable

        Raises:
            FileNotFoundError: If LibreOffice is not found
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        elif system == "Windows":
            # Common Windows installation paths
            possible_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            path = None
            for p in possible_paths:
                if os.path.exists(p):
                    path = p
                    break
            if not path:
                raise FileNotFoundError(
                    "LibreOffice not found. Please install from https://www.libreoffice.org/download/"
                )
        else:  # Linux
            path = "libreoffice"  # Usually in PATH on Linux

        # Verify it exists (for macOS)
        if system == "Darwin" and not os.path.exists(path):
            raise FileNotFoundError(
                f"LibreOffice not found at {path}. Please install: brew install --cask libreoffice"
            )

        return path

    def _convert_pptx_to_pdf(self, pptx_path: Path, output_dir: Path) -> Path:
        """
        Convert PPTX to PDF using LibreOffice headless mode.

        Educational Note: LibreOffice's headless mode allows conversion
        without launching a GUI. The --convert-to flag specifies the
        output format, and --outdir specifies where to save it.

        Args:
            pptx_path: Path to the PPTX file
            output_dir: Directory to save the PDF

        Returns:
            Path to the generated PDF file

        Raises:
            RuntimeError: If conversion fails
        """
        libreoffice_path = self._get_libreoffice_path()

        # Build the conversion command
        cmd = [
            libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(pptx_path)
        ]

        print(f"Converting PPTX to PDF: {pptx_path.name}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for large presentations
            )

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # The output PDF will have the same name as input but with .pdf extension
            pdf_name = pptx_path.stem + ".pdf"
            pdf_path = output_dir / pdf_name

            if not pdf_path.exists():
                raise RuntimeError(f"PDF not created at expected path: {pdf_path}")

            print(f"PDF created: {pdf_path}")
            return pdf_path

        except subprocess.TimeoutExpired:
            raise RuntimeError("LibreOffice conversion timed out (>2 minutes)")
        except FileNotFoundError:
            raise RuntimeError(
                "LibreOffice not found. Please install it:\n"
                "  macOS: brew install --cask libreoffice\n"
                "  Windows: Download from libreoffice.org\n"
                "  Linux: sudo apt install libreoffice"
            )

    def _get_tier_config(self) -> Dict[str, Any]:
        """Get tier configuration from centralized tier_config utility."""
        return get_anthropic_config()

    def _rate_limit(self, requests_per_minute: int) -> None:
        """
        Rate limit API calls to stay within tier limits.

        Args:
            requests_per_minute: Maximum API calls allowed per minute
        """
        with self._rate_limit_lock:
            current_time = time.time()

            # Reset counter if we're in a new minute
            if current_time - self._minute_start_time >= 60:
                self._requests_this_minute = 0
                self._minute_start_time = current_time

            # If we've hit the limit, wait until the next minute
            if self._requests_this_minute >= requests_per_minute:
                sleep_time = 60 - (current_time - self._minute_start_time)
                if sleep_time > 0:
                    print(f"Rate limit reached, waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                self._requests_this_minute = 0
                self._minute_start_time = time.time()

            self._requests_this_minute += 1

    def _load_prompt_config(self) -> Dict[str, Any]:
        """Load the PPTX extraction prompt configuration."""
        if self._prompt_config is None:
            prompt_path = self.prompts_dir / "pptx_extraction_prompt.json"
            with open(prompt_path, 'r') as f:
                self._prompt_config = json.load(f)
        return self._prompt_config

    def _load_tool_definition(self) -> Dict[str, Any]:
        """Load the slide extraction tool definition."""
        if self._tool_definition is None:
            self._tool_definition = tool_loader.load_tool("pptx_tools", "pptx_extraction")
        return self._tool_definition

    def extract_content_from_pptx(
        self,
        project_id: str,
        source_id: str,
        pptx_path: Path
    ) -> Dict[str, Any]:
        """
        Extract content from a PPTX file.

        Educational Note: This is the main entry point for PPTX processing.
        It orchestrates the full pipeline:
        1. Convert PPTX to PDF
        2. Extract slides in batches
        3. Process with Claude vision
        4. Save extracted content

        Args:
            project_id: The project UUID
            source_id: The source UUID
            pptx_path: Path to the PPTX file

        Returns:
            Dict with success status, extracted content info, and any errors
        """
        # Create a temporary directory for the PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Step 1: Convert PPTX to PDF
                pdf_path = self._convert_pptx_to_pdf(pptx_path, temp_path)

                # Step 2: Get slide count
                total_slides = get_page_count(pdf_path)
                print(f"Presentation has {total_slides} slides")

                if total_slides == 0:
                    return {
                        "success": False,
                        "error": "Presentation has no slides"
                    }

                # Step 3: Load prompt and tool configurations
                prompt_config = self._load_prompt_config()
                tool_def = self._load_tool_definition()

                # Step 4: Get tier configuration
                tier_config = self._get_tier_config()
                max_workers = tier_config["max_workers"]
                requests_per_minute = tier_config["pages_per_minute"]

                # Step 5: Create batches of slides
                batches = self._create_batches(pdf_path, total_slides)
                print(f"Created {len(batches)} batches for processing")

                # Step 6: Process batches (parallel for large presentations)
                all_results = {}
                total_tokens = {"input_tokens": 0, "output_tokens": 0}

                if len(batches) == 1:
                    # Single batch - process directly
                    _, result = self._process_batch(
                        batch=batches[0],
                        total_slides=total_slides,
                        pptx_name=pptx_path.name,
                        prompt_config=prompt_config,
                        tool_def=tool_def,
                        requests_per_minute=requests_per_minute,
                        source_id=source_id,
                        project_id=project_id
                    )
                    if result.get("success"):
                        all_results.update(result["slide_results"])
                        total_tokens["input_tokens"] += result["token_usage"].get("input_tokens", 0)
                        total_tokens["output_tokens"] += result["token_usage"].get("output_tokens", 0)
                    else:
                        return {"success": False, "error": result.get("error", "Unknown error")}
                else:
                    # Multiple batches - process in parallel
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(
                                self._process_batch,
                                batch=batch,
                                total_slides=total_slides,
                                pptx_name=pptx_path.name,
                                prompt_config=prompt_config,
                                tool_def=tool_def,
                                requests_per_minute=requests_per_minute,
                                source_id=source_id,
                                project_id=project_id
                            ): batch[0][0]
                            for batch in batches
                        }

                        for future in as_completed(futures):
                            batch_start = futures[future]
                            try:
                                _, result = future.result()
                                if result.get("success"):
                                    all_results.update(result["slide_results"])
                                    total_tokens["input_tokens"] += result["token_usage"].get("input_tokens", 0)
                                    total_tokens["output_tokens"] += result["token_usage"].get("output_tokens", 0)
                                else:
                                    return {"success": False, "error": result.get("error")}
                            except CancelledException:
                                return {"success": False, "status": "cancelled", "error": "Processing cancelled"}
                            except Exception as e:
                                return {"success": False, "error": f"Batch {batch_start} failed: {str(e)}"}

                # Step 7: Build and save the output file
                output_content = self._build_output_content(
                    all_results, total_slides, pptx_path.name
                )

                # Save to processed directory
                processed_dir = self.projects_dir / project_id / "sources" / "processed"
                processed_dir.mkdir(parents=True, exist_ok=True)
                output_path = processed_dir / f"{source_id}.txt"

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)

                print(f"Saved extracted content to: {output_path}")

                return {
                    "success": True,
                    "total_slides": total_slides,
                    "slides_processed": len(all_results),
                    "character_count": len(output_content),
                    "token_usage": total_tokens,
                    "model_used": prompt_config.get("model"),
                    "extracted_at": datetime.now().isoformat()
                }

            except Exception as e:
                print(f"Error processing PPTX: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

    def _create_batches(self, pdf_path: Path, total_slides: int) -> List[List[Tuple[int, bytes]]]:
        """
        Create batches of slides for processing.

        Args:
            pdf_path: Path to the converted PDF
            total_slides: Total number of slides

        Returns:
            List of batches, each batch is a list of (slide_number, slide_bytes) tuples
        """
        batches = []
        current_batch = []

        for slide_num in range(1, total_slides + 1):
            slide_bytes = extract_single_page_bytes(pdf_path, slide_num)
            current_batch.append((slide_num, slide_bytes))

            if len(current_batch) >= MAX_SLIDES_PER_BATCH:
                batches.append(current_batch)
                current_batch = []

        # Add remaining slides
        if current_batch:
            batches.append(current_batch)

        return batches

    def _process_batch(
        self,
        batch: List[Tuple[int, bytes]],
        total_slides: int,
        pptx_name: str,
        prompt_config: Dict[str, Any],
        tool_def: Dict[str, Any],
        requests_per_minute: int,
        source_id: str,
        project_id: str,
        max_retries: int = 3
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Process a batch of slides with Claude vision.

        Args:
            batch: List of (slide_number, slide_bytes) tuples
            total_slides: Total slides in presentation
            pptx_name: Original PPTX filename
            prompt_config: Prompt configuration
            tool_def: Tool definition
            requests_per_minute: Rate limit
            source_id: Source UUID for cancellation check
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (first_slide_in_batch, results_dict)
        """
        # Check for cancellation
        if task_service.is_cancelled(source_id):
            raise CancelledException("Processing cancelled by user")

        batch_start_slide = batch[0][0]
        batch_slide_numbers = [s[0] for s in batch]

        model = prompt_config.get("model", "claude-haiku-4-5-20251001")
        system_prompt = prompt_config.get("system_prompt", "")
        user_message_template = prompt_config.get("user_message", "")
        max_tokens = prompt_config.get("max_tokens", 16000)
        temperature = prompt_config.get("temperature", 0)

        # Build content blocks: one document block per slide
        content_blocks = []
        for slide_num, slide_bytes in batch:
            slide_base64 = encode_bytes_to_base64(slide_bytes)
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": slide_base64
                },
                "title": f"{pptx_name} - Slide {slide_num}",
            })

        # Build user message
        if len(batch) == 1:
            extraction_desc = f"slide {batch[0][0]}"
        else:
            extraction_desc = f"slides {batch[0][0]} to {batch[-1][0]}"

        slide_list = ", ".join(str(s) for s in batch_slide_numbers)

        user_message = user_message_template.format(
            total_pages=total_slides,
            extraction_description=extraction_desc,
            expected_tool_calls=len(batch),
            page_numbers=slide_list
        )

        content_blocks.append({
            "type": "text",
            "text": user_message
        })

        messages = [{"role": "user", "content": content_blocks}]

        # Retry loop
        last_error = None
        for attempt in range(max_retries):
            try:
                self._rate_limit(requests_per_minute)

                response = claude_service.send_message(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=[tool_def],
                    tool_choice={"type": "tool", "name": "submit_slide_extraction"},
                    project_id=project_id
                )

                slide_results = self._parse_tool_calls(response, batch_slide_numbers)

                return (batch_start_slide, {
                    "success": True,
                    "slide_results": slide_results,
                    "token_usage": response["usage"],
                    "model": response["model"]
                })

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                if "rate" in error_str or "429" in error_str or "overloaded" in error_str:
                    wait_time = (attempt + 1) * 30
                    print(f"Batch starting slide {batch_start_slide}: Rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    print(f"Batch starting slide {batch_start_slide}: Error - {e}")
                    if attempt < max_retries - 1:
                        time.sleep(5)

        return (batch_start_slide, {
            "success": False,
            "error": str(last_error)
        })

    def _parse_tool_calls(
        self,
        response: Dict[str, Any],
        expected_slide_numbers: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Parse tool calls from Claude response.

        Args:
            response: Claude API response
            expected_slide_numbers: List of slide numbers we expect

        Returns:
            Dict mapping slide_number to extraction results
        """
        results = {}
        tool_calls = message_service.parse_tool_calls(response)

        for tool_call in tool_calls:
            if tool_call.get("name") == "submit_slide_extraction":
                input_data = tool_call.get("input", {})
                slide_num = input_data.get("slide_number")

                if slide_num in expected_slide_numbers:
                    results[slide_num] = {
                        "slide_title": input_data.get("slide_title", "[NO TITLE]"),
                        "text_content": input_data.get("text_content", "[NO TEXT CONTENT]"),
                        "visual_elements": input_data.get("visual_elements", "[NO VISUAL ELEMENTS]"),
                        "layout_notes": input_data.get("layout_notes", ""),
                        "continues_from_previous": input_data.get("continues_from_previous", False),
                        "continues_to_next": input_data.get("continues_to_next", False)
                    }

        return results

    def _build_output_content(
        self,
        all_results: Dict[int, Dict[str, Any]],
        total_slides: int,
        pptx_name: str
    ) -> str:
        """
        Build the final output content with slide markers.

        Args:
            all_results: Dict mapping slide numbers to extraction results
            total_slides: Total slides in presentation
            pptx_name: Original PPTX filename

        Returns:
            Formatted string with PPTX PAGE markers
        """
        lines = [
            f"# Extracted from presentation: {pptx_name}",
            f"# Total slides: {total_slides}",
            f"# Processed at: {datetime.now().isoformat()}",
            ""
        ]

        for slide_num in sorted(all_results.keys()):
            result = all_results[slide_num]

            # Build continuation markers for the header
            continuation_info = ""
            if result.get("continues_from_previous"):
                continuation_info = " (continues from previous)"

            lines.append(f"=== PPTX PAGE {slide_num} of {total_slides}{continuation_info} ===")
            lines.append("")

            # Slide title
            title = result.get("slide_title", "[NO TITLE]")
            if title and title != "[NO TITLE]":
                lines.append(f"# {title}")
                lines.append("")

            # Text content
            text_content = result.get("text_content", "")
            if text_content and text_content != "[NO TEXT CONTENT]":
                lines.append("## Content")
                lines.append(text_content)
                lines.append("")

            # Visual elements
            visual_elements = result.get("visual_elements", "")
            if visual_elements and visual_elements != "[NO VISUAL ELEMENTS]":
                lines.append("## Visual Elements")
                lines.append(visual_elements)
                lines.append("")

            # Layout notes (optional, only if meaningful)
            layout_notes = result.get("layout_notes", "")
            if layout_notes and len(layout_notes) > 10:
                lines.append("## Layout")
                lines.append(layout_notes)
                lines.append("")

            lines.append("")

        return "\n".join(lines)


# Singleton instance
pptx_service = PPTXService()
