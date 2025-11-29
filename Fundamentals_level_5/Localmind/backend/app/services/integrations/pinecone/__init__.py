"""
Pinecone Integration - Vector database for semantic search.

Educational Note: Pinecone stores document embeddings and enables
fast similarity search. Used by the RAG pipeline for retrieval.
"""
from app.services.integrations.pinecone.pinecone_service import pinecone_service

__all__ = ["pinecone_service"]
