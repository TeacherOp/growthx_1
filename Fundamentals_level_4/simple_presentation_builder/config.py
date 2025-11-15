"""
Configuration Management for Presentation Builder

This module centralizes all configuration for the Flask application,
making it easier for students to understand environment setup and app configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Find and load .env file from project root
# find_dotenv() searches parent directories for .env file
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path)


class Config:
    """Application configuration class"""

    # API Keys
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    # Flask Configuration
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Server Configuration
    PORT = int(os.environ.get("FLASK_PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    HOST = "0.0.0.0"

    # File Upload Configuration
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Directory Configuration - relative to this file's location
    BASE_DIR = Path(__file__).parent

    # All input/output data is organized in one folder for clarity
    DATA_DIR = BASE_DIR / 'input_output_data'

    # Input folder - where user uploads are stored
    UPLOAD_FOLDER = DATA_DIR / 'uploads'

    # Output folders - where generated files are stored
    SLIDES_FOLDER = DATA_DIR / 'slides'           # HTML slides
    EXPORTS_FOLDER = DATA_DIR / 'exports'          # Final PPTX files
    SCREENSHOTS_FOLDER = DATA_DIR / 'screenshots'  # Slide screenshots for PPTX creation

    # AI Model Configuration
    MODEL_NAME = "claude-sonnet-4-5-20250929"

    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please set it in your .env file at the project root."
            )

    @classmethod
    def ensure_directories(cls):
        """
        Ensure all required directories exist

        Creates the main data directory and all subdirectories.
        Using parents=True ensures parent directories are created if needed.
        """
        # Create main data directory first
        cls.DATA_DIR.mkdir(exist_ok=True)

        # Create subdirectories
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.SLIDES_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_FOLDER.mkdir(parents=True, exist_ok=True)


# Utility function to check if file extension is allowed
def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension

    Args:
        filename: The filename to check

    Returns:
        True if the file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
