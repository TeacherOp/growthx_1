"""
Flask Web Application for AI-Powered Presentation Builder

This is a simple Flask web application that demonstrates how to build
an AI agent system with a web interface. Students will learn:
- Flask basics (routes, templates, sessions)
- Server-Sent Events for streaming updates
- File uploads and handling
- AI agent orchestration
- Multi-agent architecture
"""

import os
import json
import uuid
import time
import queue
import threading
from flask import Flask, render_template, request, jsonify, send_file, session, Response, stream_with_context
from werkzeug.utils import secure_filename

# Import our configuration and agents
from config import Config, allowed_file
from agent.chat_agent import ChatAgent

# Initialize Flask app
app = Flask(__name__)

# Apply configuration
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = str(Config.UPLOAD_FOLDER)

# Store active chat sessions
# In production, use Redis or a database instead of in-memory storage
chat_sessions = {}


def get_or_create_session():
    """
    Get or create a chat session for the current user

    Returns:
        tuple: (session_id, chat_session_data)
    """
    # Get or create session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    # Create new chat session if doesn't exist
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            'chat': ChatAgent(api_key=Config.ANTHROPIC_API_KEY),
            'messages': [],
            'pptx_file': None,
            'session_start_time': time.time()
        }

    return session_id, chat_sessions[session_id]


@app.route('/')
def index():
    """Render the main page"""
    # Clear any existing session to start fresh
    session.clear()
    return render_template('index.html')


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    Handle chat messages with streaming progress updates using Server-Sent Events (SSE)

    This endpoint demonstrates how to stream real-time updates from an AI agent
    to the frontend, providing a better user experience during long operations.
    """
    try:
        # Get or create session
        session_id, chat_session = get_or_create_session()

        # Get user message from request
        message = request.form.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Handle file uploads (for brand images, logos, etc.)
        uploaded_files = []
        if 'files[]' in request.files:
            files = request.files.getlist('files[]')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create unique filename to avoid conflicts
                    unique_filename = f"{session_id}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    uploaded_files.append(filepath)

        # Determine if this is the first message
        is_first_message = len(chat_session['messages']) == 0

        # Store user message in session
        chat_session['messages'].append({
            'role': 'user',
            'content': message,
            'images': uploaded_files
        })

        # Create a queue for streaming progress events
        progress_queue = queue.Queue()

        def progress_callback(event_type, data):
            """Callback function to receive progress updates from agents"""
            progress_queue.put({'event': event_type, 'data': data})

        def generate():
            """
            Generator function for Server-Sent Events

            This function runs the chat in a background thread and streams
            progress updates to the client as they occur.
            """
            try:
                # Create new chat instance with progress callback
                chat_instance = ChatAgent(
                    api_key=Config.ANTHROPIC_API_KEY,
                    progress_callback=progress_callback
                )

                # Copy conversation history from session
                chat_instance.messages = chat_session['chat'].messages.copy()

                # Container to hold the response
                response_container = {'response': None, 'error': None}

                def run_chat():
                    """Run chat in background thread"""
                    try:
                        if is_first_message:
                            response = chat_instance.start_conversation(
                                message,
                                uploaded_files if uploaded_files else None
                            )
                        else:
                            response = chat_instance.send_message(
                                message,
                                uploaded_files if uploaded_files else None
                            )
                        response_container['response'] = response
                    except Exception as e:
                        response_container['error'] = str(e)
                    finally:
                        # Signal completion
                        progress_queue.put({'event': 'done', 'data': {}})

                # Start chat in background thread
                thread = threading.Thread(target=run_chat)
                thread.start()

                # Stream progress events to client
                while True:
                    try:
                        # Get event from queue (wait max 0.1 seconds)
                        event = progress_queue.get(timeout=0.1)

                        if event['event'] == 'done':
                            # Update session with latest chat state
                            chat_session['chat'] = chat_instance

                            if response_container['error']:
                                # Send error event
                                yield f"data: {json.dumps({'event': 'error', 'data': {'message': response_container['error']}})}\n\n"
                            else:
                                # Store AI response in session
                                chat_session['messages'].append({
                                    'role': 'assistant',
                                    'content': response_container['response']
                                })

                                # Check if a PPTX file was generated
                                pptx_file = None
                                session_start_time = chat_session.get('session_start_time', 0)

                                exports_dir = Config.EXPORTS_FOLDER
                                if exports_dir.exists():
                                    pptx_files = sorted(exports_dir.glob('*.pptx'), key=os.path.getmtime, reverse=True)
                                    for pptx_path in pptx_files:
                                        # Only consider files created after this session started
                                        if os.path.getmtime(pptx_path) > session_start_time:
                                            pptx_file = str(pptx_path)
                                            chat_session['pptx_file'] = pptx_file
                                            break

                                # Send completion event with response
                                yield f"data: {json.dumps({'event': 'complete', 'data': {'response': response_container['response'], 'has_pptx': pptx_file is not None, 'pptx_filename': os.path.basename(pptx_file) if pptx_file else None}})}\n\n"
                            break
                        else:
                            # Stream progress event to client
                            yield f"data: {json.dumps(event)}\n\n"

                    except queue.Empty:
                        # Send keepalive to prevent timeout
                        yield f": keepalive\n\n"

                        # Check if thread is done
                        if not thread.is_alive() and progress_queue.empty():
                            break

            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'event': 'error', 'data': {'message': str(e)}})}\n\n"

        # Return Server-Sent Events stream
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download')
def download():
    """
    Download the generated PPTX file

    This endpoint allows users to download the PowerPoint file
    that was generated during their session.
    """
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in chat_sessions:
            return jsonify({'error': 'No active session'}), 404

        chat_session = chat_sessions[session_id]
        pptx_file = chat_session.get('pptx_file')

        if not pptx_file or not os.path.exists(pptx_file):
            return jsonify({'error': 'No presentation file found'}), 404

        return send_file(
            pptx_file,
            as_attachment=True,
            download_name=os.path.basename(pptx_file)
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    """
    Reset the current session

    Clears the conversation history and allows the user to start over.
    """
    try:
        session_id = session.get('session_id')
        if session_id and session_id in chat_sessions:
            del chat_sessions[session_id]
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
    """
    Main entry point for the Flask application

    This function:
    1. Validates configuration
    2. Ensures required directories exist
    3. Starts the Flask development server
    """

    print("\n" + "="*60)
    print("AI-POWERED PRESENTATION BUILDER")
    print("="*60)

    # Validate configuration
    try:
        Config.validate()
        print("Configuration validated successfully")
    except ValueError as e:
        print(f"\nError: {e}")
        print("Please check your .env file at the project root")
        return

    # Ensure required directories exist
    Config.ensure_directories()
    print("Required directories created")

    # Print startup message
    print(f"\nStarting Flask server...")
    print(f"Open your browser and navigate to:")
    print(f"  http://localhost:{Config.PORT}")
    print("\n" + "="*60 + "\n")

    # Run the Flask app
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )


if __name__ == "__main__":
    main()
