"""
Configuration management for LocalMind backend.

Educational Note: Centralized configuration helps maintain consistency
and makes it easy to switch between development and production settings.
Never hardcode sensitive data - use environment variables instead.
"""
import os
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """Base configuration class with default settings."""

    # Application settings
    APP_NAME = "LocalLM"
    VERSION = "1.0.0"

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # CORS settings - allowing frontend to communicate with backend
    CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

    # File paths using Path for cross-platform compatibility
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    PROJECTS_DIR = DATA_DIR / "projects"
    TEMP_DIR = DATA_DIR / "temp"

    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'json', 'png', 'jpg', 'jpeg'}

    # API settings
    API_PREFIX = "/api/v1"

    @classmethod
    def init_app(cls, app):
        """
        Initialize the application with this config.

        Educational Note: This method ensures all necessary directories
        exist before the app starts, preventing file system errors.
        """
        # Create necessary directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.PROJECTS_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)

        # Log the configuration being used
        print(f"📱 {cls.APP_NAME} v{cls.VERSION} initialized")
        print(f"📁 Data directory: {cls.DATA_DIR}")
        print(f"🔧 Debug mode: {cls.DEBUG}")


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""
    DEBUG = True
    # More verbose logging in development
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration with security hardening."""
    DEBUG = False

    # Educational Note: We only validate SECRET_KEY when actually using production config
    # The class definition shouldn't fail just because we're importing it
    def __init__(self):
        super().__init__()
        # Use environment variable for secret key in production
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")

        # Restrict CORS in production
        self.CORS_ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')


class TestingConfig(Config):
    """Testing configuration with test database."""
    TESTING = True
    # Use separate test data directory
    DATA_DIR = Config.BASE_DIR / "test_data"


# Dictionary to easily access configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}