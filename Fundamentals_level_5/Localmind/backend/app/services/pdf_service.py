"""
PDF Service - Manages PDF processing and text extraction.

Educational Note: This service MANAGES the PDF processing workflow,
but delegates the actual API calls to claude_service. This separation
ensures:
- pdf_service handles: pagination, page-by-page processing, file I/O, progress
- claude_service handles: API calls, token counting, error handling

Page-by-page processing:
- Claude API has a 100-page limit per request
- We process 1 page at a time to handle PDFs of any size
- Each page's text is appended to the output file with a page marker
- Progress is tracked and can be resumed (future enhancement)

Parallel Processing:
- Uses ThreadPoolExecutor for concurrent API calls
- Number of workers determined by Anthropic tier setting
- Rate limiting prevents hitting API limits
- Results collected in-memory, written in order after all complete

Citations:
- Enabled on document blocks for accurate source references
- Claude returns citations with exact locations in the source
- Useful for later RAG and source verification

Model: claude-haiku-4-5-20251001 (configured in prompt file)
- Fastest and cheapest Claude model
- Sufficient for text extraction tasks
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.services.claude_service import claude_service
from app.services.task_service import task_service
from app.utils.encoding import encode_bytes_to_base64
from app.utils.pdf_utils import get_page_count, extract_single_page_bytes
from app.utils.tier_config import get_anthropic_config, APIProvider
from config import Config


class CancelledException(Exception):
    """Raised when processing is cancelled by user."""
    pass


class PDFService:
    """
    Service class for managing PDF text extraction.

    Educational Note: This service orchestrates PDF processing:
    1. Splits PDF into individual pages
    2. Sends each page to Claude API (via claude_service) IN PARALLEL
    3. Collects results in memory, writes to file in order
    4. Tracks overall progress and token usage
    5. Rate limits based on Anthropic tier setting
    """

    def __init__(self):
        """Initialize the PDF service."""
        self.projects_dir = Config.PROJECTS_DIR
        self.prompts_dir = Config.DATA_DIR / "prompts"
        self._prompt_config = None
        # Rate limiting state
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0.0
        self._requests_this_minute = 0
        self._minute_start_time = 0.0

    def _get_tier_config(self) -> Dict[str, Any]:
        """
        Get tier configuration from centralized tier_config utility.

        Educational Note: The tier is set in .env via the AppSettings UI.
        The tier_config utility manages configurations for all APIs
        (Anthropic, OpenAI, Pinecone, etc.) in one place.
        """
        return get_anthropic_config()

    def _rate_limit(self, pages_per_minute: int) -> None:
        """
        Rate limit API calls to stay within tier limits.

        Educational Note: This implements a simple rate limiter that:
        1. Tracks requests per minute
        2. Pauses if we're about to exceed the limit
        3. Thread-safe using a lock

        Args:
            pages_per_minute: Maximum pages (API calls) allowed per minute
        """
        with self._rate_limit_lock:
            current_time = time.time()

            # Reset counter if we're in a new minute
            if current_time - self._minute_start_time >= 60:
                self._requests_this_minute = 0
                self._minute_start_time = current_time

            # Check if we need to wait
            if self._requests_this_minute >= pages_per_minute:
                # Wait until the next minute
                wait_time = 60 - (current_time - self._minute_start_time)
                if wait_time > 0:
                    print(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    # Reset after waiting
                    self._requests_this_minute = 0
                    self._minute_start_time = time.time()

            self._requests_this_minute += 1

    def _load_prompt_config(self) -> Dict[str, Any]:
        """
        Load the PDF extraction prompt configuration.

        Educational Note: Storing prompts in JSON files allows:
        - Easy editing without code changes
        - Version tracking of prompts
        - Different prompts for different use cases
        """
        if self._prompt_config is None:
            prompt_path = self.prompts_dir / "pdf_extraction_prompt.json"

            if not prompt_path.exists():
                raise FileNotFoundError(f"PDF extraction prompt not found: {prompt_path}")

            with open(prompt_path, "r") as f:
                self._prompt_config = json.load(f)

        return self._prompt_config

    def _get_processed_dir(self, project_id: str) -> Path:
        """Get the processed files directory for a project."""
        processed_dir = self.projects_dir / project_id / "sources" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        return processed_dir

    def _extract_single_page(
        self,
        page_bytes: bytes,
        page_number: int,
        total_pages: int,
        prompt_config: Dict[str, Any],
        pages_per_minute: int,
        max_retries: int = 3
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Extract text from a single PDF page using Claude API.

        Educational Note: Each page is sent as a separate API call with:
        - Citations enabled for source tracking
        - The page as a base64-encoded document block
        - A prompt instructing exact text extraction
        - Rate limiting to stay within tier limits
        - Retry logic for transient failures

        Args:
            page_bytes: PDF bytes for the single page
            page_number: 1-indexed page number
            total_pages: Total pages in the PDF (for context)
            prompt_config: Prompt configuration dict
            pages_per_minute: Rate limit for this tier
            max_retries: Maximum retry attempts for failed requests

        Returns:
            Tuple of (page_number, result_dict) for ordered collection
        """
        model = prompt_config.get("model", "claude-haiku-4-5-20251001")
        system_prompt = prompt_config.get("prompt", "")
        max_tokens = prompt_config.get("max_tokens", 8000)
        temperature = prompt_config.get("temperature", 0)
        citations_enabled = prompt_config.get("citations_enabled", True)

        # Encode page to base64
        page_base64 = encode_bytes_to_base64(page_bytes)

        # Build message with document block and citations enabled
        # Educational Note: Citations are enabled per-document block
        # This tells Claude to return citations with exact source locations
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": page_base64
                        },
                        "citations": {"enabled": citations_enabled}
                    },
                    {
                        "type": "text",
                        "text": f"This is page {page_number} of {total_pages}. Extract all text from this page following the system instructions exactly."
                    }
                ]
            }
        ]

        # Retry loop with rate limiting
        last_error = None
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before each API call
                self._rate_limit(pages_per_minute)

                # Call Claude API via claude_service
                response = claude_service.send_message(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                return (page_number, {
                    "success": True,
                    "text": response["content"],
                    "token_usage": response["usage"],
                    "model": response["model"],
                    "content_blocks": response.get("content_blocks", [])
                })

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error (429)
                if "rate" in error_str or "429" in error_str or "overloaded" in error_str:
                    # Wait longer for rate limit errors
                    wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                    print(f"Page {page_number}: Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # Exponential backoff for other errors
                    wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                    print(f"Page {page_number}: Error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)

        # All retries exhausted
        return (page_number, {
            "success": False,
            "error": str(last_error)
        })

    def extract_text_from_pdf(
        self,
        project_id: str,
        source_id: str,
        pdf_path: Path
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file using PARALLEL processing.

        Educational Note: This method uses ThreadPoolExecutor for parallel processing:
        1. Gets total page count and tier configuration
        2. Extracts page bytes for all pages upfront
        3. Submits all pages to thread pool for parallel API calls
        4. Collects results as they complete (with progress updates)
        5. IF ANY PAGE FAILS after retries → marks as FAILED and deletes partial content
        6. On success, writes all text to file IN ORDER

        This approach ensures:
        - No duplicate API calls (each page submitted exactly once)
        - Results written in correct page order (sorted before writing)
        - Clean failure handling (no partial files left behind)
        - Rate limiting respected even with parallel workers

        Args:
            project_id: The project UUID
            source_id: The source UUID
            pdf_path: Path to the PDF file

        Returns:
            Dict with extraction results
        """
        print(f"Starting PARALLEL PDF extraction for source: {source_id}")

        # Get output path early so we can clean up on failure
        processed_dir = self._get_processed_dir(project_id)
        output_path = processed_dir / f"{source_id}.txt"

        try:
            # Step 1: Load prompt configuration and tier settings
            prompt_config = self._load_prompt_config()
            model = prompt_config.get("model", "claude-haiku-4-5-20251001")
            tier_config = self._get_tier_config()
            max_workers = tier_config["max_workers"]
            pages_per_minute = tier_config["pages_per_minute"]

            print(f"Using model: {model}")
            print(f"Tier config: {max_workers} workers, {pages_per_minute} pages/min")

            # Step 2: Get page count
            total_pages = get_page_count(pdf_path)
            print(f"PDF has {total_pages} pages")

            # Step 3: Extract all page bytes upfront
            # Educational Note: We extract bytes before starting threads to avoid
            # file I/O contention during parallel processing
            print("Extracting page bytes...")
            page_bytes_list: List[Tuple[int, bytes]] = []
            for page_num in range(1, total_pages + 1):
                page_bytes = extract_single_page_bytes(pdf_path, page_num)
                page_bytes_list.append((page_num, page_bytes))

            # Step 4: Process pages in parallel
            results: Dict[int, Dict[str, Any]] = {}
            pages_completed = 0

            print(f"Starting parallel processing with {max_workers} workers...")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all page extraction tasks
                future_to_page = {
                    executor.submit(
                        self._extract_single_page,
                        page_bytes,
                        page_num,
                        total_pages,
                        prompt_config,
                        pages_per_minute
                    ): page_num
                    for page_num, page_bytes in page_bytes_list
                }

                # Collect results as they complete
                for future in as_completed(future_to_page):
                    # Check for cancellation periodically
                    if task_service.is_target_cancelled(source_id):
                        print(f"Processing cancelled for source {source_id}")
                        # Cancel remaining futures
                        for f in future_to_page:
                            f.cancel()
                        raise CancelledException("Processing cancelled by user")

                    page_num, result = future.result()
                    results[page_num] = result
                    pages_completed += 1

                    # Progress update
                    if result.get("success"):
                        print(f"Processing... {pages_completed}/{total_pages} pages complete")
                    else:
                        print(f"Page {page_num} FAILED: {result.get('error')}")

            # Step 5: Check for any failures
            # Educational Note: If ANY page fails after all retries, we fail the entire
            # extraction and clean up. This ensures no partial/corrupted files.
            failed_pages = [
                page_num for page_num, result in results.items()
                if not result.get("success")
            ]

            if failed_pages:
                # Clean up any existing output file
                if output_path.exists():
                    output_path.unlink()
                    print(f"Deleted partial output file: {output_path}")

                error_details = [
                    f"Page {p}: {results[p].get('error', 'Unknown error')}"
                    for p in sorted(failed_pages)
                ]
                error_message = f"Failed to extract {len(failed_pages)} page(s): {'; '.join(error_details[:5])}"
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

            # Step 6: Write results to file IN ORDER
            print("All pages extracted successfully. Writing to file...")

            total_input_tokens = 0
            total_output_tokens = 0
            total_characters = 0

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Extracted from PDF: {pdf_path.name}\n")
                f.write(f"# Total pages: {total_pages}\n")
                f.write(f"# Extracted at: {datetime.now().isoformat()}\n")
                f.write(f"# Processing: Parallel ({max_workers} workers)\n\n")

                # Write pages in order
                for page_num in sorted(results.keys()):
                    result = results[page_num]
                    extracted_text = result.get("text", "")
                    token_usage = result.get("token_usage", {})

                    f.write(f"\n=== PDF PAGE {page_num} of {total_pages} ===\n\n")
                    f.write(extracted_text)
                    f.write("\n")

                    # Accumulate totals
                    total_input_tokens += token_usage.get("input_tokens", 0)
                    total_output_tokens += token_usage.get("output_tokens", 0)
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
                "parallel_workers": max_workers,
                "errors": None
            }

        except CancelledException as e:
            print(f"PDF extraction cancelled: {e}")
            # Clean up any partial output
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
            # Clean up any partial output
            if output_path.exists():
                output_path.unlink()
            return {
                "success": False,
                "status": "error",
                "error": f"File not found: {str(e)}"
            }

        except Exception as e:
            print(f"PDF extraction failed: {e}")
            # Clean up any partial output
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
