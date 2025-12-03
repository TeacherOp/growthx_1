"""
AI Services - Simple AI-powered utility services.

Educational Note: This folder contains lightweight AI services that perform
single, focused tasks. These are NOT complex agents with tool loops - they
are simple request/response AI utilities.

Services:
- chat_naming_service: Generate concise chat titles (1-5 words)
- summary_service: Generate source document summaries (150-200 tokens)
- memory_service: AI-powered memory merging (max 150 tokens per memory)
- image_service: Extract content from images using Claude vision
- pdf_service: Extract text from PDFs using batched tool-based approach
- pptx_service: Extract content from PowerPoint presentations using Claude vision
- embedding_service: Orchestrates embedding pipeline (chunk, embed, upsert to Pinecone)

These services typically:
- Make a single API call per request (or batched calls for large documents)
- Use Haiku model for speed and cost efficiency
- Have simple input/output patterns
- Load prompts via prompt_loader.get_prompt_config()

Import Pattern:
Services are NOT imported at module level to avoid circular imports.
Import directly from the specific module:
    from app.services.ai_services.memory_service import memory_service
    from app.services.ai_services.image_service import image_service
"""

__all__ = [
    "chat_naming_service",
    "summary_service",
    "memory_service",
    "image_service",
    "pdf_service",
    "pptx_service",
    "embedding_service"
]
