# AI-Powered Presentation Builder

A Flask web application that uses AI agents to generate PowerPoint presentations from natural language descriptions. This project demonstrates multi-agent architecture, Flask web development, and real-time streaming with Server-Sent Events.

## What You'll Learn

- **Flask Web Development**: Building a web app with routes, templates, and sessions
- **Multi-Agent Architecture**: Orchestrating multiple AI agents (Chat Agent + Presentation Agent)
- **Server-Sent Events (SSE)**: Streaming real-time updates to the frontend
- **File Handling**: Uploading images and generating downloadable files
- **AI Tool Use**: Using Claude's tool-calling capabilities
- **Configuration Management**: Centralized config with environment variables

## Architecture Overview

```
User <-> Flask App <-> Chat Agent <-> Presentation Agent
                           |
                           +-> Web Search Tool
                           +-> Generate PPT Tool
```

### Components

1. **Flask App** (`app.py`): Web server handling HTTP requests and SSE streaming
2. **Chat Agent** (`agent/chat_agent.py`): Orchestrates conversation and gathers requirements
3. **Presentation Agent** (`agent/presentation_agent.py`): Generates HTML slides and converts to PPTX
4. **Configuration** (`config.py`): Centralized environment and path management
5. **Tools** (`agent/tools.py`): Tool definitions for AI agents
6. **Utilities**: Screenshot capture and PowerPoint export functionality

## How to Run

### Prerequisites

1. Activate the virtual environment from the project root:
```bash
# From the project root (Learnai/)
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

2. Ensure your `.env` file at the project root has:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### Start the Application

```bash
# Navigate to this directory
cd Fundamentals_level_4/simple_presentation_builder

# Run the Flask app
python3 app.py
```

The application will start on `http://localhost:5000`

## How It Works

### 1. User Interaction Flow

1. User opens the web interface
2. User describes their presentation needs (can include images for branding)
3. Chat Agent asks clarifying questions to gather:
   - Presentation topic and purpose
   - Content details and structure
   - Brand colors, logos, guidelines
   - Specific data or metrics
4. Once enough information is gathered, Chat Agent calls Presentation Agent
5. Presentation Agent generates HTML slides
6. Slides are converted to PowerPoint (.pptx) format
7. User can download the final presentation

### 2. Agent Communication

**Chat Agent** (`chat_agent.py`):
- Maintains conversation with user
- Has access to tools: `web_search`, `generate_ppt`
- Gathers requirements through multi-turn conversation
- Calls Presentation Agent when ready

**Presentation Agent** (`presentation_agent.py`):
- Receives structured data from Chat Agent
- Uses file creation tools to generate HTML slides
- Captures screenshots of each slide
- Exports to PowerPoint format
- Returns results to Chat Agent

### 3. Server-Sent Events (SSE)

The `/api/chat/stream` endpoint demonstrates streaming:

```python
# Client connects to SSE endpoint
# Server streams events as they occur:
{
  "event": "agent_started",
  "data": {"message": "Starting presentation generation..."}
}
{
  "event": "iteration",
  "data": {"iteration": 1}
}
{
  "event": "complete",
  "data": {"response": "...", "has_pptx": true}
}
```

This provides real-time feedback during long-running operations.

## File Structure

```
simple_presentation_builder/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── README.md                   # This file
├── agent/
│   ├── __init__.py
│   ├── chat_agent.py          # Main orchestration agent
│   ├── presentation_agent.py  # Slide generation agent
│   ├── tools.py               # Tool definitions
│   └── tool_executor.py       # Tool execution logic
├── utils/
│   ├── export.py              # PPTX export functionality
│   └── screenshot.py          # HTML screenshot capture
├── templates/
│   ├── base.html              # Base template (reusable layout)
│   └── index.html             # Chat interface (extends base)
├── static/                     # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css          # Custom styles and animations
│   └── js/
│       └── main.js            # Client-side JavaScript
└── input_output_data/          # All data files organized here
    ├── uploads/                # User-uploaded images
    ├── slides/                 # Generated HTML slides
    ├── screenshots/            # Slide screenshots for PPTX
    └── exports/                # Final PPTX files
```

## Key Concepts

### Session Management

The app uses Flask sessions to maintain state across requests:
- Each user gets a unique `session_id`
- Session stores conversation history and generated files
- Sessions are stored in-memory (use Redis in production)

### Progress Callbacks

Agents emit progress events via callbacks:
```python
def progress_callback(event_type, data):
    progress_queue.put({'event': event_type, 'data': data})
```

These events are streamed to the client via SSE.

### Configuration Pattern

All configuration is centralized in `config.py`:
- Environment variables loaded once
- Paths defined relative to project structure
- Validation ensures required settings are present

## Extending the Application

### Adding New Features

1. **New Tools**: Add to `agent/tools.py` and implement in `tool_executor.py`
2. **New Routes**: Add Flask routes in `app.py`
3. **Configuration**: Add new settings to `config.py`

### Example: Adding a New Tool

```python
# In tools.py
NEW_TOOL = {
    "name": "my_tool",
    "description": "What this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        }
    }
}

# In tool_executor.py
def execute_my_tool(self, params):
    # Tool implementation
    return result
```

## Troubleshooting

### API Key Not Found
- Ensure `.env` is in the project root (Learnai/)
- Check the key is correctly named `ANTHROPIC_API_KEY`
- Restart the Flask app after modifying `.env`

### Import Errors
- Make sure you're in the correct directory
- Virtual environment must be activated
- Run from `simple_presentation_builder/` directory

### Port Already in Use
- Change port in `.env`: `FLASK_PORT=5001`
- Or stop the process using port 5000

## Learning Path

1. **Start with `config.py`**: Understand how configuration works
2. **Read `app.py`**: See Flask route handling and SSE streaming
3. **Study `chat_agent.py`**: Learn the conversation loop and tool use
4. **Explore `presentation_agent.py`**: See the agentic loop in action
5. **Review `tools.py`**: Understand tool definitions
6. **Experiment**: Modify prompts, add features, customize output

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Server-Sent Events Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [Claude Messages API](https://docs.anthropic.com/claude/reference/messages-api)

## Notes

- This is a teaching example - production apps would need error handling, rate limiting, and proper session storage
- The agentic loop pattern shown here can be adapted to many different use cases
- SSE streaming provides a great user experience for long-running AI operations
