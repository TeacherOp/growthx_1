"""
PPTX Utilities - LibreOffice path detection and PPTX to PDF conversion.

Educational Note: These utilities handle the non-AI parts of PPTX processing:
- Detecting LibreOffice installation path across different operating systems
- Converting PPTX files to PDF using LibreOffice headless mode

Why LibreOffice?
- Free, open-source, cross-platform (macOS, Windows, Linux)
- Headless mode allows server-side conversion without GUI
- Accurate rendering of PowerPoint presentations
"""
import os
import subprocess
import platform
from pathlib import Path


def get_libreoffice_path() -> str:
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


def convert_pptx_to_pdf(pptx_path: Path, output_dir: Path) -> Path:
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
    libreoffice_path = get_libreoffice_path()

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


def is_libreoffice_available() -> bool:
    """
    Check if LibreOffice is available on this system.

    Returns:
        True if LibreOffice is found, False otherwise
    """
    try:
        get_libreoffice_path()
        return True
    except FileNotFoundError:
        return False
