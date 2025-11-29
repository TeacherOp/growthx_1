"""
Source Processing - Processing orchestration for different file types.

Educational Note: This folder contains the processing service and individual
processors for each file type. Each processor handles content extraction,
embedding generation, and summary creation for its file type.

Processing Flow:
1. Source uploaded -> status: "uploaded"
2. Processing starts -> status: "processing"
3. If embeddings needed -> status: "embedding"
4. Complete -> status: "ready" | "error"

Files:
- source_processing_service.py: Orchestrator that dispatches to the right processor
- pdf_processor.py: PDF extraction via Claude vision
- text_processor.py: Text file splitting into pages
- docx_processor.py: DOCX extraction via python-docx
- image_processor.py: Image analysis via Claude vision
- pptx_processor.py: PPTX slide analysis via Claude vision
- audio_processor.py: Audio transcription via ElevenLabs
- link_processor.py: URL content extraction via web agent
- youtube_processor.py: YouTube transcript extraction
"""
from app.services.source_services.source_processing.source_processing_service import source_processing_service

__all__ = ["source_processing_service"]
