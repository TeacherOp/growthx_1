"""
Sources API Blueprint - Document and Media Management.

Educational Note: Sources are the foundation of RAG (Retrieval Augmented Generation).
They provide the context that makes AI responses grounded in your specific data.

Source Types Supported:
1. Files (routes.py):
   - PDF: Extracted via Claude Vision (batched pages)
   - DOCX: Extracted via python-docx
   - PPTX: Converted to PDF, then extracted like PDF
   - Images: Analyzed via Claude Vision
   - Audio: Transcribed via ElevenLabs Scribe
   - CSV: Analyzed by data agent

2. URLs (uploads.py):
   - Websites: Fetched via web agent with web_fetch tool
   - YouTube: Transcripts fetched via youtube-transcript-api

3. Text (uploads.py):
   - Pasted text: Saved directly as .txt file

4. Research (uploads.py):
   - AI-generated research on a topic using web search

Source Lifecycle:
1. uploaded: Raw file saved, waiting for processing
2. processing: Extraction/transcription in progress
3. embedding: Text chunked and sent to Pinecone
4. ready: Searchable in chat
5. error: Processing failed (can retry)

The Processing Pipeline:
1. Upload -> source_service.upload_source()
2. Extract text -> source_processing_service (by file type)
3. Chunk text -> chunking.py (~200 tokens per chunk)
4. Embed -> OpenAI text-embedding-3-small
5. Store -> Pinecone vector database

Why Chunking?
- LLMs have context limits
- Smaller chunks = more precise retrieval
- Each chunk can be cited independently
"""
from flask import Blueprint

# Create blueprint for source management
sources_bp = Blueprint('sources', __name__)

# Import routes to register them with the blueprint
from app.api.sources import routes  # noqa: F401
from app.api.sources import uploads  # noqa: F401
from app.api.sources import processing  # noqa: F401
from app.api.sources import content  # noqa: F401
