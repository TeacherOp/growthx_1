"""
Alternative source upload endpoints - URL, text, and research.

Educational Note: Not all sources are file uploads. This module handles:

1. URL Sources:
   - Regular websites: Fetched via web agent with web_fetch tool
   - YouTube videos: Transcripts fetched via youtube-transcript-api
   - Stored as .link files containing JSON with URL and metadata

2. Text Sources:
   - Pasted text content
   - Stored as .txt files
   - Useful for quick notes, meeting transcripts, etc.

3. Research Sources:
   - AI-generated research on a topic
   - Uses web search to gather information
   - Long-running async operation

Why Different Source Types?
- Files: User has the content locally
- URLs: Content lives on the web
- Text: Quick paste without creating a file
- Research: AI generates content based on topic

Each type goes through the same processing pipeline after creation:
extract -> chunk -> embed -> ready for RAG

Routes:
- POST /projects/<id>/sources/url      - Add website/YouTube source
- POST /projects/<id>/sources/text     - Add pasted text source
- POST /projects/<id>/sources/research - Add AI research source
"""
from flask import jsonify, request, current_app
from app.api.sources import sources_bp
from app.services.source_services import SourceService

# Initialize service
source_service = SourceService()


@sources_bp.route('/projects/<project_id>/sources/url', methods=['POST'])
def add_url_source(project_id: str):
    """
    Add a URL source (website or YouTube link) to a project.

    Educational Note: URL sources demonstrate the web agent pattern:
    1. URL is stored as a .link file
    2. Web agent is triggered with web_fetch/web_search tools
    3. Agent extracts relevant content from the page
    4. Extracted text is processed like any other source

    For YouTube:
    - youtube-transcript-api fetches available transcripts
    - Falls back to auto-generated captions if no manual transcript
    - Much faster than web agent (no AI needed)

    Request Body:
        {
            "url": "https://example.com/article",  # required
            "name": "Article Title",                # optional
            "description": "About this article"    # optional
        }

    Returns:
        {
            "success": true,
            "source": { ... source object with status: "uploaded" ... },
            "message": "URL source added successfully"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        url = data.get('url')
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400

        source = source_service.add_url_source(
            project_id=project_id,
            url=url,
            name=data.get('name'),
            description=data.get('description', '')
        )

        return jsonify({
            'success': True,
            'source': source,
            'message': 'URL source added successfully'
        }), 201

    except ValueError as e:
        # Validation errors (invalid URL, etc.)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error adding URL source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sources_bp.route('/projects/<project_id>/sources/text', methods=['POST'])
def add_text_source(project_id: str):
    """
    Add a pasted text source to a project.

    Educational Note: Text sources are the simplest source type:
    1. Text is saved directly as a .txt file
    2. No extraction needed - text is already plain
    3. Goes straight to chunking and embedding

    Use cases:
    - Meeting notes pasted from another app
    - Code snippets
    - Email content
    - Quick notes

    Request Body:
        {
            "content": "The text content to store...",  # required
            "name": "Meeting Notes 2024-01-15",        # required
            "description": "Weekly team sync notes"    # optional
        }

    Returns:
        {
            "success": true,
            "source": { ... source object ... },
            "message": "Text source added successfully"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        content = data.get('content')
        name = data.get('name')

        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400

        if not name:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400

        source = source_service.add_text_source(
            project_id=project_id,
            content=content,
            name=name,
            description=data.get('description', '')
        )

        return jsonify({
            'success': True,
            'source': source,
            'message': 'Text source added successfully'
        }), 201

    except ValueError as e:
        # Validation errors (empty content, etc.)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error adding text source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sources_bp.route('/projects/<project_id>/sources/research', methods=['POST'])
def add_research_source(project_id: str):
    """
    Add a deep research source to a project.

    Educational Note: Research sources demonstrate autonomous AI agents:
    1. User provides topic and focus areas
    2. AI agent uses web_search to find relevant sources
    3. Agent synthesizes information into a research document
    4. Document is processed like any other text source

    This is a LONG-RUNNING operation:
    - Can take several minutes depending on topic complexity
    - Status updates: uploaded -> processing -> embedding -> ready
    - Frontend should poll for status updates

    Request Body:
        {
            "topic": "Quantum Computing Applications",    # required
            "description": "Focus on cryptography and...", # required (min 50 chars)
            "links": ["https://reference1.com", ...]      # optional seed URLs
        }

    Returns:
        {
            "success": true,
            "source": { ... source with status: "uploaded" ... },
            "message": "Research source created - processing will begin shortly"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        topic = data.get('topic')
        description = data.get('description')

        if not topic:
            return jsonify({
                'success': False,
                'error': 'Topic is required'
            }), 400

        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400

        source = source_service.add_research_source(
            project_id=project_id,
            topic=topic,
            description=description,
            links=data.get('links', [])
        )

        return jsonify({
            'success': True,
            'source': source,
            'message': 'Research source created - processing will begin shortly'
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error adding research source: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
