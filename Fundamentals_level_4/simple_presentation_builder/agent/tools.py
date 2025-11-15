"""
Tool definitions for Main AI Chat and PPT AI Agent
"""

# ===== MAIN AI CHAT TOOLS =====

# Web Search - Server-side tool (Anthropic provides this)
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 10
}

# Generate PPT - Custom client-side tool
GENERATE_PPT_TOOL = {
    "name": "generate_ppt",
    "description": """
    This tool calls an AI agent that will generate a complete presentation as a series of html slides and files.
    Use this tool ONLY when you have collected ALL required information from the user:
    - Topic of the presentation
    - Description and purpose
    - Detailed content outline or key points
    - Brand colors
    - Logo details
    - Brand guidelines
    - Additional data or statistics

    Please ensure that you are passing as much relevant and detailed information you can to the AI agent to create the best possible presentation.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "ppt_topic": {
                "type": "string",
                "description": "The main topic/title of the presentation (e.g., 'Q4 Product Roadmap 2025')"
            },
            "ppt_description": {
                "type": "string",
                "description": "A detailed description of what the presentation is about and its purpose"
            },
            "ppt_details": {
                "type": "string",
                "description": "Detailed content outline, key points to cover, data to include, and overall structure"
            },
            "ppt_data": {
                "type": "string",
                "description": "Any specific data, statistics, or numbers to include. Any logo asset file links which can be passed to the ppt agent to use can also be passed here."
            },
            "brand_logo_details": {
                "type": "string",
                "description": "Details about the brand logo - file path, URL, or description"
            },
            "brand_guideline_details": {
                "type": "string",
                "description": "Brand guidelines including tone, voice, style preferences, font types anything relevant, if needed use the web search tool to get the required information, before passing"
            },
            "brand_color_details": {
                "type": "string",
                "description": "Brand colors in hex format (e.g., 'primary: #1E40AF, secondary: #F59E0B')"
            }
        },
        "required": ["ppt_topic", "ppt_description", "ppt_details", "ppt_data", "brand_logo_details", "brand_guideline_details", "brand_color_details"]
    }
}


# ===== PPT AI AGENT TOOLS =====

CREATE_FOLDER_TOOL = {
    "name": "create_folder",
    "description": """Create a new folder in the slides directory.
    Use this to organize slide files or assets.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "folder_path": {
                "type": "string",
                "description": "Path of the folder to create (relative to data directory, e.g., 'slides/assets')"
            }
        },
        "required": ["folder_path"]
    }
}

CREATE_FILE_TOOL = {
    "name": "create_file",
    "description": """Create a new HTML slide file with complete, valid HTML content or a css file with complete valid css content, for css always use tailwind css import from cdn in html files when needed, except the custom base css.

    The content parameter should contain the COMPLETE HTML file, not just a snippet.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path where the file should be created (relative to data directory, e.g., 'slides/slide_1.html')"
            },
            "content": {
                "type": "string",
                "description": "Complete HTML file content including DOCTYPE, head, and body, cdn imports of tailwind css, google fonts, icon packs etc when needed, or complete valid css content for css files"
            }
        },
        "required": ["file_path", "content"]
    }
}

READ_FILE_TOOL = {
    "name": "read_file",
    "description": """Read the contents of an existing file.
    Use this to review previously created slides or configuration files.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path of the file to read"
            }
        },
        "required": ["file_path"]
    }
}

UPDATE_FILE_TOOL = {
    "name": "update_file",
    "description": """Update an existing HTML slide file with corrected or modified content.
    The content parameter should be the COMPLETE updated HTML file.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path of the file to update"
            },
            "content": {
                "type": "string",
                "description": "Complete updated HTML file content"
            }
        },
        "required": ["file_path", "content"]
    }
}

LIST_FILES_TOOL = {
    "name": "list_files",
    "description": """List all files in a directory.
    Use this to see what slides have been created.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory to list files from (default: 'slides')"
            }
        },
        "required": []
    }
}

RETURN_PPT_RESULT_TOOL = {
    "name": "return_ppt_result",
    "description": """Return the final result of the PPT generation process.
    Use this ONLY when all slides have been created and you're ready to finish.

    This tool marks the completion of the PPT generation process.
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "Whether the PPT generation was successful"
            },
            "message": {
                "type": "string",
                "description": "Summary message about the generated presentation"
            },
            "slide_count": {
                "type": "integer",
                "description": "Number of slides created"
            },
            "slide_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of slide file paths created"
            }
        },
        "required": ["success", "message", "slide_count", "slide_files"]
    }
}


# Collect all tools for easy access
MAIN_CHAT_TOOLS = [
    WEB_SEARCH_TOOL,
    GENERATE_PPT_TOOL
]

PPT_AGENT_TOOLS = [
    CREATE_FOLDER_TOOL,
    CREATE_FILE_TOOL,
    READ_FILE_TOOL,
    UPDATE_FILE_TOOL,
    LIST_FILES_TOOL,
    RETURN_PPT_RESULT_TOOL
]
