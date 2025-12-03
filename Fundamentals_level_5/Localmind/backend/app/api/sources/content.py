"""
Content serving endpoints - citations and AI-generated images.

Educational Note: These endpoints serve content that appears in chat responses:

1. Citations:
   - Claude cites sources using [[cite:CHUNK_ID]] syntax
   - Frontend parses these and shows tooltips on hover
   - This endpoint fetches the actual chunk content

2. AI-Generated Images:
   - Some agents generate visualizations (e.g., CSV analyzer)
   - Images are referenced in chat as [[image:FILENAME]]
   - This endpoint serves the image files

Citation Flow:
1. User asks: "What did the report say about Q3?"
2. Claude searches sources, finds relevant chunks
3. Response includes: "Revenue increased 15% [[cite:abc123_page_5_chunk_2]]"
4. Frontend renders "15%" as a clickable/hoverable link
5. On hover, frontend calls GET /citations/abc123_page_5_chunk_2
6. Tooltip shows chunk content and source name

Chunk ID Format:
- Pattern: {source_id}_page_{page}_chunk_{n}
- Example: a1b2c3d4-e5f6_page_5_chunk_2
- source_id: UUID of the source
- page: Page number in original document
- chunk: Chunk index within that page

Image Flow:
1. CSV agent analyzes data, generates chart
2. Chart saved to ai_outputs/images/{source_id}_chart.png
3. Response includes: [[image:abc123_order_chart.png]]
4. Frontend renders as <img src="/api/v1/projects/{id}/ai-images/abc123_order_chart.png">
5. This endpoint serves the image file

Routes:
- GET /projects/<id>/citations/<chunk_id> - Get chunk content
- GET /projects/<id>/ai-images/<filename> - Serve AI image
"""
from flask import jsonify, current_app, send_file
from app.api.sources import sources_bp
from app.utils.citation_utils import get_chunk_content
from app.utils.path_utils import get_ai_images_dir


@sources_bp.route('/projects/<project_id>/citations/<chunk_id>', methods=['GET'])
def get_citation_content(project_id: str, chunk_id: str):
    """
    Get the content of a chunk for citation display.

    Educational Note: This enables grounded AI responses with verifiable citations.
    When Claude cites a chunk, users can hover to see:
    - The actual text Claude is referencing
    - Which source it came from
    - The page number in the original document

    This builds trust - users can verify the AI isn't hallucinating.

    Chunk ID Format:
        {source_id}_page_{page_number}_chunk_{chunk_index}
        Example: abc123-def456_page_5_chunk_2

    Returns:
        {
            "success": true,
            "chunk": {
                "content": "The actual text content...",
                "chunk_id": "abc123_page_5_chunk_2",
                "source_id": "abc123-def456",
                "source_name": "Q3 Financial Report.pdf",
                "page_number": 5,
                "chunk_index": 2
            }
        }

    Errors:
        - 404 if chunk not found (may have been deleted)
    """
    try:
        chunk_data = get_chunk_content(project_id, chunk_id)

        if not chunk_data:
            return jsonify({
                'success': False,
                'error': f'Chunk not found: {chunk_id}'
            }), 404

        return jsonify({
            'success': True,
            'chunk': {
                'content': chunk_data['content'],
                'chunk_id': chunk_data['chunk_id'],
                'source_id': chunk_data['source_id'],
                'source_name': chunk_data['source_name'],
                'page_number': chunk_data['page_number'],
                'chunk_index': chunk_data['chunk_index']
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting citation content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sources_bp.route('/projects/<project_id>/ai-images/<filename>', methods=['GET'])
def get_ai_image(project_id: str, filename: str):
    """
    Serve an AI-generated image from the ai_outputs/images folder.

    Educational Note: Some AI agents generate visual outputs:
    - CSV analyzer: Charts and graphs
    - Future: Diagrams, infographics, etc.

    Images are stored separately from sources because:
    - They're generated, not uploaded
    - They're tied to chat responses, not source processing
    - They don't need embedding (not searchable text)

    The [[image:FILENAME]] syntax in chat responses is parsed by
    frontend into proper <img> tags pointing to this endpoint.

    URL Parameters:
        project_id: The project UUID
        filename: Image filename (e.g., source123_order_status.png)

    Returns:
        Binary image data with appropriate Content-Type header

    Errors:
        - 404 if image not found
    """
    try:
        images_dir = get_ai_images_dir(project_id)
        image_path = images_dir / filename

        if not image_path.exists():
            return jsonify({
                'success': False,
                'error': f'Image not found: {filename}'
            }), 404

        # Determine MIME type based on extension
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml'
        }
        mime_type = mime_types.get(extension, 'image/png')

        return send_file(
            image_path,
            mimetype=mime_type
        )

    except Exception as e:
        current_app.logger.error(f"Error serving AI image: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
