"""
Prompts API Blueprint.

Educational Note: System prompts are the instructions that shape how Claude
responds in conversations. This blueprint manages:

1. Project Prompts:
   - Each project can have a custom system prompt
   - If no custom prompt, falls back to default
   - Stored in project.json as 'custom_prompt' field

2. Default Prompt:
   - Global fallback stored in data/prompts/default_prompt.json
   - Used when projects don't have custom prompts

Why System Prompts Matter:
- They set Claude's persona and behavior
- They define what tools are available and how to use them
- They provide context about the user's sources
- They're the foundation of prompt engineering
"""
from flask import Blueprint

# Create blueprint for prompt management
prompts_bp = Blueprint('prompts', __name__)

# Import routes to register them with the blueprint
from app.api.prompts import routes  # noqa: F401
