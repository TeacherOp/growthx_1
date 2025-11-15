"""
Screenshot capture utility using Playwright
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def capture_slide_screenshots(slide_files: list, output_dir: str = "screenshots", progress_callback=None) -> list:
    """
    Capture screenshots of HTML slides using Playwright

    Args:
        slide_files: List of HTML file paths
        output_dir: Directory to save screenshots
        progress_callback: Optional callback function(event_type, data)

    Returns:
        List of screenshot file paths
    """

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    screenshots = []

    print(f"\n📸 Capturing screenshots...")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)

        # Create page with exact slide dimensions (1920x1080 - standard PowerPoint)
        page = browser.new_page(
            viewport={'width': 1920, 'height': 1080}
        )

        for i, slide_file in enumerate(slide_files, 1):
            try:
                # Get absolute path
                slide_path = Path(slide_file).resolve()

                if not slide_path.exists():
                    print(f"   ⚠️  Slide not found: {slide_file}")
                    continue

                # Navigate to slide using file:// protocol
                file_url = f"file://{slide_path}"
                page.goto(file_url, wait_until='networkidle')

                # Wait a bit for fonts and styles to load
                page.wait_for_timeout(500)

                # Screenshot filename
                screenshot_file = output_path / f"slide_{i}.png"

                # Take screenshot
                page.screenshot(
                    path=str(screenshot_file),
                    full_page=False  # Only capture viewport
                )

                screenshots.append(str(screenshot_file))
                print(f"   ✅ Captured: {screenshot_file.name}")

                # Emit progress event
                if progress_callback:
                    progress_callback('screenshot_captured', {
                        'slide_number': i,
                        'total_slides': len(slide_files),
                        'filename': screenshot_file.name
                    })

            except Exception as e:
                print(f"   ❌ Error capturing {slide_file}: {str(e)}")

        browser.close()

    print(f"✅ Captured {len(screenshots)} screenshots\n")

    return screenshots
