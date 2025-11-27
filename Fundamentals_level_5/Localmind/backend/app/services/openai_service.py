"""
Embeddings Service - Create embeddings using OpenAI API.

Educational Note: Embeddings convert text into dense vectors that capture
semantic meaning. Similar texts have similar vectors (close in vector space).

OpenAI Embedding Models:
- text-embedding-3-small: 1536 dimensions, cheaper, good for most use cases
- text-embedding-3-large: 3072 dimensions, more accurate, more expensive
- text-embedding-ada-002: Legacy model, 1536 dimensions

We use text-embedding-3-small as the default for cost-effectiveness.
"""
import os
from typing import List, Optional
from openai import OpenAI
from app.utils.text_utils import clean_text_for_embedding


class OpenAIService:
    """
    Service for creating text embeddings using OpenAI API.

    Educational Note: This service:
    1. Manages the OpenAI client connection
    2. Handles single and batch embedding creation
    3. Uses lazy initialization to avoid errors at import time
    """

    # Default model - good balance of quality and cost
    DEFAULT_MODEL = "text-embedding-3-small"
    # Dimensions for text-embedding-3-small
    EMBEDDING_DIMENSIONS = 1536

    def __init__(self):
        """Initialize the embeddings service."""
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """
        Get or create the OpenAI client.

        Educational Note: Lazy initialization ensures we don't fail
        at import time if the API key isn't set yet.

        Raises:
            ValueError: If OPENAI_API_KEY is not set
        """
        if self._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def create_embedding(
        self,
        text: str,
        model: str = DEFAULT_MODEL
    ) -> List[float]:
        """
        Create embedding for a single text string.

        Educational Note: For single texts, this is straightforward.
        The API returns a vector of floats representing the semantic
        meaning of the text. Text is cleaned before embedding to
        remove excessive whitespace.

        Args:
            text: Text to embed (will be cleaned automatically)
            model: OpenAI embedding model to use

        Returns:
            List of floats (the embedding vector)

        Raises:
            ValueError: If text is empty or API key not set
            OpenAI API errors if the request fails
        """
        # Clean text before embedding
        clean_text = clean_text_for_embedding(text)

        if not clean_text:
            raise ValueError("Cannot create embedding for empty text")

        client = self._get_client()

        response = client.embeddings.create(
            model=model,
            input=clean_text
        )

        return response.data[0].embedding

    def create_embeddings_batch(
        self,
        texts: List[str],
        model: str = DEFAULT_MODEL
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts in a single API call.

        Educational Note: Batch processing is more efficient than
        individual calls because:
        - Reduces API overhead
        - Lower latency overall
        - Often cheaper per token

        OpenAI supports up to 2048 texts per batch request.
        All texts are cleaned before embedding.

        Args:
            texts: List of texts to embed (will be cleaned automatically)
            model: OpenAI embedding model to use

        Returns:
            List of embedding vectors (same order as input texts)

        Raises:
            ValueError: If texts list is empty or API key not set
        """
        if not texts:
            return []

        # Clean texts and filter out empty ones, tracking indices
        cleaned_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            clean_text = clean_text_for_embedding(text)
            if clean_text:
                cleaned_texts.append(clean_text)
                valid_indices.append(i)

        if not cleaned_texts:
            raise ValueError("All texts are empty after cleaning")

        client = self._get_client()

        # Create embeddings in batch
        response = client.embeddings.create(
            model=model,
            input=cleaned_texts
        )

        # Extract embeddings in order
        embeddings_map = {item.index: item.embedding for item in response.data}
        valid_embeddings = [embeddings_map[i] for i in range(len(cleaned_texts))]

        # Reconstruct full list with None for empty texts
        result = [None] * len(texts)
        for orig_idx, embedding in zip(valid_indices, valid_embeddings):
            result[orig_idx] = embedding

        # Replace None with zero vectors for empty texts
        for i, emb in enumerate(result):
            if emb is None:
                result[i] = [0.0] * self.EMBEDDING_DIMENSIONS

        return result

    def get_embedding_dimensions(self, model: str = DEFAULT_MODEL) -> int:
        """
        Get the number of dimensions for a given model.

        Educational Note: Different models produce different dimension
        vectors. This is important for Pinecone index configuration.

        Args:
            model: The embedding model name

        Returns:
            Number of dimensions in the embedding vector
        """
        dimensions_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions_map.get(model, 1536)


# Singleton instance for easy import
openai_service = OpenAIService()
