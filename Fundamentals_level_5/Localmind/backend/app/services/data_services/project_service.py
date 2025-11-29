"""
Project Service - Business logic for project management.

Educational Note: This service layer handles all project-related operations,
keeping business logic separate from API endpoints. It manages JSON file
storage for simplicity (no database needed for learning purposes).
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from config import Config


class ProjectService:
    """
    Service class for managing projects.

    Educational Note: We use JSON files instead of a database to keep
    things simple and transparent. Each project is a JSON file in the
    projects directory.
    """

    def __init__(self):
        """Initialize the project service with the projects directory."""
        self.projects_dir = Config.PROJECTS_DIR
        # Ensure projects directory exists
        self.projects_dir.mkdir(exist_ok=True, parents=True)

        # Create a projects index file to track all projects
        self.index_file = self.projects_dir / "projects_index.json"
        self._initialize_index()

    def _initialize_index(self):
        """
        Initialize the projects index file if it doesn't exist.

        Educational Note: The index file keeps track of all projects
        without having to scan the directory each time. This improves
        performance and provides a single source of truth.
        """
        if not self.index_file.exists():
            initial_index = {
                "projects": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_index(initial_index)

    def _load_index(self) -> Dict[str, Any]:
        """Load the projects index from file."""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is corrupted or missing, reinitialize
            self._initialize_index()
            with open(self.index_file, 'r') as f:
                return json.load(f)

    def _save_index(self, index_data: Dict[str, Any]):
        """Save the projects index to file."""
        index_data["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

    def list_all_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects.

        Returns:
            List of project metadata (not full project data)

        Educational Note: We only return metadata to keep responses small.
        Full project data is loaded only when needed.
        """
        index = self._load_index()
        # Sort by last accessed time, most recent first
        projects = sorted(
            index["projects"],
            key=lambda p: p.get("last_accessed", p["created_at"]),
            reverse=True
        )
        return projects

    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            description: Optional project description

        Returns:
            Created project object

        Raises:
            ValueError: If project name already exists

        Educational Note: We use UUID for project IDs to ensure uniqueness
        without needing a database sequence.
        """
        # Check if project name already exists
        index = self._load_index()
        if any(p["name"].lower() == name.lower() for p in index["projects"]):
            raise ValueError(f"Project with name '{name}' already exists")

        # Generate unique project ID
        project_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create project metadata
        project_metadata = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": timestamp,
            "updated_at": timestamp,
            "last_accessed": timestamp
        }

        # Create project data structure
        project_data = {
            **project_metadata,
            "documents": [],
            "notes": [],
            "meetings": [],
            "settings": {
                "ai_model": "claude-sonnet-4-5",
                "auto_save": True,
                "custom_prompt": None  # None = use default prompt
            }
        }

        # Save project file
        project_file = self.projects_dir / f"{project_id}.json"
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)

        # Update index
        index["projects"].append(project_metadata)
        self._save_index(index)

        # Print creation message for learning purposes
        print(f"Created project: {name} (ID: {project_id})")

        return project_metadata

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full project data by ID.

        Args:
            project_id: The project UUID

        Returns:
            Full project data or None if not found

        Educational Note: This loads the entire project file, which could
        be large. In production, you might want to load parts selectively.
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            return None

        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)

            # Update last accessed time
            project_data["last_accessed"] = datetime.now().isoformat()
            self._save_project_data(project_id, project_data)

            return project_data
        except json.JSONDecodeError:
            print(f"Warning: Corrupted project file: {project_id}")
            return None

    def update_project(self, project_id: str, name: Optional[str] = None,
                      description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update project metadata.

        Args:
            project_id: The project UUID
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated project metadata or None if not found

        Educational Note: We update both the project file and the index
        to maintain consistency.
        """
        # Load project data
        project_data = self.get_project(project_id)
        if not project_data:
            return None

        # Check if new name conflicts with existing project
        if name and name != project_data["name"]:
            index = self._load_index()
            if any(p["name"].lower() == name.lower() for p in index["projects"]
                   if p["id"] != project_id):
                raise ValueError(f"Project with name '{name}' already exists")

        # Update fields if provided
        if name:
            project_data["name"] = name
        if description is not None:  # Allow empty string to clear description
            project_data["description"] = description

        project_data["updated_at"] = datetime.now().isoformat()

        # Save updated project
        self._save_project_data(project_id, project_data)

        # Update index
        self._update_index_entry(project_id, project_data)

        print(f"Updated project: {project_id}")

        # Return only metadata
        return {
            "id": project_data["id"],
            "name": project_data["name"],
            "description": project_data["description"],
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "last_accessed": project_data["last_accessed"]
        }

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: The project UUID

        Returns:
            True if deleted, False if not found

        Educational Note: We do a hard delete here for simplicity.
        In production, you might want soft delete (mark as deleted but keep data).
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            return False

        # Delete the project file
        project_file.unlink()

        # Remove from index
        index = self._load_index()
        index["projects"] = [p for p in index["projects"] if p["id"] != project_id]
        self._save_index(index)

        print(f"Deleted project: {project_id}")
        return True

    def open_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Open a project (update last accessed time).

        Args:
            project_id: The project UUID

        Returns:
            Project metadata or None if not found

        Educational Note: This is similar to get_project but returns
        only metadata for efficiency when just marking as opened.
        """
        project_data = self.get_project(project_id)
        if not project_data:
            return None

        # Return only metadata
        return {
            "id": project_data["id"],
            "name": project_data["name"],
            "description": project_data["description"],
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "last_accessed": project_data["last_accessed"]
        }

    def _save_project_data(self, project_id: str, data: Dict[str, Any]):
        """Helper method to save project data to file."""
        project_file = self.projects_dir / f"{project_id}.json"
        with open(project_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _update_index_entry(self, project_id: str, project_data: Dict[str, Any]):
        """Helper method to update a project entry in the index."""
        index = self._load_index()

        # Find and update the project in index
        for i, project in enumerate(index["projects"]):
            if project["id"] == project_id:
                index["projects"][i] = {
                    "id": project_data["id"],
                    "name": project_data["name"],
                    "description": project_data.get("description", ""),
                    "created_at": project_data["created_at"],
                    "updated_at": project_data["updated_at"],
                    "last_accessed": project_data.get("last_accessed", project_data["updated_at"])
                }
                break

        self._save_index(index)

    def update_custom_prompt(self, project_id: str, custom_prompt: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Update the project's custom system prompt.

        Args:
            project_id: The project UUID
            custom_prompt: The custom prompt string, or None to reset to default

        Returns:
            Updated project settings or None if project not found

        Educational Note: Custom prompts allow users to customize how the AI
        behaves for specific projects. Setting to None reverts to the default prompt.
        """
        project_data = self.get_project(project_id)
        if not project_data:
            return None

        # Ensure settings dict exists
        if "settings" not in project_data:
            project_data["settings"] = {
                "ai_model": "claude-sonnet-4-5",
                "auto_save": True,
                "custom_prompt": None
            }

        # Update the custom prompt (None means use default)
        project_data["settings"]["custom_prompt"] = custom_prompt
        project_data["updated_at"] = datetime.now().isoformat()

        # Save updated project
        self._save_project_data(project_id, project_data)

        print(f"Updated custom prompt for project: {project_id}")

        return project_data["settings"]

    def get_project_settings(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the project's settings.

        Args:
            project_id: The project UUID

        Returns:
            Project settings or None if project not found
        """
        project_data = self.get_project(project_id)
        if not project_data:
            return None

        # Return settings with defaults for any missing fields
        default_settings = {
            "ai_model": "claude-sonnet-4-5",
            "auto_save": True,
            "custom_prompt": None
        }

        settings = project_data.get("settings", {})
        # Merge with defaults
        return {**default_settings, **settings}


# Singleton instance
project_service = ProjectService()
