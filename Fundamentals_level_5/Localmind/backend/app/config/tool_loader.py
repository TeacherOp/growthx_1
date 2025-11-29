"""
Tool Loader - Loads tool definitions from JSON files.

Educational Note: This module provides a centralized way to load tool definitions
stored in JSON files. By storing tools in separate files:
- Tools can be versioned and edited independently
- Different extraction tasks can use different tool sets
- Tool definitions are easy to test and validate

Usage:
    from app.config import tool_loader

    # Load a specific tool by name
    tool = tool_loader.load_tool("pdf_tools", "pdf_extraction")

    # Load all tools from a category
    tools = tool_loader.load_tools_from_category("pdf_tools")
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ToolLoader:
    """
    Loader class for tool definitions from JSON files.

    Educational Note: Tool definitions follow the Claude API tool schema:
    - name: Unique identifier for the tool
    - description: Explains when/how to use the tool (important for Claude!)
    - input_schema: JSON Schema defining the parameters

    Tools are organized in subdirectories by category:
    - tools/pdf_tools/ - Tools for PDF processing
    - tools/search_tools/ - Tools for search functionality (future)
    - etc.
    """

    def __init__(self):
        """Initialize the tool loader with the tools directory path."""
        # Tools are stored in app/services/tools/
        self.tools_dir = Path(__file__).parent.parent / "services" / "tools"

    def load_tool(self, category: str, tool_name: str) -> Dict[str, Any]:
        """
        Load a single tool definition from a JSON file.

        Educational Note: Each tool is stored in its own JSON file
        with the schema Claude expects for tool definitions.

        Args:
            category: Tool category (subdirectory name, e.g., "pdf_tools")
            tool_name: Name of the tool file (without .json extension)

        Returns:
            Tool definition dict ready for Claude API

        Raises:
            FileNotFoundError: If tool file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        tool_path = self.tools_dir / category / f"{tool_name}.json"

        if not tool_path.exists():
            raise FileNotFoundError(
                f"Tool definition not found: {tool_path}\n"
                f"Available categories: {list(self.tools_dir.iterdir())}"
            )

        with open(tool_path, "r") as f:
            tool_def = json.load(f)

        # Validate required fields
        self._validate_tool_definition(tool_def, str(tool_path))

        return tool_def

    def load_tools_from_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Load all tool definitions from a category directory.

        Educational Note: Useful when an agent needs multiple tools
        from the same category (e.g., all PDF processing tools).

        Args:
            category: Tool category (subdirectory name)

        Returns:
            List of tool definition dicts

        Raises:
            FileNotFoundError: If category directory doesn't exist
        """
        category_dir = self.tools_dir / category

        if not category_dir.exists():
            raise FileNotFoundError(
                f"Tool category not found: {category_dir}\n"
                f"Available categories: {[d.name for d in self.tools_dir.iterdir() if d.is_dir()]}"
            )

        tools = []
        for tool_file in category_dir.glob("*.json"):
            with open(tool_file, "r") as f:
                tool_def = json.load(f)
            self._validate_tool_definition(tool_def, str(tool_file))
            tools.append(tool_def)

        return tools

    def _validate_tool_definition(self, tool_def: Dict[str, Any], source: str) -> None:
        """
        Validate that a tool definition has required fields.

        Educational Note: Claude requires specific fields for tools:
        - name: Identifier Claude uses to call the tool
        - description: Helps Claude understand when to use it
        - input_schema: Defines expected parameters

        Args:
            tool_def: Tool definition dict to validate
            source: Source file path for error messages

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["name", "description", "input_schema"]
        missing = [f for f in required_fields if f not in tool_def]

        if missing:
            raise ValueError(
                f"Tool definition at {source} missing required fields: {missing}\n"
                f"Tool definitions must have: name, description, input_schema"
            )

        # Validate input_schema has type: object
        schema = tool_def.get("input_schema", {})
        if schema.get("type") != "object":
            raise ValueError(
                f"Tool {tool_def.get('name')} has invalid input_schema: "
                f"type must be 'object', got '{schema.get('type')}'"
            )

    def get_available_categories(self) -> List[str]:
        """
        Get list of available tool categories.

        Returns:
            List of category names (subdirectory names)
        """
        if not self.tools_dir.exists():
            return []
        return [d.name for d in self.tools_dir.iterdir() if d.is_dir()]

    def get_available_tools(self, category: str) -> List[str]:
        """
        Get list of available tools in a category.

        Args:
            category: Tool category (subdirectory name)

        Returns:
            List of tool names (without .json extension)
        """
        category_dir = self.tools_dir / category

        if not category_dir.exists():
            return []

        return [f.stem for f in category_dir.glob("*.json")]

    def load_tools_for_agent(
        self,
        category: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load all tools from a category, separated by type.

        Educational Note: Agent tools can be of different types:
        - server_tools: Claude handles execution (web_search, web_fetch)
        - client_tools: We execute them (tavily_search, custom tools)
        - termination_tools: Signal agent completion (return_search_result)

        Server tools use a special format with "type" field.
        Client tools use standard format with "input_schema".

        Args:
            category: Tool category (subdirectory name, e.g., "web_agent")

        Returns:
            Dict with 'server_tools', 'client_tools', and 'beta_headers'
        """
        category_dir = self.tools_dir / category

        if not category_dir.exists():
            raise FileNotFoundError(
                f"Tool category not found: {category_dir}\n"
                f"Available categories: {[d.name for d in self.tools_dir.iterdir() if d.is_dir()]}"
            )

        server_tools = []
        client_tools = []
        beta_headers = []

        for tool_file in category_dir.glob("*.json"):
            with open(tool_file, "r") as f:
                tool_def = json.load(f)

            tool_type = tool_def.get("_type", "client_tool")

            if tool_type == "server_tool":
                # Server tools use special format for Claude API
                server_tool = {
                    "type": tool_def["type"],
                    "name": tool_def["name"],
                }
                if "max_uses" in tool_def:
                    server_tool["max_uses"] = tool_def["max_uses"]

                server_tools.append(server_tool)

                # Collect beta headers
                if "_beta_header" in tool_def:
                    beta_headers.append(tool_def["_beta_header"])

            else:
                # Client tools (including termination) use standard format
                self._validate_tool_definition(tool_def, str(tool_file))
                client_tool = {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "input_schema": tool_def["input_schema"],
                }
                client_tools.append(client_tool)

        return {
            "server_tools": server_tools,
            "client_tools": client_tools,
            "beta_headers": beta_headers
        }


# Singleton instance for easy import
tool_loader = ToolLoader()
