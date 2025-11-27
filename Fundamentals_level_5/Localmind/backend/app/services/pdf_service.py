"""
PDF Service - Manages PDF processing and text extraction using tool-based approach.

Educational Note: This service uses a TOOL-BASED extraction approach where:
- Multiple PDF pages are sent to Claude in a single API call (batch)
- Claude sees all pages in the batch for context awareness
- Claude uses the submit_page_extraction tool to return per-page extractions
- This solves the "page boundary" problem (headings on page 1, content on page 2)

Batching Strategy:
- PDFs ≤ 5 pages: Single API call with all pages
- PDFs > 5 pages: Split into batches of 5, process batches in parallel

Why Tools?
- Sending multiple pages and getting a single response loses page boundaries
- Tools let Claude return structured per-page data while having full context
- We force tool use with tool_choice={"type": "any"}

Parallel Processing:
- Uses ThreadPoolExecutor for concurrent batch processing
- Number of workers determined by Anthropic tier setting
- Rate limiting prevents hitting API limits
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.services.claude_service import claude_service
from app.services.task_service import task_service
from app.services.tool_loader import tool_loader
from app.services.message_service import message_service
from app.utils.encoding import encode_bytes_to_base64
from app.utils.pdf_utils import get_page_count, extract_single_page_bytes
from app.utils.tier_config import get_anthropic_config
from config import Config


# Maximum pages per batch - balances context awareness and output token limits
# With document titles identifying each page, we can use larger batches
MAX_PAGES_PER_BATCH = 5


class CancelledException(Exception):
    """Raised when processing is cancelled by user."""
    pass


class PDFService:
    """
    Service class for managing PDF text extraction using tool-based approach.

    Educational Note: This service orchestrates PDF processing:
    1. Splits PDF into batches of pages (max 5 per batch)
    2. Sends each batch to Claude API with all pages visible
    3. Claude uses submit_page_extraction tool for each page (with context!)
    4. Collects results, writes to file in page order
    5. For large PDFs, processes batches in parallel
    """

    def __init__(self):
        """Initialize the PDF service."""
        self.projects_dir = Config.PROJECTS_DIR
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self._prompt_config = None
        self._tool_definition = None
        # Rate limiting state
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0.0
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

    def _get_tier_config(self) -> Dict[str, Any]:
        """
        Get tier configuration from centralized tier_config utility.

        Educational Note: The tier is set in .env via the AppSettings UI.
        The tier_config utility manages configurations for all APIs.
        """
        return get_anthropic_config()

    def _rate_limit(self, requests_per_minute: int) -> None:
        """
        Rate limit API calls to stay within tier limits.

        Educational Note: With batching, we count batches (not pages) for rate limiting
        since each batch = 1 API call.

        Args:
            requests_per_minute: Maximum API calls allowed per minute
        """
        with self._rate_limit_lock:
            current_time = time.time()

            # Reset counter if we're in a new minute
            if current_time - self._minute_start_time >= 60:
                self._requests_this_minute = 0
                self._minute_start_time = current_time

            # Check if we need to wait
            if self._requests_this_minute >= requests_per_minute:
                wait_time = 60 - (current_time - self._minute_start_time)
                if wait_time > 0:
                    print(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    self._requests_this_minute = 0
                    self._minute_start_time = time.time()

            self._requests_this_minute += 1

    def _load_prompt_config(self) -> Dict[str, Any]:
        """
        Load the PDF extraction prompt configuration.

        Educational Note: The prompt config includes:
        - system_prompt: Instructions for extraction + parallel tool use hints
        - user_message: Template for the extraction request
        - model, max_tokens, temperature settings
        """
        if self._prompt_config is None:
            prompt_path = self.prompts_dir / "pdf_extraction_prompt.json"

            if not prompt_path.exists():
                raise FileNotFoundError(f"PDF extraction prompt not found: {prompt_path}")

            with open(prompt_path, "r") as f:
                self._prompt_config = json.load(f)

        return self._prompt_config

    def _load_tool_definition(self) -> Dict[str, Any]:
        """
        Load the PDF extraction tool definition.

        Educational Note: The tool definition tells Claude:
        - What the tool does (extract text for a page)
        - What parameters it accepts (page_number, extracted_text, etc.)
        - That it should be called once per page
        """
        if self._tool_definition is None:
            self._tool_definition = tool_loader.load_tool("pdf_tools", "pdf_extraction")
        return self._tool_definition

    def _get_processed_dir(self, project_id: str) -> Path:
        """Get the processed files directory for a project."""
        processed_dir = self.projects_dir / project_id / "sources" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        return processed_dir

    def _create_batch_pages(
        self,
        page_bytes_list: List[Tuple[int, bytes]],
        batch_size: int = MAX_PAGES_PER_BATCH
    ) -> List[List[Tuple[int, bytes]]]:
        """
        Split pages into batches for processing.

        Educational Note: We batch pages to balance:
        - Context window limits (too many pages = too much input)
        - Context awareness (more pages per batch = better cross-page understanding)
        - API costs (fewer calls = lower cost)

        Args:
            page_bytes_list: List of (page_number, page_bytes) tuples
            batch_size: Maximum pages per batch

        Returns:
            List of batches, each batch is a list of (page_number, page_bytes)
        """
        batches = []
        for i in range(0, len(page_bytes_list), batch_size):
            batch = page_bytes_list[i:i + batch_size]
            batches.append(batch)
        return batches

    def _extract_batch_with_tools(
        self,
        batch: List[Tuple[int, bytes]],
        total_pages: int,
        pdf_name: str,
        prompt_config: Dict[str, Any],
        tool_def: Dict[str, Any],
        requests_per_minute: int,
        max_retries: int = 3
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Extract text from a batch of PDF pages using tool-based approach.

        Educational Note: This is the core of the new extraction approach:
        1. Build a message with ALL pages in the batch as document blocks
        2. Each document has a title like "filename.pdf - Page 7" for identification
        3. Claude can see all pages → understands cross-page context
        4. Force tool use with tool_choice={"type": "tool", "name": "..."}
        5. Claude calls submit_page_extraction once per page
        6. We parse tool calls to get per-page extracted text

        Args:
            batch: List of (page_number, page_bytes) tuples
            total_pages: Total pages in the entire PDF (for context)
            pdf_name: Original PDF filename (e.g., "8page.pdf") for document titles
            prompt_config: Prompt configuration dict
            tool_def: Tool definition for submit_page_extraction
            requests_per_minute: Rate limit for this tier
            max_retries: Maximum retry attempts for failed requests

        Returns:
            Tuple of (first_page_in_batch, results_dict)
        """
        batch_start_page = batch[0][0]
        batch_page_numbers = [p[0] for p in batch]

        model = prompt_config.get("model", "claude-haiku-4-5-20251001")
        system_prompt = prompt_config.get("system_prompt", "")
        user_message_template = prompt_config.get("user_message", "")
        max_tokens = prompt_config.get("max_tokens", 16000)
        temperature = prompt_config.get("temperature", 0)

        # Build content blocks: one document block per page in batch
        # Each document has a title field to identify which page it is
        # This follows Anthropic's recommended pattern for multi-document messages
        content_blocks = []
        for page_num, page_bytes in batch:
            page_base64 = encode_bytes_to_base64(page_bytes)
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": page_base64
                },
                # Title identifies which page this document represents
                # Claude uses this to know which page_number to use in tool calls
                "title": f"{pdf_name} - Page {page_num}",
            })

        # Build user message describing what to extract
        # IMPORTANT: Explicitly list the page numbers so Claude uses correct numbering
        batch_page_nums = [p[0] for p in batch]
        if len(batch) == 1:
            extraction_desc = f"page {batch[0][0]}"
            page_list = str(batch[0][0])
        else:
            extraction_desc = f"pages {batch[0][0]} to {batch[-1][0]}"
            page_list = ", ".join(str(p) for p in batch_page_nums)

        user_message = user_message_template.format(
            total_pages=total_pages,
            extraction_description=extraction_desc,
            expected_tool_calls=len(batch),
            page_numbers=page_list  # Add explicit page numbers
        )

        content_blocks.append({
            "type": "text",
            "text": user_message
        })

        messages = [{"role": "user", "content": content_blocks}]

        # Retry loop with rate limiting
        last_error = None
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before each API call
                self._rate_limit(requests_per_minute)

                # Call Claude API with tool and forced tool use
                response = claude_service.send_message(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=[tool_def],
                    # Force Claude to use this specific tool (not just "any" tool)
                    tool_choice={"type": "tool", "name": "submit_page_extraction"}
                )

                # Parse tool calls from response
                page_results = self._parse_tool_calls(response, batch_page_numbers)

                return (batch_start_page, {
                    "success": True,
                    "page_results": page_results,
                    "token_usage": response["usage"],
                    "model": response["model"]
                })

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error (429)
                if "rate" in error_str or "429" in error_str or "overloaded" in error_str:
                    wait_time = (attempt + 1) * 30
                    print(f"Batch starting page {batch_start_page}: Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"Batch starting page {batch_start_page}: Error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)

        # All retries exhausted
        return (batch_start_page, {
            "success": False,
            "error": str(last_error),
            "failed_pages": batch_page_numbers
        })

    def _parse_tool_calls(
        self,
        response: Dict[str, Any],
        expected_pages: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Parse PDF extraction tool calls from Claude's response.

        Educational Note: Uses message_service.extract_tool_inputs() for generic
        tool parsing, then processes the PDF-specific fields (page_number,
        extracted_text, continuation flags).

        Args:
            response: Response dict from claude_service
            expected_pages: List of page numbers we expected extractions for

        Returns:
            Dict mapping page_number -> extraction result
        """
        page_results = {}

        # Use message_service for generic tool parsing
        tool_inputs = message_service.extract_tool_inputs(response, "submit_page_extraction")

        # Process PDF-specific fields from each tool call
        for inputs in tool_inputs:
            page_num = inputs.get("page_number")
            extracted_text = inputs.get("extracted_text", "")
            continues_from_previous = inputs.get("continues_from_previous", False)
            continues_to_next = inputs.get("continues_to_next", False)

            if page_num is not None:
                page_results[page_num] = {
                    "text": extracted_text,
                    "continues_from_previous": continues_from_previous,
                    "continues_to_next": continues_to_next
                }

        # Check for missing pages (Claude didn't call tool for some pages)
        missing_pages = set(expected_pages) - set(page_results.keys())
        if missing_pages:
            print(f"WARNING: Missing extractions for pages: {sorted(missing_pages)}")
            # Mark missing pages as errors so the whole extraction fails
            for page_num in missing_pages:
                page_results[page_num] = {
                    "text": "[EXTRACTION FAILED - No tool call received]",
                    "continues_from_previous": False,
                    "continues_to_next": False,
                    "error": "No tool call received for this page"
                }

        return page_results

    def extract_text_from_pdf(
        self,
        project_id: str,
        source_id: str,
        pdf_path: Path
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file using BATCHED TOOL-BASED processing.

        Educational Note: This method implements the new extraction approach:
        1. Gets total page count and tier configuration
        2. Extracts page bytes for all pages
        3. Splits into batches (max 5 pages per batch)
        4. For each batch: sends all pages, Claude uses tools for per-page extraction
        5. For large PDFs: processes batches in parallel
        6. Collects all results, writes to file in page order

        Benefits over page-by-page:
        - Context awareness: Claude sees surrounding pages
        - Better handling of content spanning page boundaries
        - Fewer API calls (5 pages per call vs 1)

        Args:
            project_id: The project UUID
            source_id: The source UUID
            pdf_path: Path to the PDF file

        Returns:
            Dict with extraction results
        """
        print(f"Starting BATCHED TOOL-BASED PDF extraction for source: {source_id}")

        # Get output path early for cleanup on failure
        processed_dir = self._get_processed_dir(project_id)
        output_path = processed_dir / f"{source_id}.txt"

        try:
            # Step 1: Load configurations
            prompt_config = self._load_prompt_config()
            tool_def = self._load_tool_definition()
            model = prompt_config.get("model", "claude-haiku-4-5-20251001")
            tier_config = self._get_tier_config()
            max_workers = tier_config["max_workers"]
            # For batched approach, rate limit is per batch (API call), not per page
            # Divide pages_per_minute by batch size to get batches_per_minute
            pages_per_minute = tier_config["pages_per_minute"]
            batches_per_minute = max(1, pages_per_minute // MAX_PAGES_PER_BATCH)

            print(f"Using model: {model}")
            print(f"Tier config: {max_workers} workers, ~{batches_per_minute} batches/min")

            # Step 2: Get page count
            total_pages = get_page_count(pdf_path)
            print(f"PDF has {total_pages} pages")

            # Step 3: Extract all page bytes upfront
            print("Extracting page bytes...")
            page_bytes_list: List[Tuple[int, bytes]] = []
            for page_num in range(1, total_pages + 1):
                page_bytes = extract_single_page_bytes(pdf_path, page_num)
                page_bytes_list.append((page_num, page_bytes))

            # Step 4: Create batches
            batches = self._create_batch_pages(page_bytes_list)
            total_batches = len(batches)
            print(f"Split into {total_batches} batch(es) of up to {MAX_PAGES_PER_BATCH} pages each")

            # Step 5: Process batches
            all_page_results: Dict[int, Dict[str, Any]] = {}
            total_input_tokens = 0
            total_output_tokens = 0
            batches_completed = 0

            # Get PDF filename for document titles
            pdf_name = pdf_path.name

            if total_batches == 1:
                # Single batch - no need for parallel processing
                print("Processing single batch...")
                _, batch_result = self._extract_batch_with_tools(
                    batches[0],
                    total_pages,
                    pdf_name,
                    prompt_config,
                    tool_def,
                    batches_per_minute
                )

                if not batch_result.get("success"):
                    raise Exception(batch_result.get("error", "Batch extraction failed"))

                all_page_results.update(batch_result.get("page_results", {}))
                total_input_tokens += batch_result.get("token_usage", {}).get("input_tokens", 0)
                total_output_tokens += batch_result.get("token_usage", {}).get("output_tokens", 0)

            else:
                # Multiple batches - process in parallel
                print(f"Processing {total_batches} batches in parallel with {max_workers} workers...")

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_batch = {
                        executor.submit(
                            self._extract_batch_with_tools,
                            batch,
                            total_pages,
                            pdf_name,
                            prompt_config,
                            tool_def,
                            batches_per_minute
                        ): batch[0][0]  # Track by first page number
                        for batch in batches
                    }

                    for future in as_completed(future_to_batch):
                        # Check for cancellation
                        if task_service.is_target_cancelled(source_id):
                            print(f"Processing cancelled for source {source_id}")
                            for f in future_to_batch:
                                f.cancel()
                            raise CancelledException("Processing cancelled by user")

                        batch_start, batch_result = future.result()
                        batches_completed += 1

                        if batch_result.get("success"):
                            all_page_results.update(batch_result.get("page_results", {}))
                            total_input_tokens += batch_result.get("token_usage", {}).get("input_tokens", 0)
                            total_output_tokens += batch_result.get("token_usage", {}).get("output_tokens", 0)
                            print(f"Batch {batches_completed}/{total_batches} complete (pages starting at {batch_start})")
                        else:
                            failed_pages = batch_result.get("failed_pages", [])
                            error_msg = batch_result.get("error", "Unknown error")
                            print(f"Batch starting at page {batch_start} FAILED: {error_msg}")
                            # Mark failed pages
                            for page_num in failed_pages:
                                all_page_results[page_num] = {
                                    "text": f"[EXTRACTION FAILED: {error_msg}]",
                                    "error": error_msg
                                }

            # Step 6: Check for failures
            failed_pages = [
                page_num for page_num, result in all_page_results.items()
                if result.get("error")
            ]

            if failed_pages:
                # Don't save partial results - let user retry
                error_message = f"Failed to extract {len(failed_pages)} page(s): {sorted(failed_pages)[:5]}"
                if len(failed_pages) > 5:
                    error_message += f" (and {len(failed_pages) - 5} more)"

                print(f"Extraction FAILED: {error_message}")

                return {
                    "success": False,
                    "status": "error",
                    "error": error_message,
                    "total_pages": total_pages,
                    "failed_pages": sorted(failed_pages)
                }

            # Step 7: Write results to file IN ORDER
            print("All pages extracted successfully. Writing to file...")

            total_characters = 0

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Extracted from PDF: {pdf_path.name}\n")
                f.write(f"# Total pages: {total_pages}\n")
                f.write(f"# Extracted at: {datetime.now().isoformat()}\n")
                f.write(f"# Method: Batched tool-based extraction ({MAX_PAGES_PER_BATCH} pages/batch)\n")
                f.write(f"# Batches: {total_batches}, Workers: {max_workers}\n\n")

                for page_num in sorted(all_page_results.keys()):
                    result = all_page_results[page_num]
                    extracted_text = result.get("text", "")

                    # Add continuation markers if present
                    markers = []
                    if result.get("continues_from_previous"):
                        markers.append("(continues from previous page)")
                    if result.get("continues_to_next"):
                        markers.append("(continues to next page)")
                    marker_str = " ".join(markers)

                    f.write(f"\n=== PDF PAGE {page_num} of {total_pages} {marker_str}===\n\n")
                    f.write(extracted_text)
                    f.write("\n")

                    total_characters += len(extracted_text)

            print(f"Extraction complete. {total_pages}/{total_pages} pages processed.")
            print(f"Total tokens: {total_input_tokens} input, {total_output_tokens} output")

            return {
                "success": True,
                "status": "ready",
                "extracted_text_path": str(output_path),
                "total_pages": total_pages,
                "pages_processed": total_pages,
                "character_count": total_characters,
                "token_usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens
                },
                "model_used": model,
                "extracted_at": datetime.now().isoformat(),
                "extraction_method": "batched_tool_based",
                "batch_size": MAX_PAGES_PER_BATCH,
                "total_batches": total_batches,
                "parallel_workers": max_workers,
                "errors": None
            }

        except CancelledException as e:
            print(f"PDF extraction cancelled: {e}")
            if output_path.exists():
                output_path.unlink()
                print(f"Deleted partial output file: {output_path}")
            return {
                "success": False,
                "status": "cancelled",
                "error": "Processing cancelled by user"
            }

        except FileNotFoundError as e:
            print(f"File not found: {e}")
            if output_path.exists():
                output_path.unlink()
            return {
                "success": False,
                "status": "error",
                "error": f"File not found: {str(e)}"
            }

        except Exception as e:
            print(f"PDF extraction failed: {e}")
            if output_path.exists():
                output_path.unlink()
                print(f"Deleted partial output file: {output_path}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }


# Singleton instance for easy import
pdf_service = PDFService()
