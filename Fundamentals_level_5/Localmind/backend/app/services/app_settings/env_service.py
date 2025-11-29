"""
Service for managing environment variables and .env file operations.

Educational Note: This service provides a safe way to read, write, and
update the .env file while maintaining the Flask app's environment.
"""
import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv, set_key, unset_key


class EnvService:
    """
    Service for managing environment variables and .env file.

    Educational Note: This class encapsulates all .env file operations,
    providing methods for CRUD operations on environment variables.
    """

    def __init__(self):
        """Initialize the service and locate the .env file."""
        # Find the .env file in the backend directory
        self.backend_dir = Path(__file__).parent.parent.parent.parent
        self.env_path = self.backend_dir / '.env'

        # Create .env file if it doesn't exist
        if not self.env_path.exists():
            self.env_path.touch()
            print(f"Created new .env file at: {self.env_path}")

        # Load current environment variables
        self.reload_env()

    def reload_env(self):
        """
        Reload environment variables from the .env file.

        Educational Note: This ensures our app has the latest values
        after any .env file updates.
        """
        load_dotenv(self.env_path, override=True)

    def get_key(self, key: str) -> Optional[str]:
        """
        Get an environment variable value.

        Args:
            key: The environment variable name

        Returns:
            The value or None if not found
        """
        return os.getenv(key)

    def set_key(self, key: str, value: str):
        """
        Set an environment variable in the .env file.

        Educational Note: This uses python-dotenv's set_key function
        which safely updates the .env file without losing other values.
        It also handles commented lines properly.

        Args:
            key: The environment variable name
            value: The value to set
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        # First, check if the key exists as a comment and remove it
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                lines = f.readlines()

            # Remove any commented versions of this key
            new_lines = []
            for line in lines:
                # Skip commented lines that contain this key
                if line.strip().startswith('#') and f'{key}=' in line:
                    continue
                new_lines.append(line)

            # Write back without the commented key
            with open(self.env_path, 'w') as f:
                f.writelines(new_lines)

        # Use python-dotenv's set_key to update the .env file
        success = set_key(self.env_path, key, value, quote_mode='never')
        if not success:
            raise RuntimeError(f"Failed to set key {key} in .env file")

        # Also set in current environment immediately
        os.environ[key] = value

    def delete_key(self, key: str):
        """
        Remove an environment variable from the .env file.

        Args:
            key: The environment variable name to remove
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        # Use python-dotenv's unset_key to remove from .env file
        success = unset_key(self.env_path, key)
        if not success:
            # Key might not exist, which is okay
            pass

        # Also remove from current environment
        if key in os.environ:
            del os.environ[key]

    def save(self):
        """
        Save changes to the .env file.

        Educational Note: Since we're using set_key/unset_key,
        changes are already saved. This method is for consistency.
        """
        # Changes are already saved by set_key/unset_key
        # This method exists for API consistency
        pass

    def mask_key(self, value: Optional[str]) -> str:
        """
        Mask an API key for display, showing only first and last few characters.

        Educational Note: This is crucial for security - we never want to
        expose full API keys in the UI or logs.

        Args:
            value: The API key to mask

        Returns:
            Masked version like 'sk-abc***xyz'
        """
        if not value:
            return ''

        if len(value) <= 8:
            # Very short keys, mask entirely
            return '***'

        # Show first 3 and last 3 characters
        return f"{value[:3]}***{value[-3:]}"

    def get_all_keys(self) -> Dict[str, str]:
        """
        Get all environment variables from the .env file.

        Returns:
            Dictionary of all key-value pairs
        """
        env_vars = {}
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        env_vars[key] = value
        return env_vars
