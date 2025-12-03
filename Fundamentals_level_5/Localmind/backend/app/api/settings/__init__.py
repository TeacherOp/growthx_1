"""
Settings API Blueprint - Application Configuration.

Educational Note: This blueprint manages application settings including:

1. API Keys (api_keys.py):
   - Store/retrieve API keys securely in .env file
   - Mask keys when sending to frontend (security)
   - Validate keys by making test API calls
   - Auto-configure related settings (e.g., Pinecone index)

2. Processing Settings (processing.py):
   - Anthropic tier configuration (rate limits)
   - Controls parallel processing (PDF extraction, etc.)

Security Considerations:
- API keys are stored in .env file (not in database)
- Keys are masked when returned to frontend (show only first/last chars)
- Validation happens server-side before keys are used
- .env changes trigger app reload to pick up new values

Key Management Flow:
1. User enters API key in Settings UI
2. Frontend calls validate endpoint to test key
3. If valid, frontend calls update endpoint to save
4. Backend saves to .env and reloads environment
5. New key is immediately available to all services

This pattern keeps sensitive credentials out of the frontend
while still allowing users to configure their own API keys.
"""
from flask import Blueprint

# Create blueprint for settings management
settings_bp = Blueprint('settings', __name__)

# Import routes to register them with the blueprint
from app.api.settings import api_keys  # noqa: F401
from app.api.settings import processing  # noqa: F401
