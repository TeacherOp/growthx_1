"""
Main entry point for LocalMind backend.

Educational Note: This file creates and runs the Flask application.
We keep it separate from the app factory to maintain clean separation
of concerns and make testing easier.
"""
import os
from dotenv import load_dotenv

from app import create_app, socketio

# Load environment variables from .env file
load_dotenv()

# Get configuration name from environment or use default
config_name = os.getenv('FLASK_ENV', 'development')

# Create the Flask application
app = create_app(config_name)


if __name__ == '__main__':
    """
    Run the Flask application.

    Educational Note: We use socketio.run instead of app.run when
    using Flask-SocketIO for WebSocket support (real-time features).
    """
    port = int(os.getenv('PORT', 5000))
    debug = config_name == 'development'

    print(f"""
    ╔════════════════════════════════════════╗
    ║       LocalMind Backend Server         ║
    ╠════════════════════════════════════════╣
    ║  Running on: http://localhost:{port}     ║
    ║  Environment: {config_name:<24} ║
    ║  Debug Mode: {str(debug):<26} ║
    ╚════════════════════════════════════════╝

    Press CTRL+C to stop the server
    """)

    # Run with SocketIO for WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',  # Allow connections from any IP
        port=port,
        debug=debug,
        use_reloader=debug  # Auto-reload on code changes in debug mode
    )