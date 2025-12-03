"""
Projects API Blueprint.

Educational Note: Projects are the top-level organizational unit in NoobBook.
Each project contains:
- Sources (documents, images, audio, URLs)
- Chats (conversations with the AI)
- Memory (project-specific context)
- Cost tracking (API usage per project)

This blueprint demonstrates RESTful API design:
- GET    /projects           - List all (collection)
- POST   /projects           - Create new (collection)
- GET    /projects/<id>      - Get one (resource)
- PUT    /projects/<id>      - Update (resource)
- DELETE /projects/<id>      - Delete (resource)
- POST   /projects/<id>/open - Action endpoint (mark as opened)

Plus analytics endpoints:
- GET /projects/<id>/costs   - API cost breakdown
- GET /projects/<id>/memory  - User + project memory
"""
from flask import Blueprint

# Create blueprint for project operations
projects_bp = Blueprint('projects', __name__)

# Import routes to register them with the blueprint
from app.api.projects import routes  # noqa: F401
from app.api.projects import costs  # noqa: F401
from app.api.projects import memory  # noqa: F401
