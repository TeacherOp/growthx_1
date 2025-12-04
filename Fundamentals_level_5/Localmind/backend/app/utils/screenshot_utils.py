"""
Screenshot Utilities - Playwright-based HTML to PNG screenshot capture.

Educational Note: This module uses Playwright to capture screenshots of HTML files
at exact viewport dimensions (1920x1080) for presentation export.

Why Playwright?
- Headless browser automation with modern web support
- Precise viewport control for consistent screenshot dimensions
- Native Python library (no Node.js subprocess required)
- Supports all CSS features (Tailwind, custom fonts, etc.)

Usage:
    from app.utils.screenshot_utils import capture_slides_as_screenshots

    screenshots = capture_slides_as_screenshots(
        slides_dir="/path/to/slides",
        output_dir="/path/to/screenshots",
        slide_files=["slide_01.html", "slide_02.html"]
    )
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright


# Slide dimensions (standard 16:9 presentation)
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080


async def _capture_screenshot_async(
    page,
    html_path: Path,
    output_path: Path
) -> bool:
    """
    Capture a screenshot of an HTML file asynchronously.

    Args:
        page: Playwright page object
        html_path: Path to the HTML file
        output_path: Path to save the screenshot

    Returns:
        True if successful, False otherwise
    """
    try:
        # Navigate to the HTML file
        file_url = f"file://{html_path.absolute()}"
        await page.goto(file_url, wait_until="networkidle")

        # Wait for fonts and images to load
        await page.wait_for_timeout(500)

        # Capture screenshot
        await page.screenshot(path=str(output_path), full_page=False)

        return True

    except Exception as e:
        print(f"[Screenshot] Error capturing {html_path.name}: {e}")
        return False


async def _capture_slides_async(
    slides_dir: Path,
    output_dir: Path,
    slide_files: List[str],
    progress_callback: Optional[callable] = None
) -> List[Dict[str, Any]]:
    """
    Capture screenshots of multiple HTML slides asynchronously.

    Args:
        slides_dir: Directory containing HTML slide files
        output_dir: Directory to save screenshots
        slide_files: List of slide filenames to capture
        progress_callback: Optional callback for progress updates

    Returns:
        List of screenshot info dicts
    """
    screenshots = []

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)

        # Create page with exact viewport dimensions
        page = await browser.new_page(
            viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT}
        )

        for i, slide_file in enumerate(slide_files):
            html_path = slides_dir / slide_file
            screenshot_name = slide_file.replace(".html", ".png")
            output_path = output_dir / screenshot_name

            if progress_callback:
                progress_callback("capturing_slide", {
                    "slide": slide_file,
                    "index": i + 1,
                    "total": len(slide_files)
                })

            print(f"[Screenshot] Capturing {slide_file} ({i + 1}/{len(slide_files)})")

            success = await _capture_screenshot_async(page, html_path, output_path)

            if success:
                screenshots.append({
                    "slide_file": slide_file,
                    "screenshot_file": screenshot_name,
                    "screenshot_path": str(output_path),
                    "success": True
                })
            else:
                screenshots.append({
                    "slide_file": slide_file,
                    "screenshot_file": None,
                    "screenshot_path": None,
                    "success": False
                })

        await browser.close()

    return screenshots


def capture_slides_as_screenshots(
    slides_dir: str,
    output_dir: str,
    slide_files: List[str],
    progress_callback: Optional[callable] = None
) -> List[Dict[str, Any]]:
    """
    Capture screenshots of HTML slides using Playwright.

    Educational Note: This function wraps the async Playwright API
    in a synchronous interface for easier integration with Flask.

    Args:
        slides_dir: Directory containing HTML slide files
        output_dir: Directory to save screenshots
        slide_files: List of slide filenames to capture (in order)
        progress_callback: Optional callback for progress updates

    Returns:
        List of dicts with screenshot info:
        [
            {
                "slide_file": "slide_01.html",
                "screenshot_file": "slide_01.png",
                "screenshot_path": "/path/to/slide_01.png",
                "success": True
            },
            ...
        ]

    Example:
        screenshots = capture_slides_as_screenshots(
            slides_dir="/path/to/presentations/job123/slides",
            output_dir="/path/to/presentations/job123/screenshots",
            slide_files=["slide_01.html", "slide_02.html", "slide_03.html"]
        )
    """
    slides_path = Path(slides_dir)
    output_path = Path(output_dir)

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Validate slides directory exists
    if not slides_path.exists():
        print(f"[Screenshot] Slides directory not found: {slides_dir}")
        return []

    # Filter to only existing files
    valid_slides = []
    for slide in slide_files:
        if (slides_path / slide).exists():
            valid_slides.append(slide)
        else:
            print(f"[Screenshot] Slide not found, skipping: {slide}")

    if not valid_slides:
        print("[Screenshot] No valid slides to capture")
        return []

    # Run async function in event loop
    try:
        screenshots = asyncio.run(
            _capture_slides_async(slides_path, output_path, valid_slides, progress_callback)
        )
    except RuntimeError as e:
        # If already in async context, use the existing loop
        if "cannot be called from a running event loop" in str(e):
            print(f"[Screenshot] Already in async context, using existing loop")
            loop = asyncio.get_event_loop()
            screenshots = loop.run_until_complete(
                _capture_slides_async(slides_path, output_path, valid_slides, progress_callback)
            )
        else:
            print(f"[Screenshot] Error in async screenshot capture: {e}")
            return []
    except Exception as e:
        print(f"[Screenshot] Error in screenshot capture: {e}")
        return []

    successful = sum(1 for s in screenshots if s["success"])
    print(f"[Screenshot] Captured {successful}/{len(valid_slides)} slides")

    return screenshots


def is_playwright_available() -> bool:
    """
    Check if Playwright is installed and browsers are available.

    Returns:
        True if Playwright can be used, False otherwise
    """
    try:
        from playwright.async_api import async_playwright as _  # noqa: F401
        return True
    except ImportError:
        return False
