"""
API Blueprint initialization.

Educational Note: Blueprints help organize Flask applications by
grouping related routes together. This makes the code more modular
and easier to maintain.
"""
from flask import Blueprint

# Create the main API blueprint
api_bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from app.api import projects  # noqa: F401

# Educational Note: The noqa comment tells flake8 to ignore the
# "imported but unused" warning. We import to register routes,
# not to use the module directly.