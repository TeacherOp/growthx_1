"""
Pinecone Service - Vector database operations for semantic search.

Educational Note: Pinecone is a managed vector database that enables:
- Storing high-dimensional vectors (embeddings)
- Fast similarity search using cosine/dot product metrics
- Metadata filtering for hybrid search

Our application uses:
- Index: "growthxlearn" (created automatically on API key validation)
- Dimensions: 1536 (OpenAI text-embedding-3-small)
- Metric: cosine similarity
- Namespace: project_id (isolate vectors by project)
"""
import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone


class PineconeService:
    """
    Service for Pinecone vector database operations.

    Educational Note: This service handles:
    - Upserting vectors (insert/update)
    - Semantic search (query by vector)
    - Deleting vectors (by ID or filter)
    - Namespace management (one namespace per project)
    """

    # Index configuration (must match validation_service.py)
    INDEX_NAME = "growthxlearn"

    def __init__(self):
        """Initialize the Pinecone service."""
        self._client: Optional[Pinecone] = None
        self._index = None

    def _get_client(self) -> Pinecone:
        """
        Get or create the Pinecone client.

        Educational Note: Lazy initialization ensures we don't fail
        at import time if the API key isn't set yet.

        Raises:
            ValueError: If PINECONE_API_KEY is not set
        """
        if self._client is None:
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                raise ValueError("PINECONE_API_KEY not found in environment")
            self._client = Pinecone(api_key=api_key)
        return self._client

    def _get_index(self):
        """
        Get the Pinecone index.

        Educational Note: The index must exist before we can use it.
        It's created automatically when the user validates their API key
        in AppSettings (via validation_service.validate_pinecone_key).

        Raises:
            ValueError: If the index doesn't exist
        """
        if self._index is None:
            client = self._get_client()

            if not client.has_index(self.INDEX_NAME):
                raise ValueError(
                    f"Pinecone index '{self.INDEX_NAME}' not found. "
                    "Please validate your Pinecone API key in App Settings first."
                )

            self._index = client.Index(self.INDEX_NAME)

        return self._index

    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str
    ) -> Dict[str, Any]:
        """
        Upsert vectors into Pinecone.

        Educational Note: Upsert = insert + update. If a vector ID exists,
        it's updated. If not, it's inserted. This makes it safe to call
        multiple times with the same data.

        Args:
            vectors: List of vector dicts with format:
                {
                    "id": "unique_id",
                    "values": [0.1, 0.2, ...],
                    "metadata": {"text": "...", "page": 1, ...}
                }
            namespace: Project ID to isolate vectors

        Returns:
            Dict with upsert stats: {"upserted_count": N}
        """
        if not vectors:
            return {"upserted_count": 0}

        index = self._get_index()

        # Upsert in batches of 100 (Pinecone recommendation)
        batch_size = 100
        total_upserted = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            response = index.upsert(vectors=batch, namespace=namespace)
            total_upserted += response.upserted_count

        return {"upserted_count": total_upserted}

    def search(
        self,
        query_vector: List[float],
        namespace: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using a query vector.

        Educational Note: This is the core of RAG retrieval:
        1. User query is converted to embedding (done elsewhere)
        2. Query vector is compared to all vectors in namespace
        3. Most similar vectors (by cosine similarity) are returned
        4. Metadata (including original text) is retrieved

        Args:
            query_vector: The embedding of the search query
            namespace: Project ID to search within
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"source_id": "abc"})
            include_metadata: Whether to return metadata with results

        Returns:
            List of search results with format:
            [
                {
                    "id": "chunk_id",
                    "score": 0.95,  # Similarity score
                    "metadata": {"text": "...", "page": 1, ...}
                },
                ...
            ]
        """
        index = self._get_index()

        response = index.query(
            vector=query_vector,
            namespace=namespace,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )

        # Convert to simple dict format
        results = []
        for match in response.matches:
            result = {
                "id": match.id,
                "score": match.score,
            }
            if include_metadata and match.metadata:
                result["metadata"] = dict(match.metadata)
            results.append(result)

        return results

    def delete_by_source(
        self,
        source_id: str,
        namespace: str
    ) -> Dict[str, Any]:
        """
        Delete all vectors for a specific source.

        Educational Note: When a user deletes a source document,
        we need to remove all its chunks from the vector database.
        We use metadata filtering to find and delete by source_id.

        Args:
            source_id: The source document ID
            namespace: Project ID (namespace)

        Returns:
            Dict with deletion info
        """
        index = self._get_index()

        # Delete by metadata filter
        index.delete(
            namespace=namespace,
            filter={"source_id": {"$eq": source_id}}
        )

        return {"deleted": True, "source_id": source_id}

    def delete_by_ids(
        self,
        ids: List[str],
        namespace: str
    ) -> Dict[str, Any]:
        """
        Delete specific vectors by their IDs.

        Args:
            ids: List of vector IDs to delete
            namespace: Project ID (namespace)

        Returns:
            Dict with deletion info
        """
        if not ids:
            return {"deleted_count": 0}

        index = self._get_index()

        # Delete in batches of 1000 (Pinecone limit)
        batch_size = 1000
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            index.delete(ids=batch, namespace=namespace)

        return {"deleted_count": len(ids)}

    def delete_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Delete all vectors in a namespace (entire project).

        Educational Note: When a project is deleted, we delete
        the entire namespace to clean up all associated vectors.

        Args:
            namespace: Project ID to delete

        Returns:
            Dict with deletion info
        """
        index = self._get_index()

        index.delete(namespace=namespace, delete_all=True)

        return {"deleted": True, "namespace": namespace}

    def get_namespace_stats(self, namespace: str) -> Dict[str, Any]:
        """
        Get statistics for a namespace.

        Args:
            namespace: Project ID

        Returns:
            Dict with stats like vector count
        """
        index = self._get_index()

        stats = index.describe_index_stats()

        namespace_stats = stats.namespaces.get(namespace, {})

        return {
            "namespace": namespace,
            "vector_count": getattr(namespace_stats, 'vector_count', 0),
            "total_vector_count": stats.total_vector_count
        }

    def is_configured(self) -> bool:
        """
        Check if Pinecone is configured and ready to use.

        Returns:
            True if API key is set and index exists
        """
        try:
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                return False

            client = self._get_client()
            return client.has_index(self.INDEX_NAME)
        except Exception:
            return False


# Singleton instance for easy import
pinecone_service = PineconeService()
