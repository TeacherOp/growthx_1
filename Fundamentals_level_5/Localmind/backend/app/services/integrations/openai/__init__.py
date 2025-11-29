"""
OpenAI Integration - OpenAI API wrapper for embeddings.

Educational Note: This module provides embedding creation using OpenAI's
text-embedding-3-small model. Used by the RAG pipeline for semantic search.
"""
from app.services.integrations.openai.openai_service import openai_service

__all__ = ["openai_service"]
