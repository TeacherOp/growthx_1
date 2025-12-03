"""
Source processing control endpoints - cancel and retry.

Educational Note: Source processing is a background operation that can:
- Take a long time (large PDFs, research sources)
- Fail due to API errors
- Need to be interrupted by user

Cancellation Pattern:
- Processing runs in ThreadPoolExecutor
- We use a "cooperative cancellation" pattern
- task_service tracks cancellation flags per source
- Processors check is_target_cancelled() periodically
- On cancel: cleanup processed files, keep raw file

Retry Pattern:
- Raw file is preserved on failure/cancel
- User can retry without re-uploading
- Processing restarts from the raw file
- Previous processed data is cleaned up first

Why Keep Raw Files?
- Upload might have been slow (large file)
- Error might be transient (API rate limit)
- User might want to try again later
- Raw file = single source of truth

Processing Status Flow:
    uploaded -> processing -> embedding -> ready
        |           |
        v           v
      error  <----error
        |
        v
      (retry) -> processing -> ...

Routes:
- POST /projects/<id>/sources/<id>/cancel - Stop processing
- POST /projects/<id>/sources/<id>/retry  - Restart processing
"""
from flask import jsonify, current_app
from app.api.sources import sources_bp
from app.services.source_services import SourceService

# Initialize service
source_service = SourceService()


@sources_bp.route('/projects/<project_id>/sources/<source_id>/cancel', methods=['POST'])
def cancel_source_processing(project_id: str, source_id: str):
    """
    Cancel processing for a source.

    Educational Note: Cancellation is "cooperative" - we set a flag and
    processors check it periodically. This allows for clean shutdown:
    - Current API call completes (can't interrupt HTTP)
    - Partial results are discarded
    - Raw file is preserved for retry

    What gets cleaned up:
    - Processed text file
    - Chunk files
    - Embeddings in Pinecone (if any were created)

    What's preserved:
    - Raw uploaded file
    - Source entry in index (status -> "uploaded")

    Can only cancel sources that are currently processing.

    Returns:
        { "success": true, "message": "Processing cancelled" }

    Errors:
        - 400 if source not found or not in processing state
    """
    try:
        cancelled = source_service.cancel_processing(project_id, source_id)

        if not cancelled:
            return jsonify({
                'success': False,
                'error': 'Cannot cancel - source not found or not processing'
            }), 400

        return jsonify({
            'success': True,
            'message': 'Processing cancelled'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error cancelling source processing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sources_bp.route('/projects/<project_id>/sources/<source_id>/retry', methods=['POST'])
def retry_source_processing(project_id: str, source_id: str):
    """
    Retry processing for a failed or cancelled source.

    Educational Note: Retry restarts the entire processing pipeline:
    1. Verify source is in retryable state (uploaded, error)
    2. Clean up any partial processed data
    3. Trigger fresh processing from raw file
    4. Status changes to "processing"

    This is why we preserve raw files - enables retry without re-upload.

    Retryable states:
    - "uploaded": Never processed or was cancelled
    - "error": Processing failed previously

    Non-retryable states:
    - "processing": Already in progress
    - "embedding": Almost done, let it finish
    - "ready": Already complete (delete and re-upload to reprocess)

    Returns:
        { "success": true, "message": "Processing restarted" }

    Errors:
        - 400 if source not in retryable state
    """
    try:
        result = source_service.retry_processing(project_id, source_id)

        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Retry failed')
            }), 400

        return jsonify({
            'success': True,
            'message': result.get('message', 'Processing restarted')
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error retrying source processing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
