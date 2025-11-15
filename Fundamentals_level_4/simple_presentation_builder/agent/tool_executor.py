"""
Tool execution functions for PPT AI Agent
"""

import os
import json
from pathlib import Path


class PPTToolExecutor:
    """Executes tools for the PPT AI Agent"""

    def __init__(self, base_path="."):
        self.base_path = Path(base_path)

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result"""

        tool_map = {
            "create_folder": self.create_folder,
            "create_file": self.create_file,
            "read_file": self.read_file,
            "update_file": self.update_file,
            "list_files": self.list_files,
            "return_ppt_result": self.return_ppt_result
        }

        if tool_name not in tool_map:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            return tool_map[tool_name](tool_input)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def create_folder(self, tool_input: dict) -> str:
        """Create a new folder"""
        folder_path = self.base_path / tool_input["folder_path"]

        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created folder: {folder_path}"
        except Exception as e:
            return f"Error creating folder: {str(e)}"

    def create_file(self, tool_input: dict) -> str:
        """Create a new file with content"""
        file_path = self.base_path / tool_input["file_path"]
        content = tool_input["content"]

        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully created file: {file_path} ({len(content)} characters)"
        except Exception as e:
            return f"Error creating file: {str(e)}"

    def read_file(self, tool_input: dict) -> str:
        """Read contents of a file"""
        file_path = self.base_path / tool_input["file_path"]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return f"File contents of {file_path}:\n\n{content}"
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def update_file(self, tool_input: dict) -> str:
        """Update an existing file"""
        file_path = self.base_path / tool_input["file_path"]
        content = tool_input["content"]

        try:
            # Check if file exists
            if not file_path.exists():
                return f"Error: File does not exist: {file_path}. Use create_file instead."

            # Update the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully updated file: {file_path} ({len(content)} characters)"
        except Exception as e:
            return f"Error updating file: {str(e)}"

    def list_files(self, tool_input: dict) -> str:
        """
        List all files in a directory

        The directory path is relative to base_path (which is set to DATA_DIR).
        Default is 'slides' which will list files in input_output_data/slides/
        """
        directory = tool_input.get("directory", "slides")
        dir_path = self.base_path / directory

        try:
            if not dir_path.exists():
                return f"Directory does not exist: {dir_path}"

            files = []
            for item in sorted(dir_path.iterdir()):
                if item.is_file() and not item.name.startswith('.'):
                    files.append(str(item.relative_to(self.base_path)))

            if not files:
                return f"No files found in {directory}"

            return f"Files in {directory}:\n" + "\n".join(f"  - {f}" for f in files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def return_ppt_result(self, tool_input: dict) -> str:
        """Return the final PPT generation result"""
        success = tool_input["success"]
        message = tool_input["message"]
        slide_count = tool_input["slide_count"]
        slide_files = tool_input["slide_files"]

        # Convert relative slide paths to absolute paths
        full_slide_files = []
        for slide_file in slide_files:
            # If it's just 'slides/slide_1.html', convert to full path
            if slide_file.startswith('slides/'):
                # Remove 'slides/' prefix and add to DATA_DIR/slides
                slide_name = slide_file.replace('slides/', '')
                full_path = str(self.base_path / 'slides' / slide_name)
            else:
                # Already a relative path without 'slides/' prefix or different format
                full_path = str(self.base_path / slide_file) if not Path(slide_file).is_absolute() else slide_file
            full_slide_files.append(full_path)

        result = {
            "success": success,
            "message": message,
            "slide_count": slide_count,
            "slide_files": full_slide_files
        }

        # This is a special marker that the PPT Agent should stop
        return f"PPT_GENERATION_COMPLETE: {json.dumps(result)}"
