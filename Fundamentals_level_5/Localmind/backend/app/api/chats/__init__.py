"""
Chats API Blueprint.

Educational Note: This blueprint handles all chat CRUD operations.
Chats are containers for conversations - they hold messages but don't
process AI responses themselves (that's the messages blueprint's job).
"""
from flask import Blueprint

# Create blueprint with url_prefix for all chat routes
chats_bp = Blueprint('chats', __name__)

# Import routes to register them with the blueprint
from app.api.chats import routes  # noqa: F401
